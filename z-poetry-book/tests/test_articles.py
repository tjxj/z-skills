#!/usr/bin/env python3
import argparse
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

SKILL_HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_HOME / "scripts"))

from article_render import wrap_code
from book_common import ManuscriptError, TeXCodec, load_json, validate_manuscript
from markdown_article import parse_markdown
from markdown_inline import plain_inline, tex_inline
from render_article import prepare


class ArticleTests(unittest.TestCase):
    def test_laozhang_structure_and_line_coverage(self):
        metadata, works = parse_markdown(SKILL_HOME / "examples" / "laozhang-deepinfer" / "source.md")
        self.assertEqual(metadata["date"], "2026-10-25")
        self.assertEqual(len(works), 5)
        self.assertEqual(works[0]["line_start"], 13)
        self.assertEqual(works[-1]["line_end"], 147)
        self.assertEqual(sum(block["type"] == "image" for work in works for block in work["blocks"]), 7)
        for previous, current in zip(works, works[1:]):
            self.assertGreater(current["line_start"], previous["line_end"])
        self.assertEqual(works[1]["title"], "通用引擎的硬核成绩单")
        self.assertEqual(works[-1]["title"], "未来很多模型都会有专属推理引擎吗？")

    def prepare_fixture(self, directory):
        args = argparse.Namespace(
            input=str(SKILL_HOME / "examples" / "technical-fixture.md"),
            output=str(Path(directory) / "output"),
            assets_dir=str(Path(directory) / "assets"),
            offline=True,
            theme="celadon",
            title=None,
            subtitle="测试副标题",
            author=None,
            series="技术专题",
            edition="测试本",
            seal="测",
            subject=None,
            date=None,
            require=["Prefill"],
        )
        book_json, images = prepare(args)
        return load_json(book_json), images

    def test_fixture_parses_all_supported_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            payload, images = self.prepare_fixture(directory)
            self.assertEqual(images, 0)
            self.assertEqual(payload["document_type"], "article")
            self.assertEqual(payload["metadata"]["title"], "技术排版夹具")
            self.assertEqual(payload["links"], ["https://example.com/?a=1&b=2"])
            kinds = [block["type"] for block in payload["chapters"][0]["works"][1]["blocks"]]
            self.assertEqual(kinds, ["code", "table", "quote", "list", "list"])
            self.assertEqual(validate_manuscript(payload)["works"], 2)

    def test_inline_markup_and_unclosed_bold(self):
        codec = TeXCodec()
        self.assertEqual(plain_inline("先看 **SGLang："), "先看 SGLang：")
        rendered = tex_inline(codec, "**加粗** 和 `code` 和 **未闭合")
        self.assertIn("\\textbf{加粗}", rendered)
        self.assertIn("\\texttt{code}", rendered)
        self.assertNotIn("**", rendered)
        unsafe = tex_inline(codec, "[链接](javascript:alert(1))")
        self.assertNotIn("href", unsafe)

    def test_long_code_is_wrapped_without_changing_source(self):
        source = "x" * 200
        wrapped = wrap_code(source)
        self.assertEqual(wrapped.replace("\n", "").replace(" ", ""), source)
        self.assertTrue(all(len(line) <= 88 for line in wrapped.splitlines()))

    def test_unsupported_structures_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.md"
            path.write_text("  - 嵌套列表\n", encoding="utf-8")
            with self.assertRaises(ManuscriptError):
                parse_markdown(path)
            path.write_text("<div>HTML</div>\n", encoding="utf-8")
            with self.assertRaises(ManuscriptError):
                parse_markdown(path)

    def test_invalid_image_path_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            payload, _ = self.prepare_fixture(directory)
            work = payload["chapters"][0]["works"][0]
            work["blocks"] = [{"type": "image", "caption": "坏路径", "path": "../secret.png", "source": ""}]
            with self.assertRaisesRegex(ManuscriptError, "安全的图片相对路径"):
                validate_manuscript(payload)

    def test_offline_missing_image_fails(self):
        from markdown_article import materialize_images

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.md"
            source.write_text("![](https://example.com/missing.png)\n", encoding="utf-8")
            _, works = parse_markdown(source)
            with self.assertRaisesRegex(ManuscriptError, "离线模式缺少图片"):
                materialize_images(source, works, Path(directory) / "assets", offline=True)


if __name__ == "__main__":
    unittest.main()
