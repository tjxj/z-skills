# z-skills

`z-skills` 是一组可复用的本地 Agent Skills，用来把常见工作流沉淀成稳定能力：网页素材采集、视频下载、视频学习网页、全景音频生成、文档解析、邮件读取、表格处理、Markdown 转 Word/PDF、诗词与技术文章成书、互动科普网页、证据型资料问答、docx 模板格式刷、手写幻灯片、手写 HTML 动画，以及文章四格漫画配图

这些 Skill 面向中文创作、知识管理和自动化任务，可按需安装到支持 Agent Skills 的环境中。当前共 **19 个 Skill**，具体能力、依赖与执行流程以各目录的 `SKILL.md` 为准。

[快速安装](#快速安装) · [Skills 一览](#skills-一览) · [诗词与技术文章成书](#诗词与技术文章成书) · [使用建议](#使用建议)

## 快速安装

### 通过 npx skills 按需安装

需要 Node.js / npm。以通用证据问答和全景音频为例：

```bash
npx skills add tjxj/z-skills --skill z-grounded-source-qa
npx skills add tjxj/z-skills --skill z-qwen-audio-studio
```

按安装器提示选择目标 Agent。目录名与 Skill 的 `name` 不一定相同，例如 `z-poetry-book` 的 Skill 名为 `poetry-book`，其专用安装方式见下文。

### 克隆后手动安装

```bash
git clone https://github.com/tjxj/z-skills.git
cd z-skills

# 示例目标目录；请替换为你的 Agent 实际读取的 skills 目录
mkdir -p "/path/to/your/.agent/skills"

# 安装一个 Skill，保留整个目录及其资源
cp -R z-xkcd-panda-comic "/path/to/your/.agent/skills/"

# 或安装全部 Skill
cp -R z-* "/path/to/your/.agent/skills/"
```

安装后按宿主要求刷新 Skills 或开启新会话，再用自然语言描述任务，也可明确点名 Skill。复制目录只安装工作流与资源，Python 包、系统工具和模型 API 仍需按各 Skill 的说明配置。

下文脚本命令均从克隆后的仓库根目录运行；若已安装到其他目录，请相应调整脚本路径。`python3` 应指向已安装所需依赖的环境。

## Skills 一览

| Skill | 用途 | 典型触发 |
| --- | --- | --- |
| [`z-web-pack`](z-web-pack/SKILL.md) | 采集网页正文、链接、图片和视频链接，整理成本地写作素材包 | 采集网页素材、把链接正文拿到本地、做成备用写作素材包 |
| [`z-video-downloader`](z-video-downloader/SKILL.md) | 下载 YouTube、B站、微信视频号、m3u8、mp4 直链等视频 | 下载视频、下载 B站、下载 YouTube、下载 m3u8、下载视频号 |
| [`z-video-study-webpage-qwen`](z-video-study-webpage-qwen/SKILL.md) | 用转录、关键帧和 Qwen 多模态分析视频，生成图文学习网页 | 理解视频内容、视频学习总结网页、关键知识点匹配画面 |
| [`z-qwen-audio-studio`](z-qwen-audio-studio/SKILL.md) | 用 qwen-audio-3.1-tts-next 生成播客、广播剧、广告和包含环境声、音效、BGM 的完整音频 | 全景音频、双人播客、广播剧、环境声、动作音效、参考音频、TTS Next |
| [`z-smart-xparse`](z-smart-xparse/SKILL.md) | 用 xparse-cli 把 PDF、图片、Office 等文档转成 Markdown 或结构化结果 | 解析 PDF、文档转 Markdown、读取扫描件 |
| [`z-mail-reader`](z-mail-reader/SKILL.md) | 通过 IMAP 读取邮件、下载附件、摘要邮件内容、监听新邮件 | 读邮件、查收邮件、邮件摘要、监听邮件 |
| [`z-md-to-word`](z-md-to-word/SKILL.md) | 把本地 Markdown 文章转换成 Word 文档，生成 `.docx` 和 `.doc` 并做打开检查 | 转成doc、Markdown转Word、md转doc、导出Word |
| [`z-md-to-pdf`](z-md-to-pdf/SKILL.md) | 把 Markdown 排成学术、书籍、现代报告三种中文 PDF，支持指定风格、批量生成和 XeLaTeX 项目复编 | Markdown转PDF、排版成PDF、一次生成多种风格PDF |
| [`z-poetry-book`](z-poetry-book/SKILL.md) | 把诗词、古籍资料和技术文章做成有出处、可重建、逐页校验的图文书，内置六套宋式审美主题 | 编年诗传、诗词成书、技术文章样张、青瓷/墨禅/月夜/竹影模板 |
| [`z-md-excel`](z-md-excel/SKILL.md) | 把 Markdown 里的表格提取成 Excel 文件 | Markdown 表格转 Excel、导出 MD 表格 |
| [`z-excel-editor`](z-excel-editor/SKILL.md) | 读取、编辑、清洗、格式化电子表格文件 | 修改 xlsx、清洗 csv、补公式、做表格 |
| [`z-xkcd-panda-comic`](z-xkcd-panda-comic/SKILL.md) | 把文章、主题或观点改写成黑白手绘四格熊猫梗图 | 四格漫画、金馆长熊猫表情、金教授熊猫脸、熊猫梗图、文章转四格漫画 |
| [`z-wanghong-handwritten-ppt`](z-wanghong-handwritten-ppt/SKILL.md) | 把文章或讲稿制作成 16:9 Notability 学术手写风 HTML 幻灯片并导出 PNG | 王虹PPT风格、王虹手写PPT、Notability学术手写幻灯片、手写网页PPT |
| [`z-wanghong-handwritten-video`](z-wanghong-handwritten-video/SKILL.md) | 直接驱动王虹手写 PPT 的原 HTML DOM，锁定预览封面字形和原布局，输出无音轨动画 MP4 | 动画版王虹PPT、王虹手写动画、Notability手写视频、手写PPT转MP4 |
| [`z-grounded-source-qa`](z-grounded-source-qa/SKILL.md) | 对任意本地 Markdown/TXT 资料做多表达式检索、证据型问答、核对和写作 | 只根据这些资料回答、按原文核对、给出出处、从访谈里找依据 |
| [`z-expense-policy-qa`](z-expense-policy-qa/SKILL.md) | 把报销与差旅制度变成可核对金额、材料、时限、例外和条款出处的问答助手，内置虚构演示制度 | 报销制度、差旅标准、这笔钱能不能报、缺什么材料 |
| [`z-liang-wenfeng-grounded-voice`](z-liang-wenfeng-grounded-voice/SKILL.md) | 基于梁文锋交流会材料做第一人称模拟回答、观点推演和来源核对 | 梁文锋交流会材料、现在你是梁文锋、记者追问、按原文核对 |
| [`z-sci-viz-lab`](z-sci-viz-lab/SKILL.md) | 把数学/科学概念生成可视化互动科普单页，支持多场景切换、Three.js/Canvas、单文件构建与 Cloudflare Pages 部署 | 可视化科普、互动科普实验、科学交互演示 |
| [`z-docx-format-brush`](z-docx-format-brush/SKILL.md) | 从模板 docx 提取格式指纹（字体/字号/行距/缩进/表格边框/封面/分页），统一刷到目标 docx，修复 pandoc/模型产物的格式混乱 | 格式刷、格式统一、套用模板格式、docx格式修复、公文格式 |

## z-web-pack 与 z-video-downloader 边界

`z-web-pack` 负责网页素材包采集，包含正文、正文相关链接、图片、本地阅读地图、媒体链接清单，以及受限来源恢复说明

`z-video-downloader` 负责视频下载，包含 YouTube、Bilibili、Vimeo、X/Twitter、TikTok、抖音、Instagram、Facebook、**微信视频号**、m3u8 和常见视频直链，并支持断点续传、批量清单、字幕、封面和下载历史。视频号分享链接（`weixin.qq.com/sph/`）通过在线解析服务自动获取视频地址，无需额外安装

`z-web-pack` 发现视频时只写入 `04-media-inventory.md`。如果要把视频保存到本地，把清单中的 Source URL 交给 `z-video-downloader`

### 采集网页素材

先在所用 Python 环境安装 `requests`、`beautifulsoup4`、`readability-lxml` 等依赖，完整流程见 [z-web-pack](z-web-pack/SKILL.md)。

```bash
python3 z-web-pack/scripts/collect_web_pack.py \
  --out-root "./Clippings/Reading" \
  --title "主题名" \
  --max-depth 0 \
  --max-pages 1 \
  "https://example.com/article"
```

输出里重点看：

- `README.md`
- `00-research-brief.md`
- `01-link-inventory.md`
- `02-image-inventory.md`
- `03-reading-map.md`
- `04-media-inventory.md`

### 下载视频

需要 Python 的 `requests`，平台视频另需 `yt-dlp`，音视频合并需 `ffmpeg`。平台可用性受登录态、风控和解析服务状态影响，详细策略见 [z-video-downloader](z-video-downloader/SKILL.md)。

```bash
python3 z-video-downloader/scripts/download_video.py \
  --out-root "./Video/Downloads" \
  --title "主题名" \
  "https://www.bilibili.com/video/BV..."
```

如果视频链接来自网页素材包，使用 `04-media-inventory.md` 里的 Source URL

也可以直接读取媒体清单：

```bash
python3 z-video-downloader/scripts/download_video.py \
  --inventory "/path/to/04-media-inventory.md"
```

## Qwen Audio Next 全景音频 Skill

`z-qwen-audio-studio` 调用阿里云百炼 `qwen-audio-3.1-tts-next`，支持：

- 单人叙事、商业广告、双人或多人播客、广播剧
- 环境声、动作音效和背景音乐
- 最多 3 条参考音频，通过 `@voice1`、`@voice2`、`@voice3` 引用
- WAV、MP3、PCM 输出，最高 48kHz 双声道
- 下载后自动执行 ffprobe 和 ffmpeg 完整解码验收
- API Key、Workspace ID、参考音频 Base64 和接口域名脱敏

首次使用前需准备：

1. 在阿里云百炼华北 2（北京）地域开通 `qwen-audio-3.1-tts-next`
2. 创建该地域可用的 API Key
3. 获取 API Key 所在业务空间的 Workspace ID
4. 安装 Python 3.9+、`requests`、`ffmpeg` 和 `ffprobe`
5. 在私有终端会话设置环境变量

```bash
export DASHSCOPE_API_KEY="your-api-key"
export SFM_WORKSPACE_ID="your-workspace-id"
python3 z-qwen-audio-studio/scripts/qwen_audio_studio.py doctor
```

`doctor` 只显示依赖和环境变量是否已配置，不显示凭据内容。完整准备流程见 [环境准备说明](z-qwen-audio-studio/references/setup.md)。

## Markdown 转 Word Skill

`z-md-to-word` 用来把本地 Markdown 文章转换成 Word 文档，适合公众号文章、Obsidian 笔记、商单稿件和需要交付 `.doc` / `.docx` 的场景。

它会自动处理几个常见问题：

- 保留 Markdown 标题、作者和日期
- 写入远程图片和本地图片
- 跳过空上传占位符
- 修正常见列表识别问题
- 生成后检查文档是否能打开和渲染

默认输出：

```text
output/doc/<原文件名>.docx
output/doc/<原文件名>.doc
```

## 诗词与技术文章成书

[z-poetry-book](z-poetry-book/README.md) 将诗词、古籍资料、Markdown 技术文章和课程讲义制作成有出处、可重建的 LaTeX PDF，保留来源清单、图片、构建文件、校验报告与预览图。

| 主题 ID | 名称 | 风格 |
| --- | --- | --- |
| `song-mist` | 烟雨留白 | 米白、淡墨、远山、江面与朱印；默认主题 |
| `celadon` | 青瓷天青 | 青灰纸色、天青层山 |
| `ink-zen` | 墨禅寂照 | 灰白、墨山、圆相与墨评 |
| `cinnabar-seal` | 朱砂印谱 | 米纸、朱砂、鉴藏印章 |
| `moon-river` | 月夜赤壁 | 蓝灰、明月、江水与夜航 |
| `bamboo` | 竹影清风 | 淡青绿、疏竹与叶影 |

![Poetry Book 六套主题预览](z-poetry-book/docs/images/theme-gallery.png)

默认简体中文横排。诗词书稿使用带来源的结构化 JSON；技术文章可直接读取受支持的 Markdown 结构。

专用安装器默认安装到 `~/.agents/skills/poetry-book/`：

```bash
# 在仓库根目录运行
python3 z-poetry-book/scripts/install.py
```

先按 [环境要求](z-poetry-book/README.md#环境要求) 配置 `latexmk`、LuaLaTeX、Ghostscript、中文字体和 Python 依赖，再从仓库根目录构建：

```bash
# 诗词或文集：使用仓库自带示例
python3 z-poetry-book/scripts/render_book.py \
  --input "z-poetry-book/examples/book.json" \
  --theme song-mist \
  --output "./output/poetry-demo"

# 技术文章：替换为你的 Markdown 文件
python3 z-poetry-book/scripts/render_article.py \
  --input "/absolute/path/article.md" \
  --theme celadon \
  --title "文章主标题" \
  --author "作者或栏目名" \
  --output "./output/article-demo"
```

输出目录须为空或不存在。交付前应确认 `validation-report.json` 的 `passed` 为 `true`，并查看封面和代表页面。当前 Markdown 模式的范围与限制、离线重建和完整案例见 [详细说明](z-poetry-book/README.md)。

## docx 格式刷 Skill

`z-docx-format-brush` 用来把一份模板 docx 的格式"刷"到另一份 docx 上，核心思想是格式参数从模板实测提取、收敛到唯一出口应用

典型场景：

- 修复 pandoc / 大模型产出的格式混乱 docx（字体混排、标题带蓝色、表格无边框、引号反向）
- 参照模板从零生成格式一致的公文类文档
- 诊断两份 docx 的格式差异

三步工作流：

```bash
# 1. 解剖模板 → 格式指纹 JSON
python3 z-docx-format-brush/scripts/extract_fingerprint.py 模板.docx --json fp.json

# 2A. 从零新建：结构化内容统一经过格式工厂
python3 z-docx-format-brush/scripts/gen_from_template.py content.json --config fp.json --out 新文档.docx

# 2B. 修复已有文档：五层格式刷（样式/段落/封面/表格/文字）
python3 z-docx-format-brush/scripts/apply_format.py 目标.docx --config fp.json

# 3. 执行基础格式检查；模板一致性还需结合格式指纹和渲染结果复核
python3 z-docx-format-brush/scripts/verify_format.py 目标.docx
```

详细方法论和踩坑记录见 [docx 格式刷说明](z-docx-format-brush/README.md)

## 熊猫四格漫画 Skill

`z-xkcd-panda-comic` 用来把文章或主题变成一张 2x2 四格漫画，默认风格是：

- 黑白手绘漫画
- 金馆长熊猫表情味 / 金教授熊猫脸
- 中文短对白
- xkcd 式冷幽默节奏
- 适合插入公众号、Obsidian、Markdown 文章

它会先提炼文章核心观点，再设计四格节奏：

1. 设定痛点或误会
2. 普通办法暴露荒诞
3. 熊猫角色给出解决动作
4. 用一句话收束核心观点

目录内包含一张参考风格图：

```text
z-xkcd-panda-comic/assets/reference-codex-computer-housekeeper-panda-comic.png
```

## 使用建议

部分 Skill 保留了作者本机的路径和外部能力约定。首次使用时，应把 `/Users/zz/...` 等路径替换为自己的工作区、Python 环境与输出目录；被引用的外部 Skill 或服务需另行准备。本仓库没有统一的一键依赖安装脚本。

- 每个 skill 都以自己的 `SKILL.md` 为准
- 有脚本的 skill 优先使用脚本，避免手工重复操作
- 处理外部文件、邮件、视频和网页时，先确认路径、链接和权限
- 生成文章或图片后，尽量做一次实际查看或运行验证
- 网页素材采集和视频下载分开维护，降低单个 skill 的复杂度
- 视频平台风控、cookie、画质、播放列表等逻辑统一放在 `z-video-downloader`
- `z-web-pack` 的媒体清单只做发现和转交提示，避免采集资料时意外下载大文件
- 单篇新闻默认使用保守采集模式；遇到付费墙或验证码时保留受限说明，再补公开来源
- 视频下载支持 `.part` 续传；输入无效时会在创建空目录前停止

## 目录结构

```text
z-skills/
  docs/
    index.html
  z-poetry-book/
    SKILL.md
    README.md
    assets/
    scripts/
    examples/
    tests/
    docs/
  z-wanghong-handwritten-ppt/
    SKILL.md
    templates/
    assets/
    examples/
    references/
    scripts/
    evals/
  z-wanghong-handwritten-video/
    SKILL.md
    scripts/
    examples/
    references/
    tests/
    evals/
  z-xkcd-panda-comic/
    SKILL.md
    assets/
    evals/
  z-docx-format-brush/
    SKILL.md
    README.md
    scripts/
  z-md-to-word/
    SKILL.md
    README.md
    scripts/
    evals/
  z-video-downloader/
    SKILL.md
    scripts/
    tests/
  z-video-study-webpage-qwen/
    SKILL.md
    scripts/
    tests/
  z-qwen-audio-studio/
    SKILL.md
    agents/
    references/
    scripts/
    tests/
    evals/
  z-liang-wenfeng-grounded-voice/
    SKILL.md
    examples/
    references/
    tests/
  z-grounded-source-qa/
    SKILL.md
    README.md
    scripts/
    references/
    tests/
    evals/
  z-expense-policy-qa/
    SKILL.md
    references/
    scripts/
    examples/
    tests/
    evals/
  ...
```

## 维护方式

新增 skill 时建议包含：

- `SKILL.md`：触发词、执行流程、输出规范
- `scripts/`：可复用脚本
- `assets/`：参考图、模板或固定素材
- `evals/`：示例输入和评估用例
- `README.md`：复杂 skill 可单独补充说明

更新 Skill 时，同步核对本页的目录入口、用途、安装示例与依赖说明；命令示例使用可替换路径，避免把个人凭据或本机配置写入公开文档。

保持触发词清楚、流程可执行、输出可验证，是这个库的核心原则。
