import os
import re
import fitz  # PyMuPDF
import docx
from flask import Flask, render_template, request
from markupsafe import Markup
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Max 5MB

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

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

        return render_template(
            'result.html',
            resume_text=highlighted_resume,
            job_description=highlighted_jd,
            match_percentage=match_percentage,
            missing_keywords=missing_keywords
        )

    return "File type not allowed. Please upload a PDF or DOCX.", 400

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

if __name__ == '__main__':
    app.run(debug=True)
