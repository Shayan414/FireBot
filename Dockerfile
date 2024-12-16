# Use the official Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies, including FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Copy project files to the container
COPY . /app

# Install Python dependencies
RUN python -m venv /opt/venv && . /opt/venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

# Add venv to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Run the bot
CMD ["python", "main.py"]
