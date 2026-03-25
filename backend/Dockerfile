# syntax=docker/dockerfile:1

# Set base image to python 3.11 slim
FROM python:3.11-slim

# Set working directory to /app
WORKDIR /app

# Copy requirements.txt to the working directory and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Expose port 8000 for the application
EXPOSE 8000

# Set the command to run the application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
