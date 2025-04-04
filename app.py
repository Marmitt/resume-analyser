import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import fitz
import docx
import re

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

        text = extract_text(filepath)  
        # Get job description from form
        job_description = request.form.get('job_description', '')
        # Analyze match
        match_percentage, missing_keywords = analyze_match(resume_text=text, job_description=job_description)

        return render_template(
            'result.html',
            resume_text=text,
            job_description=job_description,
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

# Extract text from PDF
def extract_text_from_pdf(filepath):
    try:
        text = ""
        pdf = fitz.open(filepath)
        for page in pdf:
            text += page.get_text()
        return text if text.strip() else "[No extractable text found in PDF]"
    except Exception as e:
        return f"[Error reading PDF: {e}]"

# Extract text from DOCX
def extract_text_from_docx(filepath):
    try:
        doc = docx.Document(filepath)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text if text.strip() else "[No extractable text found in DOCX]"
    except Exception as e:
        return f"[Error reading DOCX: {e}]"


def analyze_match(resume_text, job_description):
    # Normalize text
    resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
    jd_words = set(re.findall(r'\b\w+\b', job_description.lower()))

    # Consider only long-enough words
    jd_keywords = {word for word in jd_words if len(word) > 3}

    matched = resume_words.intersection(jd_keywords)
    match_percent = round((len(matched) / len(jd_keywords)) * 100, 2) if jd_keywords else 0

    missing = jd_keywords - resume_words
    return match_percent, sorted(missing)


if __name__ == '__main__':
    app.run(debug=True)
