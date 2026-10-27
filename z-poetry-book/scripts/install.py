#!/usr/bin/env python3
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="安装 Poetry Book Skill")
    parser.add_argument("--dest", default=str(Path.home() / ".agents" / "skills" / "poetry-book"))
    args = parser.parse_args()
    destination = Path(args.dest).expanduser().absolute()
    if destination.is_symlink():
        raise SystemExit(f"拒绝安装到符号链接：{destination}")
    if destination.resolve() == ROOT:
        print(f"Poetry Book 已位于目标目录：{destination}")
        return
    if destination.exists():
        skill_file = destination / "SKILL.md"
        if not destination.is_dir() or not skill_file.is_file() or "name: poetry-book" not in skill_file.read_text(encoding="utf-8"):
            raise SystemExit(f"目标已存在且不是 Poetry Book 技能，停止覆盖：{destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", "dist", "__pycache__", "*.pyc"))
    print(f"Poetry Book 已安装：{destination}")


if __name__ == "__main__":
    main()
