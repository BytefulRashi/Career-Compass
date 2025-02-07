from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, g
from werkzeug.utils import secure_filename
from pathlib import Path
import sqlite3
import os
import fitz
from dotenv import load_dotenv
from src.mas.crew import Mas
from src.mas.S3 import upload_files_to_s3
from ragS3 import RAGS3
import io
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, EqualTo
from flask_bcrypt import Bcrypt

# import markdown

load_dotenv()

def generate_secret_key():
    return os.urandom(24).hex()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', generate_secret_key())
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DATABASE = "users.db"

# Database helper functions
def get_db():
    """Connect to the database."""
    if not hasattr(g, '_database'):
        g._database = sqlite3.connect(DATABASE)
        g._database.row_factory = sqlite3.Row
    return g._database

def init_db():
    """Initialize the database and create the users table if not exists."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL)''')
        conn.commit()

# Flask-Login User Model
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    """Load user from the database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    return User(user["id"], user["username"]) if user else None

# Registration Form
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# Login Form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

@app.before_request
def before_request():
    """Ensure database connection is available before each request."""
    get_db()

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

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
@login_required
def index():
    return render_template('base.html')  # Changed to use our new base.html template

@app.route('/submit_goal', methods=['POST'])
@login_required
def submit_goal():
    career_goal = request.form.get('career_goal')
    if career_goal:
        session['career_goal'] = career_goal
        return jsonify({'success': True})
    return jsonify({'error': 'Career goal is required'}), 400

@app.route('/upload_resume', methods=['POST'])
@login_required
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
@login_required
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
@login_required
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        conn = get_db()
        cursor = conn.cursor()
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (form.username.data, hashed_password))
            conn.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (form.username.data,))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user["password"], form.password.data):
            login_user(User(user["id"], user["username"]))
            flash('Login successful!', 'success')
            return redirect('/')
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
