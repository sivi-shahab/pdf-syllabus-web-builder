# backend/ernie_client.py
import os
from textwrap import dedent

from openai import OpenAI


# ===== Konfigurasi ERNIE lewat environment =====
# Set di environment / GitHub Secrets:
#   ERNIE_API_KEY      -> access token Baidu
#   ERNIE_BASE_URL     -> opsional, default ke aistudio
#   ERNIE_MODEL_NAME   -> opsional, default ernie-4.5-turbo-128k-preview

API_KEY = os.getenv("ERNIE_API_KEY", "55d7a3f98d5d8085b11cd80030b80adbaa1f3253")  # isi di env / secrets
BASE_URL = os.getenv("ERNIE_BASE_URL", "https://aistudio.baidu.com/llm/lmapi/v3")
MODEL_NAME = os.getenv("ERNIE_MODEL_NAME", "ernie-4.5-turbo-128k-preview")

if not API_KEY:
    # Biar error-nya jelas kalau lupa set token
    raise RuntimeError("ENV ERNIE_API_KEY belum di-set. Harus diisi access token Baidu.")


client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)


def call_ernie_api(prompt: str) -> str:
    """
    Panggil ERNIE dengan format OpenAI-style (non-streaming),
    lalu return isi HTML penuh sebagai string.
    """
    chat_completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        stream=False,  # backend enakan non-stream, biar langsung dapat 1 string
        extra_body={
            "penalty_score": 1,
        },
        max_completion_tokens=12000,
        temperature=0.3,
        top_p=0.8,
        frequency_penalty=0,
        presence_penalty=0,
    )

    # Ambil isi utama dari completion
    choice = chat_completion.choices[0]
    return choice.message.content


def markdown_to_syllabus_html(md_text: str) -> str:
    """
    Fungsi ini dipanggil dari:
    - FastAPI (main.py)
    - CLI (cli_build_syllabus.py)

    Tugasnya:
    - Susun prompt bahasa Inggris untuk generate halaman web
    - Kirim ke ERNIE
    - Kembalikan HTML body (tanpa <html>, <head>, <body>)
    """
    prompt = dedent(
    f"""
    You are an expert course-website generator specializing in creating academic course pages in the style of Stanford CS229/CS231n.

    I will give you a course syllabus in Markdown. Transform it into clean, semantic HTML suitable for a single-page course website that closely matches the structure and style of Stanford CS229 (https://cs229.stanford.edu/).

    CRITICAL REQUIREMENTS:

    1. OUTPUT ONLY PURE HTML: Do NOT include <html>, <head>, <body> tags, or any CSS/JavaScript.
    2. STRUCTURE THE PAGE EXACTLY LIKE CS229:
       - Top-level header with course title and Stanford-style header
       - "Time and Location" section (as an <h2> with detailed info in paragraphs)
       - "Course Description" section (<h2>)
       - "Prerequisites" section (<h2>, if present in syllabus)
       - "Course Materials" section (<h2>, if mentioned)
       - "Course Announcements" section (<h2>)
       - "Schedule" section (<h2>) - THIS IS CRUCIAL:
         * Create a clean, well-structured HTML table with columns: Week, Date, Topics, Readings, Assignments
         * Use <thead> for column headers
         * Ensure all schedule data is properly tabularized
         * Include exam dates if mentioned
       - "Grading" section (<h2>) with breakdown in table or detailed list
       - "Policies" section (<h2>) with subsections for academic integrity, collaboration, etc.
       - "Staff" section (<h2>) if instructors/TAs are mentioned
       - "FAQs" section (<h2>) if Q&A content exists

    3. STYLING APPROACH (using semantic HTML only):
       - Use proper heading hierarchy: <h1> for course title, <h2> for main sections, <h3> for subsections
       - For the main header: <h1>Course Title</h1> followed by <p>Stanford University</p>
       - Use <table class="schedule"> for schedule (CS229 uses tables extensively)
       - Use <div class="section"> containers for major sections
       - Important dates/deadlines should be in <strong> tags
       - Links should use <a href="..."> with proper targets
       - Lists should be properly nested <ul>/<ol> with <li> items
       - Code references in <code> tags

    4. CONTENT PRESERVATION RULES:
       - Preserve ALL original information: dates, percentages, readings, assignments
       - Convert markdown links to HTML links
       - Convert markdown tables to HTML tables
       - Convert markdown code blocks to <pre><code>...</code></pre>
       - Keep all policy details verbatim
       - Maintain week-by-week structure exactly as in syllabus

    5. FORMATTING SPECIFICS:
       - Dates should be in format: "Mon, Month DD" (e.g., "Mon, Sep 23")
       - Percentages in grading should be clearly shown
       - Readings should include full citations with links when available
       - Assignment due dates should be prominent
       - Office hours should be in a clear list format

    6. DO NOT:
       - Invent content not in the syllabus
       - Add inline CSS styles
       - Use <style> or <script> tags
       - Include any explanatory text outside HTML
       - Use deprecated HTML tags
       - Omit any syllabus information

    7. FINAL OUTPUT:
       - Only valid HTML code
       - No markdown remnants
       - No comments <!-- like this -->
       - Ready to be embedded in a CS229-style template
       - Properly indented for readability

    Target visual style reference: https://cs229.stanford.edu/
    - Clean, academic, professional appearance
    - Ample white space between sections
    - Clear visual hierarchy
    - Readable typography through semantic structure

    Here is the syllabus in Markdown:

    ```markdown
    {md_text}
    ```

    Generate the HTML now:
    """
).strip()

    html_body = call_ernie_api(prompt)
    return html_body
