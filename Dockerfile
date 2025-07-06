# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install any needed packages specified in requirements.txt
# RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable for the port
ENV PORT 8080

# Define environment variable for GCP Project (Needed for bucket creation if not inferred)
# This should be set in Cloud Run environment variables
ENV GCP_PROJECT your-gcp-project-id

# Recommended: Set GOOGLE_APPLICATION_CREDENTIALS in Cloud Run service account settings
# or mount a service account key if running locally and not using gcloud auth application-default login

# Run main.py when the container launches
# Use gunicorn for production deployments as it's a WSGI HTTP server
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
