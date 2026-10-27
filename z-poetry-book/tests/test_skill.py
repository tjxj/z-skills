#!/usr/bin/env python3
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL_HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_HOME / "scripts"))

from book_common import ManuscriptError, load_json, safe_filename, validate_manuscript
from build_style import build_style, load_themes


class PoetryBookSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = load_json(SKILL_HOME / "examples" / "book.json")

    def style_args(self, theme, output):
        return argparse.Namespace(
            config=str(SKILL_HOME / "assets" / "themes.json"),
            assets=str(SKILL_HOME / "assets"),
            font_dir=str(SKILL_HOME / "assets" / "fonts"),
            theme=theme,
            output=str(output),
            title="月照诗心",
            subtitle="独立测试",
            author="李清照",
            series="编年诗选",
            edition="测试本",
            seal="易安",
            subject="通用技能测试",
            keywords="诗词,横排",
        )

    def test_six_themes_generate_real_styles(self):
        payload, _ = load_themes(SKILL_HOME / "assets" / "themes.json")
        self.assertEqual(payload["default"], "song-mist")
        self.assertEqual(len(payload["themes"]), 6)
        with tempfile.TemporaryDirectory() as directory:
            for theme in payload["themes"]:
                with self.subTest(theme=theme["id"]):
                    output = Path(directory) / f"{theme['id']}.tex"
                    result = build_style(self.style_args(theme["id"], output))
                    self.assertEqual(result["theme"], theme["id"])
                    style = output.read_text(encoding="utf-8")
                    self.assertIn("\\newcommand{\\ThemeCover}", style)
                    self.assertIn("月照诗心", style)
                    self.assertNotIn("%THEME_DEFINITIONS%", style)
                    self.assertIn(str(SKILL_HOME / "assets" / "fonts"), style)

    def test_unknown_theme_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ManuscriptError, "未知主题"):
                build_style(self.style_args("not-a-theme", Path(directory) / "style.tex"))

    def test_theme_list_cli(self):
        result = subprocess.run(
            [sys.executable, str(SKILL_HOME / "scripts" / "build_style.py"), "--list"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(len(json.loads(result.stdout)["themes"]), 6)

    def test_example_is_valid_and_not_sushi(self):
        quality = validate_manuscript(self.example)
        self.assertEqual(quality["works"], 4)
        self.assertEqual(quality["warnings"], [])
        self.assertEqual(self.example["metadata"]["author"], "李清照")

    def test_duplicate_work_id_fails(self):
        payload = copy.deepcopy(self.example)
        payload["chapters"][0]["works"][1]["id"] = "L001"
        with self.assertRaisesRegex(ManuscriptError, "ID 重复"):
            validate_manuscript(payload)

    def test_reverse_chronology_fails(self):
        payload = copy.deepcopy(self.example)
        payload["chapters"][0]["works"][0]["date"].update({"start": 1200, "end": 1200})
        with self.assertRaisesRegex(ManuscriptError, "升序"):
            validate_manuscript(payload)

    def test_unsafe_work_id_fails(self):
        payload = copy.deepcopy(self.example)
        payload["chapters"][0]["works"][0]["id"] = "../escape"
        with self.assertRaisesRegex(ManuscriptError, "id"):
            validate_manuscript(payload)

    def test_missing_source_fails(self):
        payload = copy.deepcopy(self.example)
        payload["chapters"][0]["works"][0]["sources"] = []
        with self.assertRaisesRegex(ManuscriptError, "来源"):
            validate_manuscript(payload)

    def test_empty_paragraph_fails(self):
        payload = copy.deepcopy(self.example)
        payload["chapters"][0]["works"][0]["paragraphs"] = [""]
        with self.assertRaisesRegex(ManuscriptError, "非空文本"):
            validate_manuscript(payload)

    def test_output_filename_cannot_escape(self):
        self.assertEqual(safe_filename("诗/词"), "诗_词")
        with self.assertRaises(ManuscriptError):
            safe_filename("..")

    def test_duplicate_chapter_id_fails(self):
        payload = copy.deepcopy(self.example)
        payload["chapters"][1]["id"] = "early"
        with self.assertRaisesRegex(ManuscriptError, "章节 ID 重复"):
            validate_manuscript(payload)

    def test_unknown_year_must_use_appendix(self):
        payload = copy.deepcopy(self.example)
        payload["chapters"][0]["works"][0]["date"].update({"start": None, "end": None})
        with self.assertRaisesRegex(ManuscriptError, "appendix"):
            validate_manuscript(payload)

    def test_index_must_be_boolean(self):
        payload = copy.deepcopy(self.example)
        payload["index"] = "false"
        with self.assertRaisesRegex(ManuscriptError, "布尔值"):
            validate_manuscript(payload)

    def test_appendix_only_book_renders(self):
        from book_common import TeXCodec, normalized_metadata
        from render_book import render_manuscript, validation_expectations

        payload = copy.deepcopy(self.example)
        del payload["chapters"]
        self.assertEqual(validate_manuscript(payload)["works"], 1)
        rendered = render_manuscript(payload, TeXCodec())
        self.assertIn("系年未详作品", rendered)
        expectations = validation_expectations(payload, normalized_metadata(payload))
        self.assertEqual(expectations["golden"], {"L004": "千古风流八咏楼，江山留与后人愁。"})

    def test_no_machine_specific_paths_in_skill(self):
        paths = [SKILL_HOME / "SKILL.md"]
        paths.extend((SKILL_HOME / "scripts").glob("*.py"))
        paths.extend((SKILL_HOME / "assets").rglob("*.tex"))
        for path in paths:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("/Users/", text)
                self.assertNotIn("sushi-poetry-book", text)


if __name__ == "__main__":
    unittest.main()
