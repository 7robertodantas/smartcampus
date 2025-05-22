FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies required for gunicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY weather_context_enricher.py .

# Expose the application port
EXPOSE 5000

# Define the entrypoint command using Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--log-level", "debug", "--capture-output", "weather_context_enricher:app"]
