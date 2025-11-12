import re, os
from typing import Dict, List, Any, Tuple
from openai import OpenAI
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer

# ─────────────────────────────────────────────────────────────────────────────
# OpenAI client
# ─────────────────────────────────────────────────────────────────────────────
client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────────────────────────────────────────────────────────────────────────
# JD term extraction + domain detection
# ─────────────────────────────────────────────────────────────────────────────
def extract_jd_terms(jd_text: str, top_n: int = 100) -> List[str]:
    jd = (jd_text or "").lower()
    if not jd.strip():
        return []
    vect = CountVectorizer(stop_words="english", ngram_range=(1, 2))
    X = vect.fit_transform([jd])
    terms = vect.get_feature_names_out()
    freq = Counter(dict(zip(terms, X.toarray()[0])))
    return [t for t, _ in freq.most_common(top_n)]

def detect_domain(jd_text: str) -> str:
    t = (jd_text or "").lower()
    tech = any(w in t for w in ["api", "software", "backend", "frontend", "react", "node", "database",
                                "devops", "distributed systems", "design patterns", "cloud"])
    healthcare = any(w in t for w in ["patient", "clinical", "healthcare", "hipaa", "medical", "device"])
    business = any(w in t for w in ["stakeholder", "marketing", "campaign", "sales", "kpi", "roi", "product manager"])
    research = any(w in t for w in ["research", "experiment", "publication", "analysis", "hypothesis"])
    if tech: return "tech"
    if healthcare: return "healthcare"
    if business: return "business"
    if research: return "research"
    return "general"

def extract_critical_terms(jd_text: str) -> List[str]:
    text = (jd_text or "").lower()
    candidates = [
        "software engineering", "design patterns", "distributed systems", "qa",
        "automation", "secure", "security", "enterprise systems", "user flows",
        "programming languages", "code review", "branch management", "knowledge base",
        "cloud", "infrastructure", "compliance", "scalable", "reliable", "documentation"
    ]
    out = [c for c in candidates if c in text]
    return list(dict.fromkeys(out))

# ─────────────────────────────────────────────────────────────────────────────
# Regex + helpers
# ─────────────────────────────────────────────────────────────────────────────
DATE_RX = re.compile(
    r"(?i)\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}\s*(?:–|-|to)?\s*(?:present|\d{4})?\b|(?:\b\d{4}\b)\s*(?:–|-|to)\s*(?:present|\b\d{4}\b)"
)
BULLET_MARK = re.compile(r"^\s*[•\-–]\s+")

def _lines(text: str) -> List[str]:
    return [ln.rstrip() for ln in (text or "").splitlines()]

def _canon_map() -> Dict[str, List[str]]:
    return {
        "experience": ["experience", "work experience", "employment", "professional experience", "work history"],
        "projects":   ["projects", "selected projects", "notable projects"],
        "skills":     ["skills", "technical skills", "tooling"],
        "education":  ["education", "academics"],
        "summary":    ["summary", "objective", "profile"],
    }

# ─────────────────────────────────────────────────────────────────────────────
# Section normalization
# ─────────────────────────────────────────────────────────────────────────────
def normalize_sections(text: str) -> Dict[str, List[str]]:
    lines = [ln for ln in _lines(text) if ln.strip()]
    sections: Dict[str, List[str]] = {}
    current = "misc"
    for ln in lines:
        # treat as a header only if it looks like a short title and is not a bullet
        if (not BULLET_MARK.match(ln)
            and re.match(r"^[A-Z][A-Za-z &/\-]{2,}$", ln.strip())
            and len(ln.split()) <= 6):
            current = ln.lower().strip()
            sections[current] = []
        else:
            sections.setdefault(current, []).append(ln)
    canon = {k: [] for k in _canon_map().keys()}
    for raw, ls in sections.items():
        for ck, aliases in _canon_map().items():
            if raw == ck or any(a in raw for a in aliases):
                canon[ck].extend(ls)
                break
    return {k: [x for x in v if x.strip()] for k, v in canon.items() if v}

# ─────────────────────────────────────────────────────────────────────────────
# Fold wrapped bullets into single items
# ─────────────────────────────────────────────────────────────────────────────
def fold_wrapped_bullets(lines: List[str]) -> List[str]:
    out: List[str] = []
    for ln in lines:
        if BULLET_MARK.match(ln):
            out.append(BULLET_MARK.sub("", ln).strip())
        else:
            if not out:
                out.append(ln.strip())
            else:
                out[-1] = (out[-1].rstrip() + " " + ln.strip()).strip()
    return [b for b in out if b]

