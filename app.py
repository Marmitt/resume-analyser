import os
from flask import Flask, render_template, request
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

        # Extract text from file (basic for now)
        text = extract_text(filepath)

        return render_template('result.html', resume_text=text)

    return "File type not allowed. Please upload a PDF or DOCX.", 400

def extract_text(filepath):
    if filepath.endswith('.pdf'):
        return extract_text_from_pdf(filepath)
    elif filepath.endswith('.docx'):
        return extract_text_from_docx(filepath)
    return "Unsupported file type"

# Basic placeholder functions
def extract_text_from_pdf(filepath):
    return "[PDF parsing not yet implemented]"

def extract_text_from_docx(filepath):
    return "[DOCX parsing not yet implemented]"

if __name__ == '__main__':
    app.run(debug=True)
