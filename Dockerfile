FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-render.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements-render.txt

COPY . .

EXPOSE 8501

CMD ["sh", "-c", "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 & BACKEND_PID=$!; streamlit run frontend.py --server.address 0.0.0.0 --server.port ${PORT:-8501} --server.headless true & FRONTEND_PID=$!; wait $BACKEND_PID; BACKEND_EXIT=$?; kill $FRONTEND_PID 2>/dev/null || true; wait $FRONTEND_PID 2>/dev/null || true; exit $BACKEND_EXIT"]
