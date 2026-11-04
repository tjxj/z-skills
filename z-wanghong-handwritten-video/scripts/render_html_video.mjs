#!/usr/bin/env node
import {
  accessSync,
  constants,
  mkdirSync,
  readdirSync,
  statSync,
  writeFileSync,
} from 'node:fs';
import {homedir} from 'node:os';
import {basename, dirname, join, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {once} from 'node:events';
import {spawn, spawnSync} from 'node:child_process';
import puppeteer from 'puppeteer-core';

const DEMO_FONT_FAMILY = 'HanziPen SC';
const DEMO_FONT_POSTSCRIPT = 'HanziPenSC-W3';
const DEMO_FONT_ALIAS = 'Wanghong Preview Hand';

const usage = () => {
  console.error(
    'usage: render_html_video.mjs <deck.html> <output.mp4> ' +
      '[--seconds-per-slide 4] [--max-slides N] [--fps 30] ' +
      '[--chrome PATH] [--font-file PATH]',
  );
};

const positiveNumber = (raw, label) => {
  const value = Number(raw);
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(`${label} 必须是正数`);
  }
  return value;
};

const parseArgs = (argv) => {
  if (argv.length < 2) {
    usage();
    process.exit(2);
  }
  const options = {
    html: resolve(argv[0]),
    output: resolve(argv[1]),
    secondsPerSlide: 4,
    maxSlides: Number.POSITIVE_INFINITY,
    fps: 30,
    chrome: null,
    fontFile: null,
  };
  for (let index = 2; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!value) throw new Error(`${flag} 缺少参数`);
    if (flag === '--seconds-per-slide') {
      options.secondsPerSlide = positiveNumber(value, flag);
    } else if (flag === '--max-slides') {
      options.maxSlides = Math.floor(positiveNumber(value, flag));
    } else if (flag === '--fps') {
      options.fps = Math.floor(positiveNumber(value, flag));
    } else if (flag === '--chrome') {
      options.chrome = resolve(value);
    } else if (flag === '--font-file') {
      options.fontFile = resolve(value);
    } else {
      throw new Error(`未知参数: ${flag}`);
    }
    index += 1;
  }
  if (options.fps !== 30) {
    throw new Error('当前交付规格固定为 30fps');
  }
  return options;
};

const isExecutable = (path) => {
  try {
    accessSync(path, constants.X_OK);
    return true;
  } catch {
    return false;
  }
};

const commandPath = (command) => {
  const probe = spawnSync('which', [command], {encoding: 'utf8'});
  return probe.status === 0 ? probe.stdout.trim() : null;
};

const findChrome = (explicitPath) => {
  const candidates = [
    explicitPath,
    process.env.CHROME_PATH,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    commandPath('google-chrome'),
    commandPath('google-chrome-stable'),
    commandPath('chromium'),
    commandPath('chromium-browser'),
  ].filter(Boolean);
  const match = candidates.find(isExecutable);
  if (!match) {
    throw new Error('找不到 Google Chrome 或 Chromium；可用 --chrome 指定路径');
  }
  return match;
};

const findAssetFont = () => {
  // macOS 按需下载的字体位于 com_apple_MobileAsset_Font<N>，N 随系统版本变化
  const assetsRoot = '/System/Library/AssetsV2';
  let roots = [];
  try {
    roots = readdirSync(assetsRoot, {withFileTypes: true})
      .filter((entry) => entry.isDirectory() && entry.name.startsWith('com_apple_MobileAsset_Font'))
      .map((entry) => join(assetsRoot, entry.name))
      .sort()
      .reverse();
  } catch {
    return null;
  }
  for (const assetRoot of roots) {
    let entries = [];
    try {
      entries = readdirSync(assetRoot, {withFileTypes: true});
    } catch {
      continue;
    }
    for (const entry of entries) {
      if (!entry.isDirectory() || !entry.name.endsWith('.asset')) continue;
      for (const filename of ['Hanzipen.ttc', 'HanziPen.ttc']) {
        const candidate = join(assetRoot, entry.name, 'AssetData', filename);
        try {
          if (statSync(candidate).isFile()) return candidate;
        } catch {
          // Continue looking through downloaded macOS font assets.
        }
      }
    }
  }
  return null;
};

