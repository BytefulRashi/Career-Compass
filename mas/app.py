from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
import os
import fitz
from dotenv import load_dotenv
from src.mas.crew import Mas
from src.mas.S3 import upload_files_to_s3
from ragS3 import RAGS3
import io
# import markdown

load_dotenv()

def generate_secret_key():
    return os.urandom(24).hex()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', generate_secret_key())

# Configure directories
CURRENT_DIR = Path(os.getcwd())
BASE_DIR = CURRENT_DIR / ""
TEXT_FILES_DIR = BASE_DIR / "processed_resume"
MD_FILES_DIR = BASE_DIR / "output"

# Create directories if they don't exist
TEXT_FILES_DIR.mkdir(parents=True, exist_ok=True)
MD_FILES_DIR.mkdir(parents=True, exist_ok=True)

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_pdf_to_text(pdf_file):
    """Convert PDF file to text using PyMuPDF."""
    try:
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_content = []
        
        for page in doc:
            text = page.get_text("text")
            if text.strip():
                text_content.append(text)
                
        doc.close()
        
        full_text = '\n\n'.join(text_content)
        if not full_text.strip():
            raise ValueError("No text could be extracted from the PDF")
            
        return full_text
        
    except Exception as e:
        raise Exception(f"Error converting PDF to text: {str(e)}")

def initialize_rag():
    """Initialize RAG system."""
    try:
        rag = RAGS3(
            bucket_name=os.environ.get("BUCKET_NAME"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
        return rag
    except Exception as e:
        raise Exception(f"Error initializing RAG system: {str(e)}")

@app.route('/')
def index():
    return render_template('base.html')  # Changed to use our new base.html template

@app.route('/submit_goal', methods=['POST'])
def submit_goal():
    career_goal = request.form.get('career_goal')
    if career_goal:
        session['career_goal'] = career_goal
        return jsonify({'success': True})
    return jsonify({'error': 'Career goal is required'}), 400

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if not session.get('career_goal'):
        return jsonify({'error': 'Please set career goal first'}), 400

    if file and allowed_file(file.filename):
        try:
            # Convert PDF to text
            resume_text = convert_pdf_to_text(file)
            
            # Save text content
            filename = secure_filename(file.filename)
            txt_path = TEXT_FILES_DIR / f"{filename[:-4]}.txt"
            with open(txt_path, "w", encoding='utf-8') as txt_file:
                txt_file.write(resume_text)

            # Prepare inputs for Mas
            inputs = {
                "resume": str(txt_path),
                "topic": session['career_goal']
            }

            # Process with Mas
            Mas().crew().kickoff(inputs=inputs)
            upload_files_to_s3('processed_resume', os.environ.get('BUCKET_NAME'))
            upload_files_to_s3('output', os.environ.get('BUCKET_NAME'))
            
            # Update session
            session['resume_txt_path'] = str(txt_path)
            session['processing_done'] = True
        
            return jsonify({'success': True, 'message': 'Resume processed successfully'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    if not session.get('processing_done'):
        return jsonify({'error': 'Please upload and process your resume first'}), 400
        
    try:
        question = request.json.get('question')
        if not question:
            return jsonify({'error': 'Question is required'}), 400
            
        chat_history = session.get('chat_history', [])
        
        rag = initialize_rag()
        response = rag.query(question, chat_history)
        
        # Update chat history
        chat_history.append({'role': 'user', 'content': question})
        chat_history.append({'role': 'assistant', 'content': response['answer']})
        session['chat_history'] = chat_history
        
        return jsonify({
            'answer': response['answer'],
            'chat_history': chat_history
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_analysis')
def get_analysis():
    """Get combined analysis from all markdown files."""
    if not session.get('processing_done'):
        return jsonify({'error': 'Please process resume first'}), 400
        
    try:
        combined_content = []
        md_files = [
            "Career Guidance.md",
            "Market Analysis.md",
            "Profile Assessment.md",
            "Skill Evaluation.md",
            "Bias Mitigated Responses.md"
        ]
        
        for filename in md_files:
            file_path = MD_FILES_DIR / filename
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    combined_content.append(f"## {filename[:-3]}\n\n{content}\n\n")
        
        if not combined_content:
            return jsonify({'error': 'No analysis available yet'}), 404
            
        return jsonify({'content': '\n'.join(combined_content)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_session', methods=['POST'])
def clear_session():
    session.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
