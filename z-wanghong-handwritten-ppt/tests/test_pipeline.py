#!/usr/bin/env python3
"""构建 / 检查 / 导出 全流程测试。

python3 -m unittest discover -s tests
没有 Chrome / Edge 时，浏览器相关用例自动跳过。
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
TEMPLATE = SKILL / "templates" / "slides.html"
EXAMPLE = SKILL / "examples" / "deepseek-v4-flash"
sys.path.insert(0, str(SCRIPTS))

from _chrome import find_chrome, png_size  # noqa: E402
from build import build  # noqa: E402
from check_deck import static_checks  # noqa: E402

CHROME = find_chrome(None)


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=600)


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory(prefix="wh-test-")
        cls.out = Path(cls.tmp.name)
        cls.outputs = build(TEMPLATE, cls.out, font="xiaolai", quiet=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_two_self_contained_files(self) -> None:
        self.assertEqual([p.name for p in self.outputs], ["index.html", "index-timeline.html"])
        for path in self.outputs:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn('id="wh-runtime"', text)
                self.assertIn('id="wh-template"', text)
                self.assertIn('id="wh-font"', text)
                self.assertIn("@font-face", text)
                self.assertNotIn("../assets/", text, "源稿里的预览用相对引用必须被替换掉")
                self.assertEqual(text.count('id="wh-runtime"'), 1)

    def test_modes_link_to_each_other(self) -> None:
        static = self.outputs[0].read_text(encoding="utf-8")
        steps = self.outputs[1].read_text(encoding="utf-8")
        self.assertRegex(static, r'<main[^>]*data-mode="static"[^>]*data-alt="index-timeline.html"')
        self.assertRegex(steps, r'<main[^>]*data-mode="steps"[^>]*data-alt="index.html"')

    def test_rebuild_from_output_is_idempotent(self) -> None:
        # 对已构建文件再次构建，不应叠加第二份运行时 / 样式
        with tempfile.TemporaryDirectory() as d:
            again = build(self.outputs[0], Path(d), font="xiaolai", timeline=False, quiet=True)[0]
            text = again.read_text(encoding="utf-8")
            self.assertEqual(text.count('id="wh-runtime"'), 1)
            self.assertEqual(text.count('id="wh-template"'), 1)
            self.assertEqual(text.count('id="wh-font"'), 1)

    def test_refuses_to_overwrite_source(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "index.html"
            shutil.copy(TEMPLATE, src)
            with self.assertRaises(SystemExit):
                build(src, Path(d), font="xiaolai", quiet=True)

    def test_local_images_are_inlined(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "img").mkdir()
            # 1x1 PNG
            (d / "img" / "a.png").write_bytes(bytes.fromhex(
                "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"))
            src = d / "slides.html"
            src.write_text(TEMPLATE.read_text(encoding="utf-8").replace(
                '<div class="cover-art">', '<div class="cover-art"><img src="img/a.png" alt="">', 1), encoding="utf-8")
            out = build(src, d / "out", font="xiaolai", timeline=False, quiet=True)[0]
            self.assertNotIn('src="img/a.png"', out.read_text(encoding="utf-8"))
            self.assertRegex(out.read_text(encoding="utf-8"), r'src="data:image/')

    def test_missing_image_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "slides.html"
            src.write_text(TEMPLATE.read_text(encoding="utf-8").replace(
                '<div class="cover-art">', '<div class="cover-art"><img src="img/none.png" alt="">', 1), encoding="utf-8")
            with self.assertRaises(SystemExit):
                build(src, Path(d) / "out", font="xiaolai", quiet=True)


class StaticCheckTests(unittest.TestCase):
    def test_template_is_clean(self) -> None:
        errors, warnings, count = static_checks(TEMPLATE.read_text(encoding="utf-8"))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(count, 9)

    def test_detects_missing_notes_and_deck(self) -> None:
        errors, warnings, _ = static_checks('<section class="slide"><p>x</p></section>')
        self.assertTrue(any("deck" in e for e in errors))
        self.assertTrue(any("讲稿" in w for w in warnings))

    def test_example_matches_its_source(self) -> None:
        src = (EXAMPLE / "slides.html").read_text(encoding="utf-8")
        built = (EXAMPLE / "index.html").read_text(encoding="utf-8")
        titles = re.findall(r'data-title="([^"]+)"', src)
        self.assertEqual(titles, re.findall(r'data-title="([^"]+)"', built), "示例成品过期：请重新运行 build.py")
        self.assertIn('id="wh-runtime"', (EXAMPLE / "index-timeline.html").read_text(encoding="utf-8"))

    def test_bundled_font_covers_common_symbols(self) -> None:
        table = (SKILL / "assets" / "fonts" / "Xiaolai-GB2312.chars.txt").read_text(encoding="utf-8")
        for c in "·•—−→←↑↓×≈①「」“”…％：":
            with self.subTest(char=c):
                self.assertIn(c, table)

    def test_runtime_syntax(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("没有 node")
        proc = subprocess.run([node, "--check", str(SKILL / "assets" / "runtime.js")], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


@unittest.skipUnless(CHROME, "没有找到 Chrome / Edge")
class BrowserTests(unittest.TestCase):
    def test_template_passes_layout_audit(self) -> None:
        proc = run(str(SCRIPTS / "check_deck.py"), str(TEMPLATE), "--json")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual(len(report["pages"]), 9)
        self.assertEqual(sum(len(p["errors"]) for p in report["pages"]), 0)

    def test_audit_catches_overflow(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "slides.html"
            long = "".join(f'<p class="line">第 {i} 行很长很长很长的内容，用来把页面撑破</p>' for i in range(30))
            src.write_text(TEMPLATE.read_text(encoding="utf-8").replace(
                '<p class="line">代价：', long + '<p class="line">代价：', 1), encoding="utf-8")
            proc = run(str(SCRIPTS / "check_deck.py"), str(src))
            self.assertEqual(proc.returncode, 1, proc.stdout)
            self.assertIn("第 2 页", proc.stdout)

    def test_render_png_size(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            out = build(TEMPLATE, Path(d), font="xiaolai", timeline=False, quiet=True)[0]
            proc = run(str(SCRIPTS / "render.py"), str(out), "--slides", "1,5", "--no-sheet")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            for n in ("01", "05"):
                self.assertEqual(png_size(Path(d) / "png" / f"{n}.png"), (1920, 1080))


if __name__ == "__main__":
    unittest.main()
