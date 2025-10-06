# Use official lightweight Python image
FROM python:3.13-slim AS base

# -----------------------------
# 1. Set environment variables
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/app/.venv/bin:$PATH"

# -----------------------------
# 2. Set working directory
# -----------------------------
WORKDIR /app

# -----------------------------
# 3. Install system dependencies
# -----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# 4. Install Python dependencies
# -----------------------------
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# -----------------------------
# 5. Copy project code
# -----------------------------
COPY . .

# -----------------------------
# 6. Collect static files
# -----------------------------
RUN python manage.py collectstatic --noinput

# -----------------------------
# 7. Expose port
# -----------------------------
EXPOSE 8000

# -----------------------------
# 8. Production Gunicorn CMD
# -----------------------------
# - 3 workers
# - timeout 120s
# - binds 0.0.0.0:8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