const findDemoFont = (explicitPath) => {
  const candidates = [
    explicitPath,
    process.env.WANGHONG_FONT_PATH,
    join(homedir(), 'Library', 'Fonts', 'Hanzipen.ttc'),
    join(homedir(), 'Library', 'Fonts', 'HanziPen.ttc'),
    '/Library/Fonts/Hanzipen.ttc',
    '/Library/Fonts/HanziPen.ttc',
    '/System/Library/Fonts/Supplemental/Hanzipen.ttc',
    '/System/Library/Fonts/Supplemental/HanziPen.ttc',
    findAssetFont(),
  ].filter(Boolean);
  for (const candidate of candidates) {
    try {
      if (statSync(candidate).isFile()) return candidate;
    } catch {
      // Try the next known location.
    }
  }
  throw new Error(
    '找不到预览封面使用的字体文件；请在 macOS 字体册下载“翩翩体-简”，' +
      '或用 --font-file 传入 Hanzipen.ttc',
  );
};

const ensureCommand = (command) => {
  const probe = spawnSync(command, ['-version'], {stdio: 'ignore'});
  if (probe.status !== 0) throw new Error(`缺少命令: ${command}`);
};

const waitForProcess = async (child, label) => {
  const [code, signal] = await once(child, 'close');
  if (code !== 0) {
    throw new Error(`${label} 失败，退出码 ${code ?? signal}`);
  }
};

const loadDemoFont = async (page, fontPath) => {
  const fontUrl = pathToFileURL(fontPath).href;
  await page.evaluate(
    async ({alias, family, fontUrl: source}) => {
      const face = new FontFace(alias, `url("${source}")`, {
        style: 'normal',
        weight: '100 900',
      });
      const loaded = await face.load();
      document.fonts.add(loaded);

      const style = document.createElement('style');
      style.id = 'wanghong-demo-font-lock';
      style.textContent = `
        :root {
          --hand: "${alias}";
          --hand-font: "${alias}";
          --ann-font: "${alias}";
          --font-sans: "${alias}";
          --font-display: "${alias}";
          --font-mono: "${alias}";
          --font-serif: "${alias}";
        }
        html, body, .deck, .deck *, .deck svg text {
          font-family: "${alias}" !important;
        }
      `;
      document.head.appendChild(style);
      await document.fonts.ready;
      if (!document.fonts.check(`32px "${alias}"`, '王虹学术手写')) {
        throw new Error(`字体文件加载失败: ${family}`);
      }
    },
    {alias: DEMO_FONT_ALIAS, family: DEMO_FONT_FAMILY, fontUrl},
  );
};

const verifyDemoFont = async (page) => {
  const client = await page.createCDPSession();
  try {
    await client.send('DOM.enable');
    await client.send('CSS.enable');
    const documentNode = await client.send('DOM.getDocument', {depth: -1});
    const selectors = [
      '.deck > .slide .hand-title, .deck > .slide .slide-title, .deck > .slide h1, .deck > .slide h2',
      '.deck > .slide .cover-meta div, .deck > .slide p, .deck > .slide li',
    ];
    let checked = 0;
    for (const selector of selectors) {
      const {nodeId} = await client.send('DOM.querySelector', {
        nodeId: documentNode.root.nodeId,
        selector,
      });
      if (!nodeId) continue;
      const {fonts} = await client.send('CSS.getPlatformFontsForNode', {nodeId});
      const renderedFonts = fonts.filter((font) => font.glyphCount > 0);
      if (renderedFonts.length === 0) continue;
      checked += 1;
      const matches = renderedFonts.every(
        (font) => font.isCustomFont && font.postScriptName === DEMO_FONT_POSTSCRIPT,
      );
      if (!matches) {
        throw new Error('图片示例字体校验失败：页面文字未命中指定字体文件');
      }
    }
    if (checked === 0) {
      throw new Error('图片示例字体校验失败：未找到可验证的页面文字');
    }
    console.log(`font verified: ${DEMO_FONT_POSTSCRIPT}`);
  } finally {
    await client.detach();
  }
};

