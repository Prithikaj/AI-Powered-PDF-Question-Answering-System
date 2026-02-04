<<<<<<< HEAD
# AI-Powered PDF Question Answering System

Quick prototype to upload PDFs, extract text, and ask questions referencing the PDF. Uses FastAPI backend and a minimal Awesome-UI frontend.

Prereqs
- Python 3.9+

Install

```bash
python -m pip install -r requirements.txt
```

Setup

1. Copy `.env.example` to `.env` and set `GEMINI_API_KEY`. The user-provided key can be set here as `GEMINI_API_KEY`.
2. Optionally set `GEMINI_API_URL` if you have a custom Gemini endpoint.

Run

```bash
uvicorn main:app --reload --port 8000
```

Open: http://localhost:8000

Notes
- The backend extracts text using `pdfplumber` and stores documents in a local SQLite DB.
- Retrieval is a simple TF-IDF over text chunks; the top chunks are sent to the LLM.
- The Gemini wrapper will try to call the URL in `GEMINI_API_URL` with a Bearer token; otherwise it falls back to a default Google PaLM endpoint requiring an API key.

Security
- Keep your API key secret. Do not commit `.env` to source control.
=======
# AI-Powered-PDF-Question-Answering-System
>>>>>>> 15e6d82abfd260b2fc518ec4041afb41c856bd39
