FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY file_service ./file_service

RUN mkdir -p /app/file_service/uploads

EXPOSE 8003

CMD ["uvicorn", "file_service.main:app", "--host", "0.0.0.0", "--port", "8003"]