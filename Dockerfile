FROM python:3.11-slim

WORKDIR /code


# Copy requirements from src and install
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from src/app into the image
COPY src/app ./app

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]