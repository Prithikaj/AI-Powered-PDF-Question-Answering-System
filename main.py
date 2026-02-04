from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import io
import pdfplumber
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DB_PATH = "data.db"
os.makedirs("uploads", exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -------------------- Database --------------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            content TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_document(filename, content):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (filename, content, created_at) VALUES (?, ?, ?)",
        (filename, content, datetime.utcnow().isoformat()),
    )
    doc_id = cur.lastrowid
    conn.commit()
    conn.close()
    return doc_id


def get_document(doc_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, filename, content, created_at FROM documents WHERE id = ?",
        (doc_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row

# -------------------- Chunking + Retrieval --------------------

def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + chunk_size])
        i += chunk_size - overlap
    return chunks


def retrieve_relevant_chunks(text, question, top_k=3):
    chunks = chunk_text(text)
    if not chunks:
        return []

    vectorizer = TfidfVectorizer().fit(chunks + [question])
    chunk_vecs = vectorizer.transform(chunks)
    q_vec = vectorizer.transform([question])

    sims = (chunk_vecs @ q_vec.T).toarray().ravel()
    idx = np.argsort(sims)[::-1][:top_k]

    return [chunks[i] for i in idx if sims[i] > 0]

# -------------------- Gemini 1.5 Flash (CORRECT API) --------------------

def call_gemini(prompt):
    if not GEMINI_API_KEY:
        return "ERROR: GEMINI_API_KEY not set"

    url = (
        "https://generativelanguage.googleapis.com/v1/"
        "models/gemini-2.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"ERROR calling Gemini 1.5 Flash: {e}"

# -------------------- App Events --------------------

@app.on_event("startup")
def startup_event():
    init_db()

# -------------------- Routes --------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    path = os.path.join("uploads", file.filename)

    with open(path, "wb") as f:
        f.write(content)

    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            full_text = "\n\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception as e:
        return JSONResponse({"error": f"PDF extraction failed: {e}"}, status_code=400)

    doc_id = save_document(file.filename, full_text)
    return {"doc_id": doc_id, "filename": file.filename}


@app.post("/ask")
async def ask(doc_id: int = Form(...), question: str = Form(...)):
    row = get_document(doc_id)
    if not row:
        return JSONResponse({"error": "Document not found"}, status_code=404)

    _, filename, content, _ = row
    chunks = retrieve_relevant_chunks(content, question, top_k=4)

    if chunks:
        context = "\n\n---\n\n".join(chunks)
        prompt = (
            "You are a helpful assistant answering questions using only the provided document content.\n"
            f"(From document: {filename})\n\n"
            f"{context}\n\n"
            f"Question: {question}\n\nAnswer:"
        )
    else:
        prompt = (
            "Not found in documents; general answer below.\n\n"
            f"Question: {question}\n\nAnswer:"
        )

    response = call_gemini(prompt)
    return {"response": response}
