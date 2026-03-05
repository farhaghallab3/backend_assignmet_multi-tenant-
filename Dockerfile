FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql+asyncpg://user:password@db:5432/dbname

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
