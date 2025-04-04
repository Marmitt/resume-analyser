# 🧠 Resume Analyzer

A smart, AI-assisted web app that analyzes resumes against job descriptions and highlights strengths, weaknesses, and keyword matches.

Live Demo: https://resume-analyser-xkwb.onrender.com/

---

## 🚀 Features

- Upload your **PDF** or **DOCX** resume
- Paste a **job description**
- Get:
  - ✅ Match percentage
  - ✅ Highlighted keyword matches/missing
  - ✅ Top skills summary
  - ✅ Pie chart match heatmap
  - ✅ Smart section detection (Education, Skills, Experience...)
  - ✅ Resume improvement recommendations
  - ✅ Downloadable PDF report

---

## 🛠 Built With

- **Python** & **Flask**
- **Bootstrap 5** for UI
- **PyMuPDF** & **python-docx** for resume parsing
- **xhtml2pdf** for report generation
- **Chart.js** for visualizations
- **Render** for deployment

---

## 📁 How to Run Locally

```bash
git clone https://github.com/your-username/resume-analyzer.git
cd resume-analyzer
python -m venv venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
pip install -r requirements.txt
python app.py
