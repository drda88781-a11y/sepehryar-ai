FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

COPY . .

EXPOSE 8080

CMD ["python", "start_production.py"]
