#!/usr/bin/env node
/*
 * 把 cards.html 里的每个 .card 渲染成 1080×1440 PNG，并做版面检查。
 *
 *   node render.cjs <cards.html> [--out 输出目录] [--scale 1] [--sheet 总览图.jpg]
 *
 * 输出：xhs-01-<data-name>.png。检查不过时退出码为 1。
 * 依赖：playwright（优先用系统 Chrome，没有则用 Playwright 自带 Chromium）。
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { pathToFileURL } = require('url');

const W = 1080;
const H = 1440;

function args(argv) {
  const o = { out: null, scale: 1, sheet: null, file: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--out') o.out = argv[++i];
    else if (a === '--scale') o.scale = Number(argv[++i]);
    else if (a === '--sheet') o.sheet = argv[++i];
    else if (!o.file) o.file = a;
  }
  return o;
}

function loadPlaywright() {
  const tries = ['playwright', 'playwright-core'];
  for (const name of tries) {
    try { return require(name); } catch (e) { /* 继续找 */ }
    try { return require(require.resolve(name, { paths: [process.cwd()] })); } catch (e) { /* 继续找 */ }
  }
  console.error('找不到 playwright。在当前目录执行：npm i playwright');
  process.exit(2);
}

function findSerif() {
  const home = os.homedir();
  const list = [
    process.env.XHS_SERIF_FONT,
    path.join(home, 'Library/Fonts/SourceHanSerifSC-VF.ttf'),
    '/Library/Fonts/SourceHanSerifSC-VF.ttf',
    path.join(home, '.fonts/SourceHanSerifSC-VF.ttf'),
    path.join(home, '.local/share/fonts/SourceHanSerifSC-VF.ttf'),
    '/usr/share/fonts/SourceHanSerifSC-VF.ttf',
  ].filter(Boolean);
  return list.find((p) => fs.existsSync(p)) || null;
}

async function launch(chromium) {
  try {
    return await chromium.launch({ channel: 'chrome' });
  } catch (e) {
    return chromium.launch();
  }
}

/* 在页面里运行：找出越界文字。带 data-bleed 的装饰元素不查。 */
function inspectCard(card) {
  const box = card.getBoundingClientRect();
  const bad = [];
  const walker = document.createTreeWalker(card, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    const text = node.textContent.trim();
    if (!text || node.parentElement.closest('[data-bleed],svg,style,script')) continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    for (const r of range.getClientRects()) {
      if (r.width === 0) continue;
      if (r.left < box.left + 12 || r.right > box.right - 12 || r.top < box.top + 12 || r.bottom > box.bottom - 12) {
        bad.push(text.slice(0, 18));
        break;
      }
    }
  }
  return {
    w: Math.round(box.width),
    h: Math.round(box.height),
    name: card.dataset.name || '',
    bad: [...new Set(bad)],
  };
}

async function main() {
  const o = args(process.argv.slice(2));
  if (!o.file) {
    console.error('用法：node render.cjs <cards.html> [--out 目录] [--scale 1] [--sheet 总览图.jpg]');
    process.exit(2);
  }
  const html = path.resolve(o.file);
  const outDir = path.resolve(o.out || path.join(path.dirname(html), 'output'));
  fs.mkdirSync(outDir, { recursive: true });

  const { chromium } = loadPlaywright();
  const browser = await launch(chromium);
  const context = await browser.newContext({
    viewport: { width: 1240, height: 1600 },
    deviceScaleFactor: o.scale,
  });
  const serif = findSerif();
  if (serif) {
    await context.addInitScript((url) => {
      const face = new FontFace('SHSerif', `url("${url}")`, { weight: '250 900' });
      document.fonts.add(face);
      window.__serifReady = face.load().catch(() => null);
    }, pathToFileURL(serif).href);
  } else {
    console.warn('提示：没找到 SourceHanSerifSC-VF.ttf，用系统衬线字体回退，可设 XHS_SERIF_FONT 指定路径。');
  }

  const page = await context.newPage();
  let failed = 0;
  page.on('pageerror', (e) => { console.error('页面错误：', e.message); failed++; });
  await page.goto(pathToFileURL(html).href);
  await page.waitForLoadState('networkidle');
  await page.evaluate(async () => {
    await (window.__serifReady || Promise.resolve());
    await document.fonts.ready;
    await Promise.all([...document.images].map((i) => (i.decode ? i.decode().catch(() => null) : null)));
    await new Promise((r) => setTimeout(r, 200));
  });

  const cards = await page.$$('.card');
  if (!cards.length) { console.error('没有找到 .card'); process.exit(1); }
  const files = [];
  for (let i = 0; i < cards.length; i++) {
    const info = await cards[i].evaluate(inspectCard);
    const n = String(i + 1).padStart(2, '0');
    const file = path.join(outDir, `xhs-${n}${info.name ? '-' + info.name : ''}.png`);
    await cards[i].screenshot({ path: file });
    files.push(file);
    const sized = info.w === W && info.h === H;
    if (!sized) failed++;
    if (info.bad.length) failed++;
    console.log(`${n} ${path.basename(file)} ${info.w}×${info.h}${sized ? '' : ' 尺寸不对'}${info.bad.length ? ' 越界：' + info.bad.join(' / ') : ''}`);
  }

  if (o.sheet) {
    const cols = Math.min(files.length, 4);
    const tile = 360;
    const rows = Math.ceil(files.length / cols);
    const sheet = await context.newPage();
    await sheet.setViewportSize({ width: cols * (tile + 12) + 12, height: rows * (tile * 4 / 3 + 12) + 12 });
    const imgs = files.map((f) => `<img src="${pathToFileURL(f).href}" style="width:${tile}px;height:${tile * 4 / 3}px;display:block">`).join('');
    const tmp = path.join(outDir, '.sheet.html');
    fs.writeFileSync(tmp, `<body style="margin:0;background:#2b2b2b;padding:12px;display:grid;grid-template-columns:repeat(${cols},${tile}px);gap:12px">${imgs}</body>`);
    await sheet.goto(pathToFileURL(tmp).href);
    await sheet.waitForLoadState('networkidle');
    await sheet.screenshot({ path: path.resolve(o.sheet), type: 'jpeg', quality: 82 });
    fs.unlinkSync(tmp);
  }

  await browser.close();
  console.log(failed ? `检查未通过：${failed} 项` : `通过：${files.length} 张，全部 ${W}×${H}`);
  process.exit(failed ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(1); });
