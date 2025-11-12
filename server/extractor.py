import re
from collections import Counter
from typing import List, Dict

# ---------------------------------------------------------------------
# Clean and tokenize text
# ---------------------------------------------------------------------
def _tokenize(text: str) -> List[str]:
    text = text.lower()
    # keep alphanumeric and + / . / #
    tokens = re.findall(r"[a-z0-9\+\-/\.#]+", text)
    return [t for t in tokens if len(t) > 2]

# ---------------------------------------------------------------------
# Extract skills and keywords from a job description
# ---------------------------------------------------------------------
def extract_keywords(jd_text: str, seed_skills: List[str] = None, k: int = 25) -> Dict[str, List[str]]:
    """
    Extracts the most frequent and relevant terms from a job description.
    Returns a dictionary:
      {
        "skills": [technical, domain terms],
        "keywords": [general action/soft-skill terms]
      }
    """
    jd_text = jd_text.lower()
    toks = _tokenize(jd_text)
    freq = Counter(toks)

    # --- Optional: seed boost for known skills list (e.g., from skills_seed.txt)
    if seed_skills:
        for s in seed_skills:
            if s.lower() in freq:
                freq[s.lower()] += 3

    # --- Compute top terms
    top_terms = [w for w, _ in freq.most_common(80)]

    # --- Split into likely technical vs general keywords
    technical_markers = [
        "python", "java", "c++", "javascript", "node", "react", "angular",
        "vue", "sql", "aws", "azure", "gcp", "docker", "kubernetes",
        "tensorflow", "pytorch", "ai", "ml", "machine", "learning",
        "deep", "neural", "api", "database", "security", "devops",
        "git", "linux", "unix", "testing", "automation", "distributed",
        "system", "architecture", "backend", "frontend", "fullstack"
    ]

    skills = []
    keywords = []

    for term in top_terms:
        # technical
        if any(t in term for t in technical_markers):
            skills.append(term)
        # skip stopwords
        elif term not in [
            "and", "for", "with", "the", "you", "our", "will", "this", "are",
            "have", "your", "that", "job", "description", "skills", "requirements"
        ]:
            keywords.append(term)

    # --- Limit size
    skills = list(dict.fromkeys(skills))[:k]
    keywords = list(dict.fromkeys(keywords))[:k]

    return {"skills": skills, "keywords": keywords}

# ---------------------------------------------------------------------
# Example (for debugging)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    sample_jd = """
    We’re hiring a Software Engineer intern with experience in Python,
    distributed systems, and AI/ML infrastructure. Knowledge of React
    and Node.js is preferred. You’ll collaborate with QA, security,
    and operations teams to build scalable automation pipelines.
    """
    print(extract_keywords(sample_jd))


import os
import textract
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from TXT, PDF, or DOCX file robustly.
    Returns a single plain-text string.
    """
    try:
        ext = os.path.splitext(file_path)[-1].lower()

        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif ext == ".pdf":
            text = ""
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text

        elif ext == ".docx":
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)

        else:
            # fallback for uncommon formats
            return textract.process(file_path).decode("utf-8", errors="ignore")

    except Exception as e:
        print(f"[ERROR] Failed to extract text from {file_path}: {e}")
        return ""
