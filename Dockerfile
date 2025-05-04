FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user
RUN useradd -m appuser
USER appuser

# Run the application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} 