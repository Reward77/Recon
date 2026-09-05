#!/bin/sh
set -e

echo "[worker-entrypoint] Starting Recon Celery Worker..."

# Wait for database to be ready
echo "[worker-entrypoint] Waiting for PostgreSQL..."
until python -c "
import os
import time
import psycopg2
while True:
    try:
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
    echo "[worker-entrypoint] PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "[worker-entrypoint] PostgreSQL is ready!"

# Wait for Redis
echo "[worker-entrypoint] Waiting for Redis..."
until python -c "
import os
import time
import redis
while True:
    try:
        r = redis.Redis(
            host='redis',
            port=6379,
            password=os.environ.get('REDIS_PASSWORD', 'recon-redis-secret'),
            socket_timeout=5,
            socket_connect_timeout=5
        )
        r.ping()
        break
    except Exception:
        time.sleep(2)
" 2>/dev/null; do
    echo "[worker-entrypoint] Redis is unavailable - sleeping"
    sleep 2
done
echo "[worker-entrypoint] Redis is ready!"

# Create storage directories
mkdir -p /app/storage/uploads
chmod 755 /app/storage/uploads

echo "[worker-entrypoint] Starting Celery worker..."
exec "$@"
