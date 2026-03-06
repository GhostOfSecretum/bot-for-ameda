FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app
COPY run_bot.py admin_dashboard.py ./
COPY credentials ./credentials
COPY .env ./.env

RUN mkdir -p /app/data/photos

CMD ["python", "run_bot.py"]
