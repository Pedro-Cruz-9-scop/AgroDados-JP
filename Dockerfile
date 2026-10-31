FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY . .

# Valor só para o build; a chave real vem das variáveis de ambiente em execução.
RUN DJANGO_DEBUG=0 DJANGO_SECRET_KEY=build-only-not-used-at-runtime \
    python manage.py collectstatic --noinput

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && exec python -m gunicorn agrodados.wsgi:application --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 120"]
