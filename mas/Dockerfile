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

# Install Flask and any other needed packages explicitly
RUN pip install flask crewai crewai-tools pymupdf langchain-google-genai faiss-cpu boto3 langchain-groq marko

# Copy the rest of the application code into the container
COPY . .

# Expose the port Flask will run on (default 5000)
EXPOSE 5000

# Define environment variable to run Flask in production mode
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Set environment to disable debug mode in production
ENV FLASK_ENV=production

# Run the application using Flask
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--extra-files", "app.py"]
