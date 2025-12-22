# backend/build_site.py
from pathlib import Path


TEMPLATE_PATH = Path(__file__).parent / "templates" / "base.html"
SITE_DIR = Path(__file__).parent.parent / "site"


def build_site(html_body: str, title: str = "Course Syllabus") -> Path:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    assets_dir = SITE_DIR / "assets"
    assets_dir.mkdir(exist_ok=True)

    # Baca template
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = template.replace("{{TITLE}}", title).replace("{{CONTENT}}", html_body)

    # Simpan index.html
    index_path = SITE_DIR / "index.html"
    index_path.write_text(rendered, encoding="utf-8")

    # CSS simple
    css_path = assets_dir / "style.css"
    if not css_path.exists():
        css_path.write_text(
            """
            body {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f5f7;
                color: #222;
            }
            header {
                background: #111827;
                color: white;
                padding: 24px;
            }
            header h1 { margin: 0; font-size: 1.8rem; }
            header p { margin: 4px 0 0; opacity: 0.8; }
            main {
                max-width: 960px;
                margin: 24px auto;
                background: white;
                padding: 24px 32px;
                border-radius: 16px;
                box-shadow: 0 18px 45px rgba(15,23,42,0.13);
            }
            h1, h2, h3 { color: #111827; }
            table { width: 100%; border-collapse: collapse; margin: 16px 0; }
            th, td { border: 1px solid #e5e7eb; padding: 8px 10px; font-size: 0.9rem; }
            th { background: #f9fafb; text-align: left; }
            code, pre { font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
            a { color: #2563eb; text-decoration: none; }
            a:hover { text-decoration: underline; }
            """.strip(),
            encoding="utf-8",
        )

    return index_path
