import os
import re
import fitz  # PyMuPDF
import docx
from flask import Flask, render_template, request, send_file
from markupsafe import Markup
from werkzeug.utils import secure_filename
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Max 5MB

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Store last analysis in memory (for now)
last_analysis = {}

# Define known skills for extraction
KNOWN_SKILLS = [
    'python', 'flask', 'django', 'html', 'css', 'javascript', 'sql',
    'mysql', 'postgresql', 'mongodb', 'git', 'github',
    'docker', 'linux', 'aws', 'azure', 'gcp',
    'react', 'vue', 'node', 'java', 'c#', 'c++',
    'communication', 'teamwork', 'leadership', 'problem-solving', 'adaptability',
    'critical thinking', 'time management', 'creativity'
]

@app.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d'):
    return datetime.now().strftime(format)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'resume' not in request.files:
        return "No file uploaded.", 400

    file = request.files['resume']
    if file.filename == '':
        return "No selected file.", 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extract text from file
        text = extract_text(filepath)

        # Analyze match
        job_description = request.form.get('job_description', '')
        match_percentage, missing_keywords, highlighted_resume, highlighted_jd = analyze_match(
            resume_text=text,
            job_description=job_description
        )

        # Extract top skills
        top_skills = extract_skills(text)

        # Detect resume sections
        sections_detected = detect_sections(text)

        # Generate smart recommendations
        recommendations = generate_recommendations(sections_detected, missing_keywords)

        # Save to memory for PDF generation
        last_analysis['resume_text'] = highlighted_resume
        last_analysis['job_description'] = highlighted_jd
        last_analysis['match_percentage'] = match_percentage
        last_analysis['missing_keywords'] = missing_keywords
        last_analysis['top_skills'] = top_skills
        last_analysis['sections'] = sections_detected
        last_analysis['recommendations'] = recommendations

        return render_template(
            'result.html',
            resume_text=highlighted_resume,
            job_description=highlighted_jd,
            match_percentage=match_percentage,
            missing_keywords=missing_keywords,
            top_skills=top_skills,
            sections=sections_detected,
            recommendations=recommendations
        )

    return "File type not allowed. Please upload a PDF or DOCX.", 400

@app.route('/download')
def download():
    rendered = render_template("export.html", **last_analysis)
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(rendered, dest=pdf)
    pdf.seek(0)
    return send_file(pdf, download_name="resume_analysis.pdf", as_attachment=True)

def extract_text(filepath):
    if filepath.endswith('.pdf'):
        return extract_text_from_pdf(filepath)
    elif filepath.endswith('.docx'):
        return extract_text_from_docx(filepath)
    return "Unsupported file type"

def extract_text_from_pdf(filepath):
    try:
        text = ""
        pdf = fitz.open(filepath)
        for page in pdf:
            text += page.get_text()
        return text if text.strip() else "[No extractable text found in PDF]"
    except Exception as e:
        return f"[Error reading PDF: {e}]"

def extract_text_from_docx(filepath):
    try:
        doc = docx.Document(filepath)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text if text.strip() else "[No extractable text found in DOCX]"
    except Exception as e:
        return f"[Error reading DOCX: {e}]"

def analyze_match(resume_text, job_description):
    resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
    jd_words = set(re.findall(r'\b\w+\b', job_description.lower()))
    jd_keywords = {word for word in jd_words if len(word) > 3}

    matched = resume_words.intersection(jd_keywords)
    missing = jd_keywords - resume_words

    resume_highlighted = highlight_keywords(resume_text, matched, "match")
    job_highlighted = highlight_keywords(job_description, matched, "match")
    job_highlighted = highlight_keywords(job_highlighted, missing, "missing")

    match_percent = round((len(matched) / len(jd_keywords)) * 100, 2) if jd_keywords else 0

    return match_percent, sorted(missing), Markup(resume_highlighted), Markup(job_highlighted)

def highlight_keywords(text, keywords, css_class):
    for word in sorted(keywords, key=len, reverse=True):
        regex = re.compile(rf'\b({re.escape(word)})\b', re.IGNORECASE)
        text = regex.sub(rf'<span class="{css_class}">\1</span>', text)
    return text

def extract_skills(resume_text):
    found_skills = []
    words = set(re.findall(r'\b\w+\b', resume_text.lower()))
    for skill in KNOWN_SKILLS:
        if skill.lower() in words:
            found_skills.append(skill)
    return sorted(found_skills)

def detect_sections(text):
    sections = {
        "Education": "",
        "Experience": "",
        "Skills": "",
        "Projects": "",
        "Certifications": ""
    }
    lines = text.splitlines()
    current_section = None
    for line in lines:
        clean = line.strip().lower()
        if "education" in clean:
            current_section = "Education"
        elif "experience" in clean or "work history" in clean:
            current_section = "Experience"
        elif "skill" in clean:
            current_section = "Skills"
        elif "project" in clean:
            current_section = "Projects"
        elif "certification" in clean:
            current_section = "Certifications"
        elif current_section and line.strip():
            sections[current_section] += line.strip() + "\n"
    return {k: v.strip() for k, v in sections.items() if v.strip()}

def generate_recommendations(sections, missing_keywords):
    tips = []
    important_sections = ["Education", "Experience", "Skills"]
    for section in important_sections:
        if section not in sections:
            tips.append(f"Consider adding a '{section}' section to your resume.")
    for section, content in sections.items():
        if len(content.split()) < 10:
            tips.append(f"The '{section}' section seems very short — consider adding more detail.")
    if missing_keywords:
        tips.append(f"You're missing {len(missing_keywords)} keywords from the job description. Consider integrating more relevant terms.")
    if not tips:
        tips.append("Nice work! Your resume looks well-structured and relevant to the job.")
    return tips

if __name__ == '__main__':
    app.run(debug=True)