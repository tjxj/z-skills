# 内容 JSON

```json
{
  "brand": "@你的账号",
  "pages": [
    {"type": "cover", "tag": "新手必看", "kicker": "写给第一次租房的人", "title": "第一次租房\n这样买不亏", "sub": "把钱花在每天都用的东西上", "tags": ["必买", "缓买"], "note": "先收藏"},
    {"type": "points", "tag": "必买", "title": "入住当天**必买**", "items": [{"head": "一盏落地灯", "text": "暖光立刻舒服"}, {"head": "多孔插线板", "text": "选带开关的"}], "note": "每一件都天天用"}
  ]
}
```

顶层：`brand` 账号名，`pages` 页面数组，`style` 可选（命令行 `--style` 优先）。

每页通用：`type` 必填；`tag` 页眉标签，≤8 字；`note` 页脚短句；`name` 导出文件名里的英文短名。

| type | 用途 | 字段 |
|---|---|---|
| `cover` | 封面 | `title` ≤16，`kicker` ≤16，`sub` ≤24，`tags` ≤4 个，`image` 可选 |
| `points` | 并列要点 | `title` ≤20，`items` 2–5 条 |
| `steps` | 有先后的步骤 | `title` ≤20，`items` 2–5 条 |
| `compare` | 两方对比 | `title` ≤20，`left`/`right` 各含 `label` ≤8 和 `items` 2–4 条（每条 ≤14），`verdict` ≤26 |
| `quote` | 金句 | `text` ≤48，`source` ≤16 |
| `stat` | 一个关键数字 | `title` ≤20，`value` ≤6，`unit` ≤4，`text` ≤30，`items` ≤3 条（`head` ≤8，`text` ≤12） |
| `image` | 截图或照片 | `title` ≤20，`image` 必填，`caption` ≤30 |
| `end` | 结尾 | `title` ≤20，`items` 2–5 条可选，`cta` ≤20 |

`items` 每条：`head` ≤12，`text` ≤30 可选。

字数按版面宽度计：一个汉字算 1，一个西文字符算 0.55。

写法：`\n` 手动换行，`**词**` 高亮。上限是版面能保证的边界，日常写到上限的七成效果最好。
