FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr -
# makes `docker logs` behave sensibly.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# `curl` is only needed for the container HEALTHCHECK below.
# psycopg2-binary ships precompiled wheels, so no build toolchain is needed.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x scripts/entrypoint.sh \
    && useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["scripts/entrypoint.sh"]
