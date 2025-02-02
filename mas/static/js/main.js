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

// Load Analysis Results
// Previous code remains the same...

function loadAnalysis() {
    const analysisTypes = [
        { id: 'careerGuidance', title: 'Career Guidance', file: 'Career Guidance.txt' },
        { id: 'skillEvaluation', title: 'Skill Evaluation', file: 'Skill Evaluation.txt' },
        { id: 'profileAssessment', title: 'Profile Assessment', file: 'Profile Assessment.txt' },
        { id: 'marketAnalysis', title: 'Market Analysis', file: 'Market Analysis.txt' }
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

    fetch(`/outputs/${filename}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Analysis not available');
            }
            return response.text();
        })
        .then(content => {
            // Create a pre element to preserve formatting
            const preElement = document.createElement('pre');
            preElement.className = 'analysis-text';
            // Safely escape any HTML content and preserve whitespace
            preElement.textContent = content;
            
            // Clear the content div and append the pre element
            contentDiv.innerHTML = '';
            contentDiv.appendChild(preElement);
        })
        .catch(error => {
            console.error("Error loading analysis content:", error);
            contentDiv.innerHTML = 
                '<p class="message error">Analysis content not available. Please ensure your resume has been processed.</p>';
        });
}
// Rest of the code remains the same...

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
        // Add bot message
        const botMessage = document.createElement("div");
        botMessage.className = "chat-message bot-message";
        botMessage.innerHTML = `<strong>Career Advisor:</strong> ${data.answer}`;
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