FROM python:3.12-slim

WORKDIR /app

# Install deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code (the Excel is uploaded by the user at runtime, not baked in)
COPY stamp_tescil.py app.py ./
COPY templates ./templates

EXPOSE 8000

# Serve with gunicorn; app:app = module app.py, Flask object `app`.
#
# --workers 1 is load-bearing, not a performance choice. The uploaded workbook
# and the pending download live in this process's memory, so a second worker
# means the Excel can land on one and the PDF on the other — "no source loaded",
# intermittently. See decisions/0008-single-user-session-scoped.
# Threads keep the UI responsive during a batch without splitting that memory.
#
# --timeout 300: a batch of PDFs takes longer than the 30s default allows.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", \
     "--workers", "1", "--threads", "4", "--worker-class", "gthread", \
     "--timeout", "300", "app:app"]
