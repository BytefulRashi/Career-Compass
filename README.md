![image](https://github.com/user-attachments/assets/5d27e495-9bb1-4ec7-83df-a1e76d2b6059)


# Career Compass: AI-Powered Career Guidance Platform

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-green.svg)](https://www.python.org/downloads/)

Career Compass is an innovative AI-driven platform developed for the Amdocs Gen AI Hackathon 2024-2025. Our platform revolutionizes career guidance by combining advanced AI technologies with emotional intelligence to provide personalized, unbiased career advice and professional development planning.

## 🌟 Key Features

Career Compass leverages a sophisticated multi-agent system to deliver comprehensive career guidance:

- **Personalized Career Recommendations**: Data-driven advice based on your skills, experience, and market trends
- **Advanced Skill Assessment**: In-depth analysis of your competencies and personalized development roadmaps
- **Emotionally Intelligent Conversations**: Natural, empathetic interactions powered by advanced AI
- **Bias-Free Guidance**: Engineered to provide fair and inclusive career recommendations
- **Real-Time Market Insights**: Up-to-date career opportunities aligned with industry trends
- **Continuous Learning**: System evolves and improves through user feedback and market data

## 🚀 Getting Started

### Prerequisites

Before installation, ensure you have:

- Python 3.11 or higher
- pip (Python package manager)
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/career-compass.git
cd career-compass
```

2. Create and activate a virtual environment:
```bash
# For Unix/macOS
python -m venv .venv
source .venv/bin/activate

# For Windows
python -m venv .venv
.venv\Scripts\activate.ps1
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Install additional dependencies:
```bash
pip install crewai crewai-tools pymupdf langchain-google-genai faiss-cpu boto3 langchain-groq marko streamlit
```

5. Set up environment variables:
```bash
# Create .env file in src/mas directory
touch src/mas/.env

# Add required environment variables
# Example:
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
```

### Verification

Verify your installation:
```bash
pip list  # Check installed packages
pip check  # Verify dependencies
```

### Running the app
```bash
flask run --extra-files "app.py"
```

## 🏗️ System Architecture

### Multi-Agent Analysis Orchestra

Our platform utilizes five specialized AI agents:

1. **Market Analyst Agent**: Processes industry trends and identifies emerging opportunities
2. **Profile Assessment Agent**: Evaluates user profiles and career trajectories
3. **Skill Evaluation Agent**: Conducts comprehensive skill gap analysis
4. **Bias Mitigation Agent**: Ensures fair and unbiased recommendations
5. **Career Guide Agent**: Synthesizes insights into actionable career plans

### Emotionally Intelligent RAG Interface

The platform features an advanced Retrieval-Augmented Generation (RAG) system that provides:

- Context-aware responses
- Personalized career insights
- Emotionally intelligent interactions
- Natural conversation flow

## 🎯 Use Cases

Career Compass serves diverse user needs:

- **Students**: Discover career paths aligned with their interests and skills
- **Professionals**: Plan career transitions and skill development
- **Career Counselors**: Augment their guidance with data-driven insights
- **HR Professionals**: Support employee development and career planning

## Prototype

![image](https://github.com/user-attachments/assets/84f8236a-7d3a-4b2b-ac5a-8a3011598166)
![image](https://github.com/user-attachments/assets/dbeae431-01a3-4abd-bba6-79062bafe3f4)
![image](https://github.com/user-attachments/assets/1df08133-45d5-480d-91af-cd6238f35b8d)


## 🛣️ Roadmap

Future enhancements planned:

- Integration with major job platforms
- AI-powered interview preparation module
- Industry mentor matching system
- Real-time market opportunity alerts
- Enhanced skill assessment tools
- International market insights

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

- Project Team - [careercompass@example.com](mailto:your-email@example.com)

## 🏆 Acknowledgments

- Amdocs Gen AI Hackathon 2024-2025 organizers
- The open-source community

Developed with ❤️ for the Amdocs Gen AI Hackathon 2024-2025
