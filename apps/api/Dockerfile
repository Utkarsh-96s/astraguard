FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY apps/api/pyproject.toml /workspace/apps/api/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e "/workspace/apps/api"

# Copy source code
COPY apps /workspace/apps
COPY ml /workspace/ml
COPY config /workspace/config
COPY .env* /workspace/

WORKDIR /workspace/apps/api

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
