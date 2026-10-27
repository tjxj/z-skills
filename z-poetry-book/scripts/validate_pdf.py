#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

import fitz
from PIL import Image, ImageDraw


def normalized(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text or ""))


def has_horizontal_text(page):
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span["text"].strip()
                if len(text) < 2 or abs(line["dir"][0]) < 0.9 or abs(line["dir"][1]) > 0.2:
                    continue
                x0, y0, x1, y1 = span["bbox"]
                if x1 - x0 > max(5, (y1 - y0) * 1.2):
                    return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--build-dir", default="build/book")
    parser.add_argument("--report", default="dist/validation-report.json")
    parser.add_argument("--render-dir")
    args = parser.parse_args()
    pdf_path = Path(args.pdf).resolve()
    build_dir = Path(args.build_dir).resolve()
    report_path = Path(args.report).resolve()
    render_dir = Path(args.render_dir).resolve() if args.render_dir else report_path.parent / "preview" / "full"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((build_dir / "manifest.json").read_text(encoding="utf-8"))
    font_usage = json.loads((build_dir / "font-usage.json").read_text(encoding="utf-8"))
    expectations = manifest.get("validation")
    if not isinstance(expectations, dict) or not expectations.get("pdf_title"):
        raise ValueError("manifest.json 缺少 validation.pdf_title；请先使用当前构建器重新生成书稿")
    checks = []

    def check(name, condition, detail=""):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    doc = fitz.open(pdf_path)
    check("PDF opens", not doc.needs_pass and not doc.is_encrypted, f"{len(doc)} pages")
    check("PDF metadata title", doc.metadata.get("title") == expectations["pdf_title"], doc.metadata.get("title"))
    expected_size = (185 / 25.4 * 72, 260 / 25.4 * 72)
    bad_sizes = [i + 1 for i, page in enumerate(doc) if abs(page.rect.width - expected_size[0]) > 0.5 or abs(page.rect.height - expected_size[1]) > 0.5]
    check("page dimensions", not bad_sizes, bad_sizes[:20])
    expected_ids = {x["id"] for x in manifest["works"]}
    records = [line.split() for line in (build_dir / "book.works").read_text().splitlines() if line.strip()]
    mapped = {}
    duplicates = []
    for record in records:
        if len(record) != 2 or not record[1].isdigit():
            duplicates.append(record)
            continue
        work_id, page = record
        if work_id in mapped:
            duplicates.append(record)
        mapped[work_id] = int(page)
    check("work records are unique", not duplicates, duplicates[:10])
    check("work record count", len(records) == len(expected_ids), f"{len(records)} / {len(expected_ids)}")
    check("all works mapped to PDF", set(mapped) == expected_ids, {"missing": sorted(expected_ids - set(mapped))[:20], "extra": sorted(set(mapped) - expected_ids)[:20]})
    check("mapped pages in range", all(1 <= page <= len(doc) for page in mapped.values()))
    text_by_page = {}
    for work_id, page_number in mapped.items():
        if page_number not in text_by_page:
            text_by_page[page_number] = normalized(doc[page_number - 1].get_text())
    missing_text = [work_id for work_id, page_number in mapped.items() if work_id not in text_by_page[page_number]]
    check("work IDs actually present on mapped pages", not missing_text, missing_text[:30])
    golden_failures = []
    for work_id, phrase in expectations.get("golden", {}).items():
        if work_id not in mapped or normalized(phrase) not in text_by_page.get(mapped.get(work_id, 0), ""):
            golden_failures.append({"id": work_id, "phrase": phrase, "page": mapped.get(work_id)})
    check("golden works present in final PDF", not golden_failures, golden_failures)

    log = (build_dir / "book.log").read_text(encoding="utf-8", errors="replace")
    fatal_patterns = [r"Missing character", r"Undefined control sequence", r"LaTeX Error", r"Fatal error", r"undefined references", r"Reference .* undefined", r"Duplicate label", r"unreferenced destination"]
    log_issues = [line for line in log.splitlines() if any(re.search(pattern, line) for pattern in fatal_patterns)]
    check("LaTeX log has no fatal or reference issues", not log_issues, log_issues[:30])
    overfull = [line for line in log.splitlines() if "Overfull" in line]
    underfull = [line for line in log.splitlines() if "Underfull" in line]
    check("no overfull boxes", not overfull, overfull[:20])

    fonts = {}
    for page_number in range(len(doc)):
        for record in doc.get_page_fonts(page_number):
            fonts[record[0]] = record
    font_details = []
    unembedded = []
    for xref, record in sorted(fonts.items()):
        name = record[3]
        try:
            extracted = doc.extract_font(xref)
            size = len(extracted[3]) if extracted and extracted[3] else 0
        except Exception:
            size = 0
        font_details.append({"xref": xref, "basefont": name, "embedded_bytes": size})
        if size == 0:
            unembedded.append(name)
    check("all PDF fonts embedded", not unembedded, unembedded)
    forbidden = [x["basefont"] for x in font_details if "lastresort" in x["basefont"].lower() or "unifont" in x["basefont"].lower()]
    check("no generic fallback fonts", not forbidden, forbidden)
    for family, usage in font_usage.items():
        if usage["count"]:
            expected = "BabelStoneHan" if family == "babeljfont" else "I.Ming"
            check(f"fallback font embedded {family}", any(expected in x["basefont"] for x in font_details), expected)

    out_of_bounds = []
    blank_pages = []
    for index, page in enumerate(doc):
        rect = page.rect
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    x0, y0, x1, y1 = span["bbox"]
                    if x0 < -1 or y0 < -1 or x1 > rect.width + 1 or y1 > rect.height + 1:
                        out_of_bounds.append({"page": index + 1, "text": span["text"][:30], "bbox": span["bbox"]})
        pixmap = page.get_pixmap(matrix=fitz.Matrix(0.22, 0.22), colorspace=fitz.csGRAY, alpha=False)
        image = Image.frombytes("L", (pixmap.width, pixmap.height), pixmap.samples)
        crop = image.crop((int(image.width * 0.16), int(image.height * 0.1), int(image.width * 0.84), int(image.height * 0.9)))
        dark_pixels = sum(1 for value in crop.getdata() if value < 200)
        text_content = re.sub(r"[0-9０-９〇]+", "", normalized(page.get_text()))
        if not text_content and dark_pixels < 10:
            blank_pages.append(index + 1)
    check("no text outside page bounds", not out_of_bounds, out_of_bounds[:20])
    check("no unexpected blank pages", not blank_pages, blank_pages[:30])

    sample_pages = sorted(set([1, len(doc)] + list(range(1, len(doc) + 1, max(1, len(doc) // 25)))))
    horizontal_failures = [page for page in sample_pages if not has_horizontal_text(doc[page - 1])]
    check("horizontal writing detected on sampled pages", not horizontal_failures, horizontal_failures)

    if expectations.get("required_phrases") or expectations.get("markdown_artifacts"):
        whole_text = normalized("".join(page.get_text() for page in doc))
        required_failures = [phrase for phrase in expectations.get("required_phrases", []) if normalized(phrase) not in whole_text]
        check("required article phrases present", not required_failures, required_failures)
        if expectations.get("markdown_artifacts"):
            artifacts = re.findall(r"\*\*|!\[|\]\(", whole_text)
            check("no Markdown syntax artifacts", not artifacts, artifacts[:10])
    image_pages = set()
    if expectations.get("expected_images") is not None:
        image_records = []
        ratio_failures = []
        image_bounds = []
        for page_index, page in enumerate(doc):
            for info in page.get_image_info(xrefs=True):
                image_records.append(info)
                image_pages.add(page_index + 1)
                x0, y0, x1, y1 = info["bbox"]
                if x0 < -1 or y0 < -1 or x1 > page.rect.width + 1 or y1 > page.rect.height + 1:
                    image_bounds.append({"page": page_index + 1, "bbox": info["bbox"]})
                displayed_ratio = (x1 - x0) / max(y1 - y0, 0.001)
                source_ratio = info["width"] / info["height"]
                if abs(displayed_ratio - source_ratio) / source_ratio > 0.02:
                    ratio_failures.append({"page": page_index + 1, "bbox": info["bbox"], "pixels": [info["width"], info["height"]]})
        expected_images = expectations["expected_images"]
        check("article images embedded", len(image_records) == expected_images and not image_bounds, {"expected": expected_images, "actual": len(image_records), "out_of_bounds": image_bounds[:10]})
        check("article image aspect ratios preserved", not ratio_failures, ratio_failures[:10])
    if expectations.get("expected_links"):
        uris = [link["uri"] for page in doc for link in page.get_links() if link.get("uri")]
        check("article hyperlinks preserved", len(uris) >= expectations["expected_links"] and all(uri.startswith(("https://", "http://")) for uri in uris), uris[:20])

    representative = {1, 2, 3, 4, len(doc)}
    representative.update(sorted(image_pages)[:3])
    for title in expectations.get("chapter_titles", []):
        needle = normalized(title)
        found = next((i + 1 for i in range(len(doc)) if needle in normalized(doc[i].get_text())), None)
        if found:
            representative.add(found)
    representative_ids = set(expectations.get("golden", {}))
    representative_ids.update(expectations.get(key) for key in ["longest_title_id", "longest_text_id"])
    representative_ids.discard(None)
    for work_id in representative_ids:
        if work_id in mapped:
            representative.add(mapped[work_id])
    representative = sorted(x for x in representative if 1 <= x <= len(doc))
    for page_number in representative:
        doc[page_number - 1].get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False).save(render_dir / f"page-{page_number:04d}.png")
    thumbnails = []
    for page_number in representative:
        image = Image.open(render_dir / f"page-{page_number:04d}.png").convert("RGB")
        image.thumbnail((300, 425))
        tile = Image.new("RGB", (320, 460), "white")
        tile.paste(image, ((320 - image.width) // 2, 24))
        ImageDraw.Draw(tile).text((8, 6), f"PDF p.{page_number}", fill="black")
        thumbnails.append(tile)
    columns = 4
    rows = (len(thumbnails) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 320, rows * 460), "white")
    for index, tile in enumerate(thumbnails):
        sheet.paste(tile, ((index % columns) * 320, (index // columns) * 460))
    sheet_path = render_dir / "contact-sheet.png" if args.render_dir else report_path.parent / "preview" / "contact-sheet.png"
    sheet_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(sheet_path)

    ghostscript = subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=nullpage", str(pdf_path)], capture_output=True, text=True, timeout=900)
    check("Ghostscript validates all pages", ghostscript.returncode == 0, (ghostscript.stdout + ghostscript.stderr)[-2000:])
    report = {
        "passed": all(x["passed"] for x in checks),
        "pdf": str(pdf_path),
        "theme": manifest.get("theme", "song-mist"),
        "input_sha256": manifest.get("input_sha256"),
        "pages": len(doc),
        "works": len(expected_ids),
        "checks": checks,
        "fonts": font_details,
        "overfull_warnings": len(overfull),
        "underfull_warnings": len(underfull),
        "blank_pages": blank_pages,
        "out_of_bounds": out_of_bounds,
        "horizontal_sample_pages": sample_pages,
        "representative_pages": representative,
        "contact_sheet": str(sheet_path),
        "ghostscript_returncode": ghostscript.returncode,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "checks": len(checks), "failed": sum(not x["passed"] for x in checks), "pages": len(doc), "works": len(expected_ids), "blank_pages": len(blank_pages), "out_of_bounds": len(out_of_bounds), "report": str(report_path)}, ensure_ascii=False))
    for item in checks:
        if not item["passed"]:
            print(f"FAIL {item['name']}: {item['detail']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
