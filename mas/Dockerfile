# Use an official Python 3.11 runtime as a parent image
FROM python:3.11-slim

# Upgrade pip and install git (and clean up after installation)
RUN pip install --upgrade pip
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /mas

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

<<<<<<< HEAD
# Install Flask and any other needed packages explicitly
=======
# Install Flask and other required packages explicitly (if needed)
>>>>>>> cafb8480b4e8ba60ff860355e0c89468cb2e2765
RUN pip install flask crewai crewai-tools pymupdf langchain-google-genai faiss-cpu boto3 langchain-groq marko

# Copy the rest of the application code into the container
COPY . .

# Expose the port Flask will run on (default 5000)
EXPOSE 5000

<<<<<<< HEAD
# Define environment variable to run Flask in production mode
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Set environment to disable debug mode in production
ENV FLASK_ENV=production

# Run the application using Flask
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--extra-files", "app.py"]
=======
# Set environment variable to run Flask in production mode
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Install gunicorn and set the command to run Flask using it
RUN pip install gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
>>>>>>> cafb8480b4e8ba60ff860355e0c89468cb2e2765
