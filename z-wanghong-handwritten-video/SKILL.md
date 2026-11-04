---
name: z-wanghong-handwritten-video
description: 将 z-wanghong-handwritten-ppt 生成的王虹学术手写 HTML 直接制作成 16:9 动画 MP4，字形锁定为原 PPT Skill 预览封面的手写字，完整保留字号、颜色、留白、图表和标注，输出零音频流。用户提到动画版王虹PPT、王虹手写动画、Notability手写视频、手写PPT转MP4、学术手写动画、纯画面手写视频、把王虹手写 HTML 做成视频或要求手写风 MP4 时必须使用。
---

# 王虹学术手写 HTML 动画视频

直接渲染原 HTML DOM，在原页面元素上增加帧驱动的写入、分步出现、荧光揭示、SVG 路径绘制和纸张转场。文字节点和排版仍由原 HTML 提供，渲染器在截图前加载原 PPT Skill 预览封面使用的同一字体文件，并校验 Chrome 实际命中的字形。不重新排版文字。

## 硬性边界

- 输入必须是 `z-wanghong-handwritten-ppt` 生成并通过检查的 HTML。
- 所有文字固定使用原 PPT Skill `assets/preview-cover.png` 里的字形，不使用候选字体。
- 渲染器必须读取指定字体文件，并通过 Chrome 的实际字体记录验证标题和正文；校验失败立即停止。
- 字号、字重、颜色、布局、图表和标注由原 HTML 决定。
- 输出固定为 1920×1080、30fps、H.264、`yuv420p`。
- 成片恰好一条视频流、零条音频流；不添加旁白、音乐、音效或静音占位音轨。
- 同时输出 MP4 和同目录下的 `cover.png`。

## 工作流程

### 1. 先得到原版手写 HTML

用户提供文章、讲稿或技术主题时，先严格使用同仓库的 `z-wanghong-handwritten-ppt` 生成 HTML。不要在本 Skill 内重新设计页面。

用户已经提供该 Skill 的 HTML 时，直接进入检查。保留 HTML 所在目录和相对资源路径，避免复制单个文件造成 CSS、图片或脚本丢失。

### 2. 用原 Skill 检查 HTML

```bash
python3 ../z-wanghong-handwritten-ppt/scripts/check_deck.py \
  "/absolute/path/to/deck/index.html"
```

检查失败时先修复原 HTML。输入应是 `build.py` 生成的 `index.html`（样式、运行时、字体、图片均已内嵌）；只有源稿 `slides.html` 时先运行 `python3 ../z-wanghong-handwritten-ppt/scripts/build.py slides.html`，在 macOS 上保持默认的翩翩体构建。

### 3. 安装一次渲染依赖

在本 Skill 目录运行：

```bash
npm install
```

渲染器使用本机 Google Chrome 或 Chromium 打开原 HTML。macOS 上先在字体册下载预览封面所用的“翩翩体-简”。渲染器会检查系统字体目录；字体文件在其他位置时，使用 `--font-file "/absolute/path/to/Hanzipen.ttc"`。可通过 `--chrome "/absolute/path/to/chrome"` 指定浏览器。

### 4. 渲染无声 MP4

```bash
scripts/render_html_video.sh \
  "/absolute/path/to/deck/index.html" \
  "/absolute/path/to/output/wanghong-handwritten-video.mp4" \
  --seconds-per-slide 4 \
  --font-file "/absolute/path/to/Hanzipen.ttc"
```

快速样片可以限制页数：

```bash
scripts/render_html_video.sh \
  "/absolute/path/to/deck/index.html" \
  "/absolute/path/to/output/preview.mp4" \
  --seconds-per-slide 4 \
  --max-slides 6
```

渲染器按以下顺序处理每页：

1. 原标题与标题线写入；
2. 原页面的顶层内容组依次出现；
3. 原荧光标记横向揭示；
4. 原 SVG 线条按路径绘制；
5. 结尾使用暖白纸张转场。

这些动作只修改透明度、位移、裁切和 SVG 描边进度。原 DOM 内容与计算后的排版保持原样，字形锁定为预览封面的指定字体。

### 5. 验收

包装脚本会自动检查编码、分辨率、帧率、像素格式、视频流和音频流，并执行完整解码测试。仍需人工查看：

- `cover.png` 与原 PPT Skill 的 `assets/preview-cover.png` 是否使用相同字形；
- 每页开始、内容完全显示、转场前各一帧；
- 标题、图表、标注、脚注有无遮挡或裁切；
- 结论是否至少完整停留 0.8 秒；
- MP4 是否没有可见或隐藏的音频流。

需要逐帧核对时，使用原 PPT Skill 的 `scripts/render.py index.html --slides N` 先导出同一页静态 PNG，再与 MP4 对应完成帧对照。字形或排版出现差异时停止交付，检查指定字体文件、原 CSS 和 HTML 路径。

## 动效纪律

- 一页只推进一个问题，动作服务于阅读顺序。
- 页面主体保持稳定，避免镜头缩放、卡片弹跳、粒子和发布会式炫技。
- 原 HTML 已有 CSS 动画时，渲染器把它们固定到最终视觉状态，再用统一帧进度控制进入顺序。
- 不改写原 HTML 的文字和事实，不添加页面外的新结论。

## 随附资源

- `scripts/render_html_video.mjs`：直接驱动原 HTML DOM 并逐帧编码。
- `scripts/render_html_video.sh`：原 Skill 检查、渲染和媒体验收入口。
- `references/motion-injection.md`：DOM 选择与动效规则。
- `examples/handwritten-html-motion-demo/`：由原 HTML 直接生成的无声样片。
- `tests/test_renderer_contract.py`：防止重新排版与音频回归。
