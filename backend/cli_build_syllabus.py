# backend/cli_build_syllabus.py
import argparse
from pathlib import Path

from backend.ocr_to_markdown import extract_markdown_from_pdf
from backend.ernie_client import markdown_to_syllabus_html
from backend.build_site import build_site


def main():
    parser = argparse.ArgumentParser(
        description="Build a static course syllabus website from a PDF (PaddleOCR-VL -> ERNIE -> HTML -> site/)."
    )
    parser.add_argument(
        "--pdf",
        required=True,
        help="Path to the input PDF file, e.g. input/syllabus.pdf",
    )
    parser.add_argument(
        "--title",
        default="Course Syllabus",
        help="Website title shown in the page header and <title> tag.",
    )
    parser.add_argument(
        "--out",
        default="site",
        help="Output directory for the static site (default: site).",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # 1) PDF -> Markdown (PaddleOCR-VL API)
    print(f"[1/3] Extracting Markdown from PDF via PaddleOCR-VL API: {pdf_path}")
    md_text = extract_markdown_from_pdf(str(pdf_path))

    # 2) Markdown -> HTML (ERNIE)
    print("[2/3] Generating semantic HTML via ERNIE...")
    html_body = markdown_to_syllabus_html(md_text)

    # 3) HTML -> Static site files (site/index.html + assets/style.css)
    print(f"[3/3] Building static site into: {args.out}")
    index_path = build_site(html_body=html_body, title=args.title, out_dir=args.out)

    print("\n✅ Done!")
    print(f"Main page: {index_path}")
    print("Open it in a browser (local):")
    print(f"  - Linux:   xdg-open {index_path}")
    print(f"  - macOS:   open {index_path}")
    print(f"  - Windows: start {index_path}")


if __name__ == "__main__":
    main()
