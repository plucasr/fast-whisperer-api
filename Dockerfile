# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
# IMPORTANT: This must be done first to leverage Docker's build cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir speeds up the build and reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code to the working directory (main.py, .env, etc.)
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run the application using Uvicorn
# The command starts the server, serving the 'app' object from 'main.py'
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
