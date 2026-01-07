# Multi-stage Dockerfile for Call Analysis App
# Optimized for Hugging Face Spaces FREE tier (16GB RAM, 2 CPU cores)

# Stage 1: Base image with system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Stage 2: Python dependencies
FROM base as builder

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Stage 3: Final image
FROM base

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY app.py .
COPY dashboard.py .
COPY analyser.py .
COPY transcriber.py .
COPY database.py .
COPY pdf_exporter.py .
COPY customer_sentiment.py .
COPY customer_sentiment_api.py .
COPY recalculate_sentiment.py .
COPY recalculate_if_needed.py .
COPY check_sentiment_scores.py .
COPY check_pos_neg_ratios.py .
COPY fix_agents.py .
COPY config.yaml .
COPY requirements.txt .

# Copy font files
COPY fonts/ fonts/
COPY dejavu-sans-ttf-2.37/ dejavu-sans-ttf-2.37/

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Create necessary directories
RUN mkdir -p audio_samples && \
    mkdir -p fonts && \
    mkdir -p dejavu-sans-ttf-2.37

# Expose ports
EXPOSE 8501 8503

# Health check on main app port
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run both Streamlit apps using the startup script
CMD ["./start.sh"]
