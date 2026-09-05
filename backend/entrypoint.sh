#!/bin/sh
set -e

echo "[entrypoint] Starting Recon API..."

# Wait for database to be ready
echo "[entrypoint] Waiting for PostgreSQL..."
until python -c "
import urllib.request
import os
import time
while True:
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='postgres',
            port=5432,
            user=os.environ.get('POSTGRES_USER', 'recon'),
            password=os.environ.get('POSTGRES_PASSWORD', 'recon'),
            dbname=os.environ.get('POSTGRES_DB', 'recon'),
            connect_timeout=5
        )
        conn.close()
        break
    except Exception:
        time.sleep(2)
" 2>/dev/null; do
    echo "[entrypoint] PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "[entrypoint] PostgreSQL is ready!"

# Run database migrations
echo "[entrypoint] Running database migrations..."
cd /app
python -m alembic upgrade head || echo "[entrypoint] Alembic migration failed or not configured, continuing..."

# Create storage directories
mkdir -p /app/storage/uploads
chmod 755 /app/storage/uploads

echo "[entrypoint] Starting uvicorn..."
exec "$@"
