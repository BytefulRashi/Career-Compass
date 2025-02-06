const { BUCKET_NAME } = require('./config.js');
const { AWS_REGION } = require('./config.js');

// Navigation
document.querySelectorAll('.sidebar nav a').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        
        document.querySelectorAll('.sidebar nav a').forEach(l => l.classList.remove('active'));
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        
        this.classList.add('active');
        
        const sectionId = this.id.replace('Link', 'Section');
        document.getElementById(sectionId).classList.add('active');
    });
});

// Career Goal Form
document.getElementById("goalForm").addEventListener("submit", function(e) {
    e.preventDefault();
    const goal = document.getElementById("careerGoal").value;
    const messageElement = document.getElementById("goalMessage");
    
    fetch("/submit_goal", {
        method: "POST",
        body: new URLSearchParams({ career_goal: goal }),
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
    })
    .then(response => response.json())
    .then(data => {
        messageElement.innerText = data.success ? "Career goal set successfully!" : "Error setting goal";
        messageElement.className = `message ${data.success ? 'success' : 'error'}`;
    })
    .catch(error => {
        messageElement.innerText = "An error occurred while setting the goal";
        messageElement.className = "message error";
    });
});
// Resume Upload Form
document.getElementById("resumeForm").addEventListener("submit", function(e) {
    e.preventDefault();
    const formData = new FormData();
    const fileInput = document.getElementById("resume");
    const messageElement = document.getElementById("uploadMessage");
    
    if (fileInput.files.length > 0) {
        formData.append("resume", fileInput.files[0]);
        messageElement.innerText = "Resume uploaded, please wait while we analyse it";
        messageElement.className = "message info";
        
        fetch("/upload_resume", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                messageElement.innerText = "Error: " + data.error;
                messageElement.className = "message error";
            } else {
                setTimeout(() => {
                    loadAnalysis();
                }, 1000);
            }
        })
        .catch(error => {
            messageElement.innerText = "An error occurred while uploading the resume";
            messageElement.className = "message error";
        });
    }
});

function loadAnalysis() {
    const analysisTypes = [
        { id: 'careerGuidance', title: 'Career Guidance', file: 'Career Guidance.md' },
        { id: 'skillEvaluation', title: 'Skill Evaluation', file: 'Skill Evaluation.md' },
        { id: 'profileAssessment', title: 'Profile Assessment', file: 'Profile Assessment.md' },
        { id: 'marketAnalysis', title: 'Market Analysis', file: 'Market Analysis.md' }
    ];

    const analysisContent = document.getElementById("analysisContent");
    analysisContent.innerHTML = ''; // Clear existing content

    // Create buttons container
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'analysis-buttons';
    
    // Create and add buttons
    analysisTypes.forEach(type => {
        const button = document.createElement('button');
        button.className = 'btn analysis-btn';
        button.textContent = type.title;
        button.addEventListener('click', () => loadAnalysisContent(type.file));
        buttonContainer.appendChild(button);
    });

    analysisContent.appendChild(buttonContainer);
    
    // Create content container
    const contentDiv = document.createElement('div');
    contentDiv.id = 'analysisTextContent';  // Changed from analysisMarkdownContent
    contentDiv.className = 'analysis-content';
    analysisContent.appendChild(contentDiv);

    // Load first analysis by default
    loadAnalysisContent(analysisTypes[0].file);
}

function loadAnalysisContent(filename) {
    const contentDiv = document.getElementById('analysisTextContent');
    
    // Update active button state
    document.querySelectorAll('.analysis-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent === filename.split('.')[0]) {
            btn.classList.add('active');
        }
    });

    // Show loading state
    contentDiv.innerHTML = '<p class="loading">Loading analysis...</p>';
    console.log('Loading analysis content for file:', filename);

    // S3 bucket public URL
    const bucketName = BUCKET_NAME;  // Replace with your actual bucket name
    const s3Region = AWS_REGION;  // Replace with your actual AWS region
    const s3BaseUrl = `https://${bucketName}.s3.${s3Region}.amazonaws.com/outputs/`;

    // Construct the full URL
    const fileUrl = s3BaseUrl + encodeURIComponent(filename);
    console.log('Constructed file URL:', fileUrl);

    // Fetch the content from the file URL
    fetch(fileUrl)
        .then(response => {
            console.log('Response received for file:', filename, 'Status:', response.status);
            if (!response.ok) {
                throw new Error('Analysis not available');
            }
            return response.text();
        })
        .then(content => {
            console.log('Content fetched successfully for file:', filename);

            // Use marked.js to convert markdown content to HTML
            const htmlContent = marked.parse(content);

            // Clear the content div and insert the HTML
            contentDiv.innerHTML = htmlContent;
            console.log('Markdown content displayed successfully in the analysis area.');
        })
        .catch(error => {
            console.error("Error loading analysis content:", error);
            contentDiv.innerHTML = 
                '<p class="message error">Analysis content not available. Please ensure your resume has been processed.</p>';
        });
}

// Chat functions remain unchanged
function sendChat() {
    const chatInput = document.getElementById("chatInput");
    const question = chatInput.value.trim();
    
    if (!question) return;
    
    const chatBox = document.getElementById("chatBox");
    
    // Add user message
    const userMessage = document.createElement("div");
    userMessage.className = "chat-message user-message";
    userMessage.innerHTML = `<strong>You:</strong> ${question}`;
    chatBox.appendChild(userMessage);
    
    // Clear input
    chatInput.value = "";
    
    // Send to server
    fetch("/chat", {
        method: "POST",
        body: JSON.stringify({ question }),
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        // Convert the bot's markdown response to HTML using marked.js
        const htmlResponse = marked.parse(data.answer);

        // Add bot message
        const botMessage = document.createElement("div");
        botMessage.className = "chat-message bot-message";
        botMessage.innerHTML = `<strong>Career Advisor:</strong> ${htmlResponse}`;
        chatBox.appendChild(botMessage);
        
        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(error => {
        const errorMessage = document.createElement("div");
        errorMessage.className = "chat-message bot-message error";
        errorMessage.innerHTML = "<strong>Error:</strong> Failed to get response";
        chatBox.appendChild(errorMessage);
    });
}

// Chat input enter key handler
document.getElementById("chatInput").addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
        sendChat();
    }
});

// Initial load
document.addEventListener("DOMContentLoaded", function() {
    // Load analysis if available
    loadAnalysis();
});

document.addEventListener('DOMContentLoaded', function() {
    // Load analysis if available
    loadAnalysis();

    // Smooth Scroll Animations using IntersectionObserver
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('translate-y-0', 'opacity-100');
                entry.target.classList.remove('translate-y-20', 'opacity-0');
            } else {
                entry.target.classList.remove('translate-y-0', 'opacity-100');
                entry.target.classList.add('translate-y-20', 'opacity-0');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
});
