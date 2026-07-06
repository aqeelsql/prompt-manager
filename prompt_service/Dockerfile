FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY prompt_service ./prompt_service

EXPOSE 8000

CMD ["uvicorn", "prompt_service.main:app", "--host", "0.0.0.0", "--port", "8000"]