# ─────────────────────────────────────────────────────────────────────────────
# Entry parsing (Experience / Projects)
# ─────────────────────────────────────────────────────────────────────────────
def parse_entries(section_lines: List[str]) -> List[Dict[str, Any]]:
    lines = [ln.strip() for ln in section_lines if ln.strip()]
    entries: List[Dict[str, Any]] = []
    cur = None

    def push():
        nonlocal cur
        if cur:
            cur["bullets"] = [b for b in fold_wrapped_bullets(cur["bullets"]) if len(b.split()) > 2]
            if cur["header"] or cur["bullets"]:
                entries.append(cur)
        cur = None

    def title_case_ratio(s: str) -> float:
        toks = [t for t in re.split(r"\s+", s) if t]
        if not toks: return 0.0
        titled = sum(1 for t in toks if (t[0].isupper() and any(ch.islower() for ch in t[1:])))
        return titled / len(toks)

    def is_headerish(s: str) -> bool:
        if BULLET_MARK.match(s): return False
        if s.strip().lower().startswith(("github:", "link:", "demo:", "repo:", "website:")): return False
        has_sep = any(sym in s for sym in [" — ", " - ", " | ", ":", " · "])
        looks_titley = (title_case_ratio(s) >= 0.5 and len(s) <= 120)
        ends_sentence = s.strip().endswith((".", "!", "?"))
        return (has_sep or looks_titley) and not ends_sentence

    i = 0
    while i < len(lines):
        ln = lines[i]
        if is_headerish(ln):
            push()
            cur = {"header": ln.strip(), "dates": "", "bullets": []}
            m = DATE_RX.search(ln)
            if m:
                cur["dates"] = m.group(0)
                cur["header"] = ln.replace(m.group(0), "").strip()
            elif i + 1 < len(lines) and DATE_RX.search(lines[i + 1] or ""):
                cur["dates"] = DATE_RX.search(lines[i + 1]).group(0)
                i += 1
            # keep immediate repo/link line as the first bullet
            if i + 1 < len(lines) and lines[i + 1].strip().lower().startswith(("github:", "link:", "demo:", "repo:", "website:")):
                cur["bullets"].append(lines[i + 1].strip())
                i += 1
        else:
            if not cur:
                cur = {"header": "", "dates": "", "bullets": []}
            cur["bullets"].append(ln)
        i += 1
    push()
    return entries

# ─────────────────────────────────────────────────────────────────────────────
# Keyword coverage utilities
# ─────────────────────────────────────────────────────────────────────────────
def _coverage(text: str, terms: List[str]) -> float:
    if not terms: return 1.0
    low = text.lower()
    uniq = [t.lower() for t in dict.fromkeys(terms)]
    found = sum(1 for t in uniq if t in low)
    return found / max(1, len(uniq))

# ─────────────────────────────────────────────────────────────────────────────
# LLM rewriting (Experience & Projects)
# ─────────────────────────────────────────────────────────────────────────────
def domain_prompt_hint(domain: str) -> str:
    return {
        "tech": "Emphasize scalability, security, design patterns, distributed systems, code quality, and collaboration with QA.",
        "business": "Emphasize stakeholder communication, measurable outcomes, process improvements, and cross-functional collaboration.",
        "healthcare": "Emphasize compliance, patient/user outcomes, data privacy/security, and interdisciplinary collaboration.",
        "research": "Emphasize experimental design, analysis, reproducibility, and insightful results.",
        "general": "Emphasize reliability, teamwork, initiative, and measurable impact.",
    }.get(domain, "Emphasize reliability, teamwork, initiative, and measurable impact.")

