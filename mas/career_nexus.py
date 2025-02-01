import streamlit as st
from pathlib import Path
import os
from src.mas.crew import Mas
from src.mas.S3 import upload_files_to_s3
import fitz 
import io
import time
from ragS3 import RAGS3
from dotenv import load_dotenv

load_dotenv()

def read_log_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return "Log file not found."
    except Exception as e:
        return f"Error reading log file: {str(e)}"

def convert_pdf_to_text(pdf_file):
    """
    Convert PDF file to text using PyMuPDF while preserving formatting and content.
    Args:
        pdf_file: Uploaded PDF file from Streamlit
    Returns:
        str: Extracted text from PDF
    """
    try:
        pdf_bytes = pdf_file.getvalue()
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

# Ensure correct working directory
CURRENT_DIR = Path(os.getcwd())

# Define directories with absolute paths
BASE_DIR = CURRENT_DIR / ""
TEXT_FILES_DIR = BASE_DIR / "processed_resumes"
MD_FILES_DIR = BASE_DIR / "output"

# Ensure required directories exist
TEXT_FILES_DIR.mkdir(parents=True, exist_ok=True)
MD_FILES_DIR.mkdir(parents=True, exist_ok=True)

# Initialize session state variables
if "career_goal" not in st.session_state:
    st.session_state["career_goal"] = ""
if "resume_txt_path" not in st.session_state:
    st.session_state["resume_txt_path"] = ""
if "processing_done" not in st.session_state:
    st.session_state["processing_done"] = False
if "rag_initialized" not in st.session_state:
    st.session_state["rag_initialized"] = False
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "rag_instance" not in st.session_state:
    st.session_state["rag_instance"] = None

def initialize_rag():
    try:
        with st.spinner("Initializing RAG system..."):
            rag = RAGS3(
                bucket_name=os.environ.get("BUCKET_NAME"),
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
            )
            st.session_state["rag_instance"] = rag
            st.session_state["rag_initialized"] = True
            return True
    except Exception as e:
        st.error(f"Error initializing RAG system: {str(e)}")
        return False

