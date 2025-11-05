# Etapa 1: construir el entorno con dependencias
FROM python:3.12.6 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 2: imagen final más ligera
FROM python:3.12.6-slim

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . .

# Fly espera que la app escuche en el puerto 8080
EXPOSE 8080

# Usa waitress para servir la app en el puerto 8080
CMD ["waitress-serve", "--listen=0.0.0.0:8080", "app:app"]


