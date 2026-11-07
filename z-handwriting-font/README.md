# z-handwriting-font 手写字体工坊

把自己或家人的手写字做成可安装的 OpenType 字体。两条路线：

- **格子路线**：打印模板 → 一格写一个字 → 手机拍照 → 自动定位、裁切、对齐标签 → 生成字体。推荐。
- **信件路线**：只有一封旧信或一页笔记 → 按逐字抄录切出现有的字 → 人工核对方框 → 生成字体。

```bash
npx skills add tjxj/z-skills --skill z-handwriting-font
pip install -r requirements.txt && brew install potrace
```

然后对 Agent 说“帮我把我的手写字做成字体”即可。完整流程、参数与局限见 [SKILL.md](SKILL.md)。

字形只来自你提供的照片，不使用任何现成字体的轮廓或数据。`tests/make_synthetic.py` 可以用一份你有权使用的字体模拟“手写+拍照”，用来端到端自测。

这不是专业字库：没有逐字修形和字偶距，汉字只覆盖你写过的那些。字迹属于书写者，公开发布前请先征得同意并选好许可证。
