# ATS Resume Optimizer

A lightweight AI-powered tool that automatically tailors your resume to a specific job description.  
It reads your resume, analyzes the job posting, and rewrites your content to better match keywords — while keeping it natural and professional.

---

## Features

- Extracts text from PDF or DOCX resumes  
- Analyzes job descriptions for relevant skills & keywords  
- Uses the OpenAI API to rewrite and optimize resume content  
- Preserves human readability and structure  
- Exports a new, ready-to-download PDF resume  

---

## How It Works

1. **Upload your resume** (PDF or DOCX)  
2. **Upload a job description**  
3. The app compares both and rewrites your resume using GPT to highlight matching skills  
4. A polished PDF version is generated — recruiter- and ATS-friendly  

---

## Tech Stack

- **Backend:** FastAPI, Uvicorn  
- **AI Integration:** OpenAI GPT API  
- **Parsing:** Textract, PyMuPDF  
- **PDF Builder:** ReportLab  
- **Frontend (optional):** React / Vite  
- **Deployment:** Render or Railway  

---

## Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Simba4077/ats-resume-optimizer.git
cd ats-resume-optimizer/server
```
### 2. Create a VM (Optional)
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# or
source .venv/bin/activate  # Mac/Linux
```

### 3. Install Dependencies 
```bash
pip install -r requirements.txt
```
### 4. Add your OpenAI API key  
Create a .env file inside the server folder and add:  
```bash
OPENAI_API_KEY=your_openai_api_key_here
```
### 5. Run the backend  
```bash 
uvicorn main:app --reload --port 8000
```

### 6. Run the frontend 
```bash
cd ../client
npm install
npm run dev
```  

Then open the URL printed in your terminal (usually http://localhost:5173).  

---
## License  
This project is licensed under the MIT License.

---

## Notes
-- Works best with clearly formatted resumes  
-- Model automatically adapts tone and phrasing for the job role  
-- You can edit pdf_builder.py or tailoring.py to customize formatting or logic  