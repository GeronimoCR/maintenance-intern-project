FROM python:3.12.6 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt

FROM python:3.12.6-slim
WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .

# Exponer el puerto
EXPOSE 8080

# Ejecutar directamente tu aplicación (usa waitress dentro de app.py)
CMD ["/app/.venv/bin/python", "app.py"]