def llm_rewrite_bullets(section: str, bullets: List[str], jd_text: str,
                        all_terms: List[str], critical_terms: List[str], domain: str) -> List[str]:
    if not client or not bullets:
        return bullets

    hint = domain_prompt_hint(domain)
    base = f"""
Rewrite the following {section} bullet points for an ATS-optimized, HUMAN-readable resume.

Rules:
- Keep every fact true; do NOT invent roles or numbers.
- Start with strong action verbs; keep each bullet ≤ 26–28 words.
- Weave job-description keywords NATURALLY (no parentheses or keyword dumps). Use them inline (e.g., “applied design patterns in a Python service to improve reliability”).
- {hint}
Return each bullet on its own line beginning with "- ".

Job Description:
{jd_text}

Critical keywords to include when relevant: {", ".join(critical_terms[:14])}
Additional keywords to consider: {", ".join(all_terms[:40])}

Original bullets:
{chr(10).join(f"- {b}" for b in bullets)}
"""
    def _rewrite(prompt: str) -> List[str]:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.25,
            max_tokens=900,
        )
        text = res.choices[0].message.content.strip()
        return [re.sub(r"^[\-•]\s*", "", ln).strip() for ln in text.splitlines() if len(ln.strip()) > 4]

    out = _rewrite(base)
    joined = " ".join(out)
    if _coverage(joined, all_terms) < 0.85 or _coverage(joined, critical_terms) < 0.7:
        retry = base + "\n\nCoverage was low. Re-inject missing relevant terms organically while keeping clarity and truth. Avoid repetitive phrasing."
        out = _rewrite(retry)

    return out or bullets

# ─────────────────────────────────────────────────────────────────────────────
# Summary (third-person; forced opener)
# ─────────────────────────────────────────────────────────────────────────────
def llm_summary(jd_text: str, terms: List[str], domain: str) -> str:
    opener = "Highly motivated CS candidate"
    if not client:
        return f"{opener} with hands-on experience and interest in {domain} problems; collaborates well across teams and focuses on scalable, reliable results."
    prompt = f"""
Write a concise, 2-sentence, third-person summary that STARTS with "{opener} with".
Make it natural and recruiter-friendly (not keyword-stuffed). Blend several relevant JD terms.

Domain emphasis: {domain_prompt_hint(domain)}

JD terms: {", ".join(terms[:20])}

Job Description:
{jd_text}
"""
    try:
        r = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=120,
        )
        txt = r.choices[0].message.content.strip()
        if not txt.lower().startswith(opener.lower()):
            txt = f"{opener} with " + txt[0].lower() + txt[1:]
        return txt
    except Exception:
        return f"{opener} with hands-on experience and interest in {domain} problems; collaborates well across teams and focuses on scalable, reliable results."

# ─────────────────────────────────────────────────────────────────────────────
# Skills cleanup + grouping
# ─────────────────────────────────────────────────────────────────────────────
LABEL_RX = re.compile(r"(?i)\b(programming|languages?|frameworks?|libraries?|tooling|tools|ai|ml|data|devops)\s*:\s*")
BAD = {"labeling","logging","experience","engineering","systems","pipelines","ability","applied","application"}

LANGS = {"python","java","c","c++","c#","go","golang","typescript","javascript","js","sql","r","matlab","swift","kotlin","scala","rust"}
FRAME_LIB = {"react","node","flask","django","fastapi","spring","express","streamlit","pytorch","tensorflow","keras","sklearn","pandas","numpy","matplotlib","seaborn"}
DATA_CLOUD = {"aws","gcp","azure","firebase","mongodb","postgres","mysql","snowflake","bigquery","spark","hadoop","airflow","kafka","docker","kubernetes","redis"}
DEVOPS = {"git","github","gitlab","ci","cd","ci/cd","terraform","ansible","jenkins","sentry","datadog","grafana","prometheus"}
DESIGN_TOOLS = {"figma","jira","confluence","notion","excel","tableau","powerbi","photoshop","illustrator"}
SOFT = {"leadership","collaboration","communication","problem-solving","teamwork","adaptability","time management","stakeholder management","customer focus"}

def tokenize_skills(sk_lines: List[str]) -> List[str]:
    text = " | ".join(sk_lines)
    text = LABEL_RX.sub("", text)
    toks = re.split(r"[,\|\n;]+", text)
    toks = [t.strip() for t in toks if t.strip()]
    expanded: List[str] = []
    for t in toks:
        if "(" in t and ")" in t:
            head = t.split("(")[0].strip()
            subs = t[t.find("(")+1:t.rfind(")")].split(",")
            expanded.append(head)
            expanded.extend(s.strip() for s in subs if s.strip())
        else:
            expanded.append(t)
    # normalize
    out = []
    for x in expanded:
        xl = x.lower()
        if xl in BAD or len(xl) > 40: continue
        out.append(x.strip())
    # dedupe keep order
    return list(dict.fromkeys(out))

