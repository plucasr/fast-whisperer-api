# Stage 1: Base Image
FROM python:3.10-slim

# Install system dependencies (FFmpeg) and immediately clean up APT cache
# This single RUN command is key for reducing image size and layers
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy only the requirements file first to leverage Docker's build cache
COPY requirements.txt .

# Install Python packages
# Use --no-cache-dir and upgrade pip for best practice
# All dependencies (including yt-dlp) should be listed in requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
# This is done AFTER dependencies so code changes don't bust the pip cache
COPY . .

# Environment setup (can be done here or handled by the app/entrypoint)
# The application should be responsible for creating temp_audio if it doesn't exist,
# but defining it here is fine for clarity if the app is relying on it being present.
RUN mkdir -p temp_audio

# Expose the port
EXPOSE 8000

# Run the application
# Use the executable form for CMD
# Note: For production, it's often better to use an ENTRYPOINT script
# to ensure the temp_audio directory has the correct permissions if needed.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
