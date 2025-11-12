# ─────────────────────────────────────────────
# Backend: FastAPI + Python 3.11
# ─────────────────────────────────────────────
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependencies first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend source files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
