# backend/main.py
from pathlib import Path
import tempfile

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from .ocr_to_markdown import extract_markdown_from_pdf
from .ernie_client import markdown_to_syllabus_html
from .build_site import build_site

app = FastAPI(title="PDF Syllabus → Web Builder")


@app.post("/build-syllabus")
async def build_syllabus(
    pdf: UploadFile = File(...),
    course_title: str = Form("My Course Syllabus"),
):
    # 1. Simpan PDF sementara
    suffix = Path(pdf.filename).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await pdf.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # 2. PDF → Markdown (PaddleOCR)
        md_text = extract_markdown_from_pdf(str(tmp_path))

        # 3. Markdown → HTML (ERNIE)
        html_body = markdown_to_syllabus_html(md_text)

        # 4. Bangun site statik (index.html + style.css)
        index_path = build_site(html_body, title=course_title)

        # 5. Response
        return FileResponse(
            index_path,
            media_type="text/html",
            filename="index.html",
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
