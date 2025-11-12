# ATS Resume Optimizer

This project helps you automatically tailor your resume to a specific job description.  
It parses your resume, identifies key details from a job posting, and uses AI to rewrite and reformat your resume so it matches the role while still sounding natural.

---

## Features

- Extracts text from uploaded resumes (PDF or DOCX)
- Analyzes job descriptions for skills and keywords
- Uses the OpenAI API to rewrite and enhance the resume
- Keeps the formatting readable and professional
- Exports a new, ready-to-download PDF resume

---

## How It Works

1. Upload your resume file  
2. Paste in a job description  
3. The app compares both, rewrites the resume using GPT, and inserts relevant keywords naturally  
4. A new PDF is generated that’s easier for both recruiters and ATS systems to read

---

## Tech Stack

- **Backend:** FastAPI, Uvicorn  
- **AI:** OpenAI GPT API  
- **Parsing:** Textract, PyMuPDF  
- **PDF Generation:** ReportLab  
- **Frontend (optional):** HTML / React  
- **Deployment:** Render or Railway

---

## Setup (Local)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Simba4077/ats-resume-optimizer.git
   cd ats-resume-optimizer/server


Optional: create a virtual env  
python -m venv .venv
.venv\Scripts\activate   # Windows
# or
source .venv/bin/activate  # Mac/Linux


Install dependencies:  
`pip install -r requirements.txt  
`

Add your OpenAI key --> Create a .env file in the server folder and add:
`  

Run the server in one terminal:
`uvicorn main:app --reload --port 8000`  

Run the program in another terminal:    
Go to \client folder and run
`npm run dev`  
Follow the local host url 