const setMotionFrame = async (page, slideIndex, localTime, duration) => {
  await page.evaluate(
    ({slideIndex: current, localTime: time, duration: sceneDuration}) => {
      const clamp = (value) => Math.max(0, Math.min(1, value));
      const smooth = (value) => {
        const x = clamp(value);
        return x * x * (3 - 2 * x);
      };
      const slides = Array.from(document.querySelectorAll('.deck > .slide'));
      const active = slides[current];
      if (!active) throw new Error(`找不到第 ${current + 1} 页`);

      slides.forEach((slide, index) => {
        const selected = index === current;
        slide.classList.toggle('is-active', selected);
        slide.classList.toggle('is-prev', index < current);
        slide.classList.toggle('motion-active', selected);
        slide.style.opacity = selected ? `${smooth(time / 0.22)}` : '0';
        slide.style.pointerEvents = 'none';
        slide.style.transform = 'none';
        if (!selected) {
          Array.from(slide.children).forEach((element) => {
            if (!(element instanceof HTMLElement || element instanceof SVGElement)) return;
            element.style.opacity = '';
            element.style.translate = '';
            element.style.clipPath = '';
          });
        }
      });

      const groups = Array.from(active.children).filter(
        (element) =>
          element instanceof HTMLElement &&
          !element.matches('.notes, aside.notes, .speaker-notes'),
      );
      groups.forEach((element, index) => {
        const start = index === 0 ? 0.04 : 0.34 + (index - 1) * 0.24;
        const progress = smooth((time - start) / 0.62);
        element.style.opacity = `${progress}`;
        element.style.translate = `0 ${Math.round(22 * (1 - progress))}px`;
        element.style.clipPath =
          index === 0 ? `inset(0 ${(1 - progress) * 100}% 0 0)` : '';
      });

      const titleLines = active.querySelectorAll('.title-line');
      titleLines.forEach((line) => {
        if (!(line instanceof HTMLElement || line instanceof SVGElement)) return;
        const progress = smooth((time - 0.28) / 0.55);
        line.style.transformOrigin = 'left center';
        line.style.scale = `${progress} 1`;
        line.style.opacity = `${progress}`;
      });

      const markers = active.querySelectorAll(
        '.marker, .marker-yellow, .marker-green, .marker-coral, .mark-yellow, .mark-green, .mark-coral, .hl, .hl-yellow, .hl-green, .hl-coral, .takeaway',
      );
      markers.forEach((marker, index) => {
        if (!(marker instanceof HTMLElement || marker instanceof SVGElement)) return;
        const progress = smooth((time - 0.9 - index * 0.08) / 0.42);
        marker.style.clipPath = `inset(0 ${(1 - progress) * 100}% 0 0)`;
      });

      const paths = active.querySelectorAll(
        'svg path, svg line, svg polyline, svg rect, svg circle, .scribble',
      );
      paths.forEach((shape, index) => {
        if (!(shape instanceof SVGGeometryElement)) return;
        const progress = smooth((time - 0.72 - index * 0.018) / 1.2);
        let length = Number(shape.getAttribute('data-motion-length'));
        if (!Number.isFinite(length) || length <= 0) {
          try {
            length = shape.getTotalLength();
          } catch {
            length = 0;
          }
          shape.setAttribute('data-motion-length', `${length}`);
        }
        if (length > 0 && getComputedStyle(shape).fill === 'none') {
          shape.style.strokeDasharray = `${length}`;
          shape.style.strokeDashoffset = `${length * (1 - progress)}`;
        } else {
          shape.style.opacity = `${progress}`;
        }
      });

      let wipe = document.getElementById('wanghong-motion-wipe');
      if (!wipe) {
        wipe = document.createElement('div');
        wipe.id = 'wanghong-motion-wipe';
        document.body.appendChild(wipe);
      }
      const wipeProgress = smooth((time - (sceneDuration - 0.34)) / 0.32);
      wipe.style.transform = `scaleX(${wipeProgress}) skewX(-2deg)`;
    },
    {slideIndex, localTime, duration},
  );
};

