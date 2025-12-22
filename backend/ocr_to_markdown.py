# backend/ocr_to_markdown.py
import base64
import os
from pathlib import Path
from typing import Dict, Any, List

import requests


API_URL = os.getenv("PADDLE_VL_API_URL", "https://h1t7y8r8wfu0c8g5.aistudio-app.com/layout-parsing")
TOKEN = os.getenv("PADDLE_VL_TOKEN", "55d7a3f98d5d8085b11cd80030b80adbaa1f3253")


class PaddleOCRVLClientError(Exception):
    """Error khusus untuk call PaddleOCR-VL API."""
    pass


def _ensure_config():
    if not API_URL:
        raise PaddleOCRVLClientError(
            "PADDLE_VL_API_URL belum di-set. "
            "Set dulu di environment variable."
        )
    if not TOKEN:
        raise PaddleOCRVLClientError(
            "PADDLE_VL_TOKEN belum di-set. "
            "Set dulu di environment variable / GitHub Secret."
        )


def _encode_file_to_base64(file_path: Path) -> str:
    file_bytes = file_path.read_bytes()
    return base64.b64encode(file_bytes).decode("ascii")


def call_paddle_vl_api(file_path: Path, file_type: int = 0) -> Dict[str, Any]:
    """
    Call PaddleOCR-VL layout API.
    - file_type: 0 = PDF, 1 = image.
    Return: result dict dari response.json()["result"]
    """
    _ensure_config()

    file_data = _encode_file_to_base64(file_path)

    headers = {
        "Authorization": f"token {TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "file": file_data,
        "fileType": file_type,
        "useDocOrientationClassify": False,
        "useDocUnwarping": False,
        "useChartRecognition": False,
    }

    resp = requests.post(API_URL, json=payload, headers=headers, timeout=300)
    if resp.status_code != 200:
        raise PaddleOCRVLClientError(
            f"Request gagal. Status: {resp.status_code}, body: {resp.text[:500]}"
        )

    data = resp.json()
    if "result" not in data:
        raise PaddleOCRVLClientError(
            f"Tidak menemukan key 'result' di response: {list(data.keys())}"
        )

    return data["result"]


def merge_markdown_from_layout_results(result: Dict[str, Any]) -> str:
    """
    Gabungkan semua `markdown["text"]` dari layoutParsingResults menjadi satu Markdown.
    """
    layout_results: List[Dict[str, Any]] = result.get("layoutParsingResults", [])
    if not layout_results:
        raise PaddleOCRVLClientError("layoutParsingResults kosong di result PaddleOCR-VL.")

    md_parts: List[str] = ["# Extracted Syllabus (PaddleOCR-VL)\n"]

    for i, res in enumerate(layout_results):
        md = res.get("markdown", {})
        text = md.get("text", "")
        if not text:
            # kalau kosong, skip
            continue

        # Tambahkan heading per dokumen jika mau
        md_parts.append(f"\n\n## Document {i + 1}\n")
        md_parts.append(text)

    return "\n".join(md_parts)


def extract_markdown_from_pdf(pdf_path: str) -> str:
    """
    Fungsi utama yang dipakai pipeline:
    - Input: path ke PDF
    - Output: 1 string Markdown gabungan dari seluruh layoutParsingResults
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF tidak ditemukan: {path}")

    # fileType = 0 → sesuai sample: untuk PDF
    result = call_paddle_vl_api(path, file_type=0)
    markdown = merge_markdown_from_layout_results(result)
    return markdown


def debug_save_markdown_and_images(result: Dict[str, Any], output_dir: Path) -> None:

    output_dir.mkdir(parents=True, exist_ok=True)

    for i, res in enumerate(result.get("layoutParsingResults", [])):
        md_filename = output_dir / f"doc_{i}.md"
        md = res.get("markdown", {})
        text = md.get("text", "")
        md_filename.write_text(text, encoding="utf-8")
        print(f"Markdown document saved at {md_filename}")

        # Simpan images di markdown["images"]
        for img_path, img_url in md.get("images", {}).items():
            full_img_path = output_dir / img_path
            full_img_path.parent.mkdir(parents=True, exist_ok=True)
            img_bytes = requests.get(img_url, timeout=60).content
            full_img_path.write_bytes(img_bytes)
            print(f"Image saved to: {full_img_path}")

        # Simpan outputImages
        for img_name, img_url in res.get("outputImages", {}).items():
            img_response = requests.get(img_url, timeout=60)
            if img_response.status_code == 200:
                filename = output_dir / f"{img_name}_{i}.jpg"
                filename.write_bytes(img_response.content)
                print(f"Image saved to: {filename}")
            else:
                print(f"Failed to download image, status code: {img_response.status_code}")

