# ---------- Base Image ----------
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# ---------- System Dependencies ----------
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# ---------- Working Directory ----------
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Playwright setup (downloads browser binaries)
RUN playwright install chromium

# ---------- Copy App Code ----------
COPY . .

# Expose the port
EXPOSE 8000

# ---------- Start Command ----------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
