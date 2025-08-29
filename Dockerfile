# Multi-stage Docker build for AI Writer application

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/web
COPY web/package.json web/package-lock.json* ./
RUN npm ci --only=production

COPY web/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim AS backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application code
COPY apps/ ./apps/
COPY packages/ ./packages/
COPY prompts/ ./prompts/

# Copy built frontend
COPY --from=frontend-builder /app/web/dist ./web/dist

# Create necessary directories
RUN mkdir -p logs data runs bundles

# Create non-root user
RUN useradd --create-home --shell /bin/bash aiwriter
RUN chown -R aiwriter:aiwriter /app
USER aiwriter

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

# Start command
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]