def categorize_skills(raw: List[str], jd_terms: List[str]) -> Tuple[List[str], Dict[str, List[str]]]:
    # booster: add clean JD tokens if they look like skills/phrases
    for k in jd_terms:
        k = k.strip()
        if 2 <= len(k) <= 24 and re.match(r"^[A-Za-z0-9#.+\- ]+$", k):
            if k.lower() not in [s.lower() for s in raw]:
                raw.append(k)

    cats = {
        "Languages": [],
        "Frameworks & Libraries": [],
        "Data & Cloud": [],
        "DevOps": [],
        "Design & Tools": [],
        "Soft Skills": [],
        "Other": [],
    }
    for s in raw:
        sl = s.lower()
        if sl in LANGS: cats["Languages"].append(s)
        elif sl in FRAME_LIB: cats["Frameworks & Libraries"].append(s)
        elif sl in DATA_CLOUD: cats["Data & Cloud"].append(s)
        elif sl in DEVOPS: cats["DevOps"].append(s)
        elif sl in DESIGN_TOOLS: cats["Design & Tools"].append(s)
        elif sl in SOFT: cats["Soft Skills"].append(s.title())
        else: cats["Other"].append(s)

    # tidy: dedupe + cap each bucket
    grouped = {k: list(dict.fromkeys(v))[:10] for k, v in cats.items() if v}
    # flat list for preview
    flat = []
    for k in ["Languages","Frameworks & Libraries","Data & Cloud","DevOps","Design & Tools","Soft Skills","Other"]:
        if k in grouped:
            flat.extend(grouped[k])
    flat = list(dict.fromkeys(flat))[:30]
    return flat, grouped

# ─────────────────────────────────────────────────────────────────────────────
# Bullets trimming (never drop entries/projects)
# ─────────────────────────────────────────────────────────────────────────────
def trim_bullets_only(entries: List[Dict[str, Any]], max_bullets: int) -> List[Dict[str, Any]]:
    out = []
    for e in entries:
        out.append({
            "header": e.get("header","").strip(),
            "dates":  e.get("dates","").strip(),
            "bullets": (e.get("bullets") or [])[:max_bullets]
        })
    return out

# ─────────────────────────────────────────────────────────────────────────────
# Public: build final resume model
# ─────────────────────────────────────────────────────────────────────────────
def build_tailored_model(resume_text: str, jd_skills: List[str], jd_keywords: List[str], jd_text: str = "") -> Dict[str, Any]:
    print("\n🧠 Starting build_tailored_model — invoking LLM tailoring...")

    secs = normalize_sections(resume_text)
    lines = [ln.strip() for ln in _lines(resume_text) if ln.strip()]

    name = lines[0] if lines else "Your Name"
    contact = lines[1] if len(lines) > 1 else "email@example.com | (000) 000-0000 | City, ST"

    domain = detect_domain(jd_text)
    auto_terms = extract_jd_terms(jd_text, top_n=100)
    critical = extract_critical_terms(jd_text)
    all_terms = list(dict.fromkeys((jd_skills or []) + (jd_keywords or []) + auto_terms + critical))[:120]

    # Skills → tokens → grouped
    raw_skill_tokens = tokenize_skills(secs.get("skills", []))
    flat_skills, grouped_skills = categorize_skills(raw_skill_tokens, all_terms)

    # Experience / Projects parse
    exp_entries = parse_entries(secs.get("experience", []))
    proj_entries = parse_entries(secs.get("projects", []))

    # LLM rewrite with JD coverage
    for e in exp_entries:
        e["bullets"] = llm_rewrite_bullets("Work Experience", e.get("bullets", []), jd_text, all_terms, critical, domain)
    for p in proj_entries:
        p["bullets"] = llm_rewrite_bullets("Projects", p.get("bullets", []), jd_text, all_terms, critical, domain)

    # Trim bullets only (keep ALL entries/projects)
    exp_entries = trim_bullets_only(exp_entries, max_bullets=5)
    proj_entries = trim_bullets_only(proj_entries, max_bullets=3)

    # Summary (third-person opener)
    summary = llm_summary(jd_text, all_terms, domain)

    education = secs.get("education", ["University, Degree — YYYY"])

    return {
        "name": name,
        "contact": contact,
        "summary": [summary],
        "skills": flat_skills,             # for existing preview UI
        "skills_grouped": grouped_skills,  # for nice PDF rendering with bold mini-headers
        "experience_entries": exp_entries,
        "project_entries": proj_entries,
        "education": education,
    }
