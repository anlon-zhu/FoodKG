# Use the official Python image as the base image
FROM python:3.8-slim

# Set the working directory
WORKDIR /flask-api

# Copy the requirements file into the container
COPY ./flask-api/requirements.txt .

# Install the required Python packages
RUN pip install -r requirements.txt

# Copy the rest of the Flask API application code into the container
COPY ./flask-api/ .

# Expose the port that your Flask app listens on
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]