# Streamlit UI
st.set_page_config(
    page_title="Career Compass Prototype",
    page_icon=":rocket:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force light theme
def set_light_theme():
    st.markdown("""
    <style>
    html, body, [class*="css"]  {
        color: #000000;
        background-color: #ffffff;
    }
    .st-emotion-cache-6qob1r {
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

set_light_theme()

# Add logo to the sidebar
st.sidebar.image("logo.png", width = 500)

# Main title
st.markdown('<div class="title">Career Compass Prototype</div>', unsafe_allow_html=True)

# Resume upload
uploaded_resume = st.file_uploader("Upload Your Resume (.pdf)", type="pdf")

categories = {
    "Career Guidance": "Career Guidance.md",
    "Market Analysis": "Market Analysis.md",
    "Your Profile Assessment": "Profile Assessment.md",
    "Skill Evaluation": "Skill Evaluation.md",
    "Bias Mitigation": "Bias Mitigated Responses.md"
}

# Sidebar for selecting generated insights
nav_options = list(categories.keys()) + ["Chat with Career Advisor"]
selected_category = st.sidebar.selectbox("Select a category:", nav_options)

# Process only if both career goal and resume are present
if uploaded_resume and st.session_state.get("topic") and not st.session_state["processing_done"]:
    try:
        # Convert PDF to text
        resume_text = convert_pdf_to_text(uploaded_resume)
        
        # Save converted text to file
        resume_path = TEXT_FILES_DIR / f"{uploaded_resume.name[:-4]}.txt"
        with open(resume_path, "w", encoding='utf-8') as txt_file:
            txt_file.write(resume_text)

        st.session_state["resume_txt_path"] = str(resume_path)
        st.success("Resume converted and uploaded successfully! Processing...")

        # Prepare inputs for Mas
        inputs = {
            "resume": str(resume_path),
            "topic": st.session_state["topic"]
        }

        try:
            Mas().crew().kickoff(inputs=inputs)
            upload_files_to_s3('output', os.environ.get('BUCKET_NAME'))
            st.session_state["processing_done"] = True
            st.success("Processing completed! Reports are ready.")
            st.rerun()
        except Exception as e:
            st.error(f"Error during processing: {str(e)}")
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        
elif uploaded_resume and not st.session_state.get("topic"):
    st.warning("Please enter your career goal before uploading your resume.")

# Define categories based on generated markdown files
categories = {
    "Career Guidance": "Career Guidance.md",
    "Market Analysis": "Market Analysis.md",
    "Your Profile Assessment": "Profile Assessment.md",
    "Skill Evaluation": "Skill Evaluation.md",
    "Bias Mitigation": "Bias Mitigated Responses.md"
}

# Sidebar for selecting generated insights as navigation buttons
nav_options = list(categories.keys()) + ["Chat with Career Advisor"]
# Using radio buttons to mimic navigation buttons
selected_category = st.sidebar.radio("Select a category:", nav_options, key="nav")

if selected_category != "Chat with Career Advisor":
    with st.chat_message("assistant"):
        st.write("What do you want to become?")
    career_goal = st.chat_input("Enter your career goal here...")
    if career_goal:
        st.session_state["topic"] = career_goal
        with st.chat_message("user"):
            st.write(career_goal)
        st.write(f"Your career goal: {career_goal}")

if selected_category == "Chat with Career Advisor":
    st.subheader("Chat with Your Career Advisor")
    
    if not st.session_state["processing_done"]:
        st.warning("Please complete the resume processing first to chat with the career advisor.")
    else:
        # Ensure RAG is initialized
        if not st.session_state["rag_initialized"]:
            if not initialize_rag():
                st.error("Unable to initialize the chat system. Please try again.")
                st.stop()
        
        # Display chat history
        for message in st.session_state["chat_history"]:
            role = message["role"]
            content = message["content"]
            with st.chat_message(role):
                st.write(content)

        # Chat input
        user_question = st.chat_input("Ask your career-related questions...", key="career_advisor_chat")
        
        if user_question:
            # Display user message
            with st.chat_message("user"):
                st.write(user_question)

            # Get RAG response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        if st.session_state["rag_instance"] is None:
                            raise Exception("Chat system not properly initialized")
                            
                        response = st.session_state["rag_instance"].query(
                            user_question, 
                            st.session_state["chat_history"]
                        )
                        st.write(response["answer"])

                        # Update chat history
                        st.session_state["chat_history"].append({"role": "user", "content": user_question})
                        st.session_state["chat_history"].append({"role": "assistant", "content": response["answer"]})
                    except Exception as e:
                        st.error(f"Error getting response: {str(e)}")

# Display content only if processing is done
if st.session_state["processing_done"] and selected_category in categories:
    file_path = MD_FILES_DIR / categories[selected_category]
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as file:
            st.markdown(file.read(), unsafe_allow_html=True)  # Render Markdown
    else:
        st.warning(f"Report for '{selected_category}' is not available yet. Please wait for processing.")

# Custom CSS for styling
st.markdown(
    """
    <style>
    /* Main container styling */
    .main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }

    /* Title styling */
    .title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4A90E2;
        text-align: center;
        margin-bottom: 20px;
    }
    

    /* Removed override for inner content color so that it can inherit dark blue styling */

    /* Style for the sidebar close button */
    [data-testid="stSidebar"] button[aria-label="Close"] {
        color: #00008B !important;
        background: transparent !important;
        border: none;
    }

    /* Logo styling */
    .logo {
        display: block;
        width: 300px;
        margin: 0 auto 10px auto;  /* Centers the logo horizontally */
    }


    /* Button styling for other buttons in the app */
    .stButton>button {
        background-color: #4A90E2;
        color: #00008B;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 1rem;
        border: none;
        cursor: pointer;
    }

    .stButton>button:hover {
        background-color: #357ABD;
        color: #00008B;
    }

    /* Custom styling for radio buttons used for navigation in the sidebar */
    div[data-baseweb="radio"] label {
        display: block;
        border: 1px solid #00008B;  /* Dark blue border */
        border-radius: 5px;
        padding: 8px 12px;
        margin-bottom: 8px;
        background-color: white;
        color: #00008B;            /* Dark blue text */
        cursor: pointer;
        transition: background-color 0.3s, color 0.3s;
    }
    
    /* Hide the default radio circles */
    div[data-baseweb="radio"] input[type="radio"] {
        display: none;
    }
    
    /* Style for the selected navigation button */
    div[data-baseweb="radio"] input:checked + div {
        background-color: #00008B !important;
        color: white !important;
    }
    
    /* Hover effect for navigation buttons: light blue background */
    div[data-baseweb="radio"] label:hover {
        background-color: #ADD8E6;
        color: #00008B;
    }

    /* Chat message styling */
    .chat-message {
        background-color: #F1F1F1;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }

    .chat-message.user {
        background-color: #4A90E2;
        color: white;
    }

    .chat-message.assistant {
        background-color: #E1E1E1;
        color: #333;
    }

    /* Markdown content styling */
    .markdown-content {
        background-color: #F9F9F9;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True,
)