const render = async (options) => {
  ensureCommand('ffmpeg');
  ensureCommand('ffprobe');
  const chrome = findChrome(options.chrome);
  const fontPath = findDemoFont(options.fontFile);
  mkdirSync(dirname(options.output), {recursive: true});
  const coverPath = resolve(dirname(options.output), 'cover.png');

  const browser = await puppeteer.launch({
    executablePath: chrome,
    headless: true,
    defaultViewport: {width: 1920, height: 1080, deviceScaleFactor: 1},
    args: [
      '--allow-file-access-from-files',
      '--disable-gpu',
      '--hide-scrollbars',
      '--no-sandbox',
      '--window-size=1920,1080',
    ],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({width: 1920, height: 1080, deviceScaleFactor: 1});
    // ?export：z-wanghong-handwritten-ppt 运行时隐藏控制条、直接显示整页
    await page.goto(`${pathToFileURL(options.html).href}?export#/1`, {
      waitUntil: 'networkidle0',
      timeout: 60_000,
    });
    await page.waitForFunction(
      () => !document.getElementById('wh-runtime') || document.documentElement.dataset.whReady === '1',
      {timeout: 30_000},
    );
    await loadDemoFont(page, fontPath);
    await page.addStyleTag({
      content: `
        html, body, .deck { width: 1920px !important; height: 1080px !important; overflow: hidden !important; }
        * { transition: none !important; animation-play-state: paused !important; }
        [class*="anim-"], .anim-stagger-list > * { animation: none !important; opacity: 1 !important; filter: none !important; }
        .notes, aside.notes, .speaker-notes, .notes-overlay, .overview, .progress-bar { display: none !important; }
        #wanghong-motion-wipe {
          position: fixed; inset: 0; z-index: 999999; pointer-events: none;
          background: var(--paper, #f7f5ed); transform-origin: right center;
          transform: scaleX(0); opacity: .985;
        }
      `,
    });
    await verifyDemoFont(page);
    console.log(`font source: ${basename(fontPath)}`);

    const detectedSlides = await page.evaluate(
      () => document.querySelectorAll('.deck > .slide').length,
    );
    if (detectedSlides < 1) throw new Error('HTML 中没有 .slide 页面');
    const slideCount = Math.min(detectedSlides, options.maxSlides);
    const framesPerSlide = Math.round(options.secondsPerSlide * options.fps);
    const totalFrames = framesPerSlide * slideCount;

    const ffmpegArgs = [
      '-y',
      '-v',
      'error',
      '-f',
      'image2pipe',
      '-framerate',
      `${options.fps}`,
      '-vcodec',
      'png',
      '-i',
      '-',
      '-an',
      '-c:v',
      'libx264',
      '-preset',
      'medium',
      '-crf',
      '18',
      '-pix_fmt',
      'yuv420p',
      '-s',
      '1920x1080',
      '-colorspace',
      'bt709',
      '-color_primaries',
      'bt709',
      '-color_trc',
      'bt709',
      '-movflags',
      '+faststart',
      options.output,
    ];
    const encoder = spawn('ffmpeg', ffmpegArgs, {
      stdio: ['pipe', 'inherit', 'inherit'],
    });
    const encoderDone = waitForProcess(encoder, 'ffmpeg 编码');
    let coverWritten = false;

    for (let slideIndex = 0; slideIndex < slideCount; slideIndex += 1) {
      for (let localFrame = 0; localFrame < framesPerSlide; localFrame += 1) {
        const localTime = localFrame / options.fps;
        await setMotionFrame(
          page,
          slideIndex,
          localTime,
          options.secondsPerSlide,
        );
        const buffer = await page.screenshot({
          type: 'png',
          clip: {x: 0, y: 0, width: 1920, height: 1080},
        });
        if (!coverWritten && slideIndex === 0 && localTime >= 2.4) {
          writeFileSync(coverPath, buffer);
          coverWritten = true;
        }
        if (!encoder.stdin.write(buffer)) await once(encoder.stdin, 'drain');

        const rendered = slideIndex * framesPerSlide + localFrame + 1;
        if (rendered === 1 || rendered % 30 === 0 || rendered === totalFrames) {
          console.log(`rendered ${rendered}/${totalFrames}`);
        }
      }
    }
    encoder.stdin.end();
    await encoderDone;
    if (!coverWritten) {
      await setMotionFrame(page, 0, options.secondsPerSlide * 0.65, options.secondsPerSlide);
      const cover = await page.screenshot({
        type: 'png',
        clip: {x: 0, y: 0, width: 1920, height: 1080},
      });
      writeFileSync(coverPath, cover);
    }
    console.log(`done: ${options.output}`);
    console.log(`cover: ${coverPath}`);
    console.log(`source slides: ${slideCount}/${detectedSlides}`);
  } finally {
    await browser.close();
  }
};

try {
  await render(parseArgs(process.argv.slice(2)));
} catch (error) {
  console.error(`error: ${error instanceof Error ? error.message : error}`);
  process.exit(1);
}
