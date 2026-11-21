# data.json 字段说明

必填只有 `topic`、`dimensions`、`items`，其余都有默认值。

## 顶层

| 字段 | 默认 | 说明 |
|---|---|---|
| `topic` | 必填 | 主题，也是默认标题 |
| `scope` | 空 | 收录范围，写进依据表 |
| `asof` | 今天 | 截至日期 `YYYY-MM-DD`；页脚写「截至 2026.11.21」，标题上方写「TIER LIST · 2026.11」 |
| `title` | `topic` | 大标题，太长会自动缩小或折行，建议 ≤ 12 字 |
| `subtitle` | 自动 | 不写时为「16 个候选 · 32 个独立来源 · 5 维加权打分」；写 `""` 不显示 |
| `kicker` | `TIER LIST · 年.月` | 标题上方的小字 |
| `seal` | `从夯到拉` | 右上角印章，2 字或 4 字；写 `""` 不显示 |
| `theme` | `ink` | `ink` 暗金 / `paper` 宣纸；命令行 `--theme` 优先 |
| `layout` | `auto` | `auto` / `tile` 方块 / `pill` 横条 / `compact` 紧凑；命令行 `--layout` 优先 |
| `byline` | 空 | 署名，显示在页脚第一行右侧 |
| `show_score` | `true` | 显示加权分 |
| `show_notes` | `true` | 显示档位下方的小字（封神 / 强推 / 能打 / 路人 / 避雷） |
| `ghost` | `true` | 夯档背景里的大号水印字 |
| `empty_text` | `虚位以待` | 空档显示的文字 |
| `file_stem` | `{topic}-夯到拉` | 输出文件名前缀 |
| `footer_sources` | 自动 | 页脚「来源」一行；不写时取被引用最多的 4 个来源名 + 独立链接数 |
| `tiers` | 见下 | 改档位名或小字：`[{"name": "夯", "note": "封神"}, …]`，按顺序覆盖，最多 5 个 |
| `cuts` | `[9.0, 8.0, 7.0, 5.5]` | 分档线，从高到低 4 个 |
| `forbid` | `[]` | 本次任务的禁用词，和 `forbid.txt` 叠加 |
| `dimensions` | 必填 | 评分维度，见下 |
| `items` | 必填 | 候选，见下 |
| `sources` | `[]` | 不挂在某个候选下的公共来源（总榜、行业报告） |

## dimensions[]

```json
{"key": "taste", "name": "产品力", "weight": 30, "rubric": "10=爆品多、复购高；7=稳定好喝；4=一般；1=难喝"}
```

- `key`：英文短名，`items[].scores` 用它
- `name`：上图的维度名，2-4 字最好
- `weight`：权重，所有维度加起来 100
- `rubric`：打分锚点，依据表里会展示

## items[]

下面是格式示意（虚构品牌）：

```json
{
  "name": "山海茶铺·鲜果茶系列",
  "short": "山海茶铺",
  "icon": {"mono": "山", "color": "#2F6B4F"},
  "scores": {"taste": 8.5, "scale": 7, "price": 8, "safety": 9, "brand": 6},
  "tier": "",
  "override_reason": "",
  "verdict": "小而美，复购王",
  "summary": "门店数两家机构口径不同，取低值",
  "evidence": []
}
```

| 字段 | 说明 |
|---|---|
| `name` | 全名，依据表用它 |
| `short` | 上图用的短名；名字超过 13 字宽时必写 |
| `icon` | 图标，见下 |
| `scores` | 每个维度 0-10 分，可以有 0.5 |
| `tier` | 手动指定档位（`"夯"` / `"t0"` / `0` 都行）；和分数算出来的不一样时必须写 `override_reason` |
| `override_reason` | 改档理由，依据表里公开 |
| `verdict` | 上图锐评，≤ 12 字 |
| `summary` | 依据表里的补充说明：分歧、口径、保守给分的原因 |
| `evidence` | 证据列表 |

## evidence[]

| 字段 | 说明 |
|---|---|
| `text` | 一句话事实，带数字和口径 |
| `source` | 来源名（媒体、机构、榜单） |
| `url` | 具体页面链接 |
| `date` | `YYYY-MM-DD` 或 `YYYY-MM` |
| `type` | `官方` / `榜单` / `评测` / `市场` / `媒体` / `口碑` |
| `neg` | 负面证据写 `true` |

## sources[]

```json
{"name": "Artificial Analysis", "url": "https://artificialanalysis.ai/", "type": "榜单", "date": "2026-11-20", "note": "Intelligence Index"}
```

## 图标怎么选

| 写法 | 适合 | 例子 |
|---|---|---|
| `{"mono": "喜", "color": "#1C1C1C"}` | 品牌、公司、产品、人物。中文取一个代表字，英文取 1-2 个字母；`color` 用品牌主色 | 喜茶 → 喜，Kimi → K |
| `{"emoji": "🥟"}` | 食物、动物、地点、品类 | 包子 🥟、成都 🐼 |
| `{"image": "icons/xx.png", "bg": "#fff", "fit": "contain"}` | 有本地 logo 文件 | 相对路径以 data.json 所在目录为准；`fit: "cover"` 铺满（适合照片），默认留白居中 |

- 什么都不写：自动取名字第一个字做字标，颜色按名字算
- 远程图片 8 秒内加载不出来会自动退回字标，尽量用本地文件
- 同一档里的字标颜色别太接近，品牌色撞了就微调明度
- emoji 用常见的（Unicode 13 以内），太新的可能显示成方框
- 公开发布时字标最稳妥，用别人的 logo 先想清楚商标授权
