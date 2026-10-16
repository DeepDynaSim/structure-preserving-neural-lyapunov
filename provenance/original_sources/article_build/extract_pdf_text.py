"""Extract page-delimited UTF-8 text from one or more PDFs for local analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader


def extract(pdf_path: Path, out_dir: Path) -> Path:
    reader = PdfReader(str(pdf_path))
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{pdf_path.stem}.txt"
    chunks: list[str] = []
    for page_index, page in enumerate(reader.pages, start=1):
        chunks.append(f"\n===== PAGE {page_index} / {len(reader.pages)} =====\n")
        chunks.append(page.extract_text() or "")
    output_path.write_text("\n".join(chunks), encoding="utf-8")
    print(f"{pdf_path} -> {output_path} ({len(reader.pages)} pages)")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdfs", nargs="+", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("article_build/extracted"))
    args = parser.parse_args()
    for pdf_path in args.pdfs:
        extract(pdf_path, args.out_dir)


if __name__ == "__main__":
    main()
