import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from tempfile import NamedTemporaryFile
from typing import List
from dotenv import load_dotenv
load_dotenv()
import os
print("🔍 OPENAI_API_KEY loaded:", bool(os.getenv("OPENAI_API_KEY")))


from parsers import read_text
from extractor import extract_keywords   # keep this for jd_skills/keywords seed
from tailoring import build_tailored_model
from pdf_builder import build_pdf

app = FastAPI(title="ATS Resume Tailor API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def _read_seed(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]

@app.post("/api/tailor")
async def tailor_resume(jd: UploadFile = File(...), resume: UploadFile = File(...)):
    jd_bytes = await jd.read()
    res_bytes = await resume.read()

    _, jd_text = read_text(jd.filename, jd_bytes)
    _, res_text = read_text(resume.filename, res_bytes)

    if not jd_text.strip():
        raise HTTPException(400, "Could not parse JD text")
    if not res_text.strip():
        raise HTTPException(400, "Could not parse resume text")

    # keep extractor for a good seed set into LLM + verification
    skills_seed = _read_seed(os.path.join(os.path.dirname(__file__), "skills_seed.txt"))
    info = extract_keywords(jd_text, skills_seed, k=25)   # {'skills': [...], 'keywords': [...]}

    model = build_tailored_model(res_text, info["skills"], info["keywords"], jd_text)

    tmp = NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    build_pdf(model, tmp.name)
    f = open(tmp.name, "rb")
    return StreamingResponse(
        f,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=tailored_resume.pdf"}
    )
@app.post("/api/preview")
async def preview_resume(jd: UploadFile = File(...), resume: UploadFile = File(...)):
    jd_bytes = await jd.read()
    res_bytes = await resume.read()

    _, jd_text = read_text(jd.filename, jd_bytes)
    _, res_text = read_text(resume.filename, res_bytes)

    if not jd_text.strip() or not res_text.strip():
        raise HTTPException(400, "Invalid or empty file content")

    skills_seed = _read_seed(os.path.join(os.path.dirname(__file__), "skills_seed.txt"))
    info = extract_keywords(jd_text, skills_seed, k=25)
    model = build_tailored_model(res_text, info["skills"], info["keywords"], jd_text)

    # Return JSON model for preview
    return model

