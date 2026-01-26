FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p staticfiles media

RUN python manage.py collectstatic --noinput

EXPOSE 8080

CMD python manage.py migrate && python create_admin.py && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080}
