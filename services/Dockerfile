FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
# Install system dependencies required for gunicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 5000

# Define the entrypoint command using Gunicorn for production
ARG APP_FILE
ENV APP_FILE=${APP_FILE}

# GARANTIR que a aplicação existe antes de copiar
COPY fiware.py .
COPY ${APP_FILE}.py .

ARG CONFIG=server
ENV CONFIG=${CONFIG}

# Default CMD
CMD ["sh", "-c", "if [ \"$CONFIG\" = \"server\" ]; then gunicorn --bind 0.0.0.0:5000 ${APP_FILE}:app; else python ${APP_FILE}.py; fi"]