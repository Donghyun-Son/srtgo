FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including git
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    curl \
    libcurl4-openssl-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY srtgo-web/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code first
COPY srtgo-web/backend .

# Copy the original srtgo module for imports
COPY srtgo /app/srtgo

# Add srtgo module to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Create directories for data
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]