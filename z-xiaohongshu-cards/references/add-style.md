# 沉淀新风格

新风格优先做成 JSON 风格，内容和版式分开，别人用起来才稳定。

```text
styles/<id>/
  style.css     风格样式，排在 styles/_base/base.css 之后
  pages.html    可选，用同名 template 覆盖 styles/_base/pages.html 的骨架
  sample.json   示范内容，8 种页面类型各一页
  STYLE.md      气质、适用内容、色板、字体、招牌元素、注意事项
  preview.jpg   sample.json 的渲染总览
  samples/      3 张代表页，720×960 JPG
```

## 步骤

1. **取名**：`id` 用英文短横线，中文名四个字左右，要能让人想起画面，例如「红笔试卷」。
2. **定母题**：选一个现实中的物件或印刷工艺，让它决定版式。换个配色就能得到的方案不算新风格。
3. **写样式**：8 种页面类型都要实现，字体只用 `--serif --sans --mono --hand` 四个变量。装饰元素放进 `decor`，加 `data-bleed` 跳过检查。内容必须留在 `.main` 里。
4. **写样例**：文案要贴合风格的适用内容。
5. **写 STYLE.md**：照现有风格的小节写，色板写具体色值。
6. **更新索引**：`SKILL.md` 的风格表、`README.md` 的风格表、`docs/styles-grid.jpg`。
7. **验收**：

   ```bash
   node scripts/check_all.cjs --write-preview <id>
   ```

   命令会渲染样例，再用 `tests/stress.json` 把每个字段写到上限压测一遍。两边都要通过，再逐页看图。

## 沉淀已有作品

从作品的 `cards.html` 提取色板、字体和版式，按上面的结构重写。视频来源先把场景摊成静态页。来不及拆成 JSON 风格时，可以放 `template.html` 作为模板风格，图片换成 `.ph` 占位块。

## 授权

公开仓库只放自己写的风格和自己的作品样图。第三方模板和其他开源 Skill 的代码、版式都不要复制，也不要拿来当参考。
