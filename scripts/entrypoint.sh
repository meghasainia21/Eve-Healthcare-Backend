#!/bin/sh
set -e

echo "Waiting for database to be ready..."
python -c "
import time
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

for attempt in range(30):
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database is ready.')
        sys.exit(0)
    except Exception as exc:
        print(f'DB not ready yet (attempt {attempt + 1}/30): {exc}')
        time.sleep(1)
print('Database never became ready, giving up.')
sys.exit(1)
"

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
