# Crosshatch v2.0 Docker Image
# Multi-stage build for optimal image size

# Stage 1: Base image with Python and system dependencies
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Stage 2: Build stage - install dependencies
FROM base as builder

# Copy requirements first (for better caching)
COPY requirements.txt .
COPY setup.py .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install SAM2
RUN git clone https://github.com/facebookresearch/sam2.git && \
    cd sam2 && \
    pip install --no-cache-dir -e .

# Stage 3: Runtime stage
FROM base as runtime

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/sam2 /app/sam2

# Copy application code
COPY crosshatch/ /app/crosshatch/
COPY docker-app/app.py /app/
COPY setup.py /app/

# Install the crosshatch package
RUN pip install --no-cache-dir -e .

# Download SAM2 checkpoints
RUN mkdir -p /app/sam2/checkpoints && \
    cd /app/sam2/checkpoints && \
    wget -q https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt && \
    echo "✓ Downloaded SAM2 checkpoint"

# Create directories for uploads/outputs
RUN mkdir -p /tmp/uploads /tmp/outputs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV PORT=5000
ENV DEVICE=cuda
ENV SAM2_MODEL=small
ENV MAX_DIMENSION=1200

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Run the application
CMD ["python", "app.py"]
