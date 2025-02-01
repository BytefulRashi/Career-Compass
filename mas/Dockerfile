# Use an official Python 3.11 runtime as a parent image
FROM python:3.11-slim
RUN pip install --upgrade pip

RUN apt-get update && apt-get install -y git && apt-get clean

# Set the working directory in the container
WORKDIR /mas

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional required packages
RUN pip install crewai crewai-tools pymupdf langchain-google-genai faiss-cpu boto3 langchain-groq marko

# Install Streamlit
RUN pip install streamlit

# Copy the rest of the application code into the container
COPY . .

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["streamlit", "run", "career_nexus.py"]