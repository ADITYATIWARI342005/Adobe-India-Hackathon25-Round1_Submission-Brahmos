# Adobe Hackathon Round 1B: Document Intelligence System
# Minimal approach - install dependencies using pip only

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy Python dependencies first for better caching
COPY pyproject.toml ./

# Install Python dependencies directly (pdfplumber has binary wheels available)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install pdfplumber==0.10.3 \
    && pip cache purge

# Copy application code
COPY main_semantic.py ./
COPY document_analyzer.py ./
COPY pdf_parser.py ./
COPY embedder.py ./
COPY retriever.py ./
COPY enhanced_ranking.py ./
COPY config.py ./

# Create necessary directories
RUN mkdir -p /app/Challenge_1b /app/output /app/logs \
    && chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Switch to non-root user
USER appuser

# Set default command
CMD ["python", "main_semantic.py", "--all"]

# Add labels for metadata
LABEL maintainer="Adobe Hackathon Team"
LABEL version="1.0.0"
LABEL description="Persona-driven document intelligence system for Adobe Hackathon Round 1B"
LABEL challenge="Adobe India Hackathon Round 1B"


# To build image 
# docker build -t adobe-document-intelligence:latest .

# To run container
# docker run --rm   -v $(pwd)/Challenge_1b:/app/Challenge_1b   adobe-document-intelligence:latest   python main_semantic.py --all