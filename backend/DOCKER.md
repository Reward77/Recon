# Docker Production Deployment Guide

## Architecture Overview

```
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
|   API Service     |---->|   Redis           |<----|   Worker Service  |
|   (FastAPI)       |     |   (Broker +       |     |   (Celery)        |
|                   |     |    Result Backend)|     |                   |
+-------------------+     +-------------------+     +-------------------+
         |                           |                         |
         |                           |                         |
         v                           v                         v
+--------------------------------------------------------------------+
|                                                                    |
|   PostgreSQL                                                       |
|   (Persistent Volume)                                              |
|                                                                    |
+--------------------------------------------------------------------+
```

### Services

| Service | Image | Purpose | Ports |
|---------|-------|---------|-------|
| `api` | Built from `Dockerfile` | FastAPI application server | `127.0.0.1:8000` |
| `worker` | Built from `Dockerfile.worker` | Celery background worker | None |
| `postgres` | `postgres:16-alpine` | Primary database | `127.0.0.1:5432` |
| `redis` | `redis:7-alpine` | Message broker + result backend | `127.0.0.1:6379` |
| `flower` | `mher/flower:2.0.1` | Celery monitoring dashboard | `127.0.0.1:5555` |

### Networking

All services communicate over an isolated bridge network (`recon-net`) with static IP assignments for predictable DNS resolution.

### Volumes

| Volume | Mount Point | Purpose |
|--------|-------------|---------|
| `postgres-data` | `/var/lib/postgresql/data` | Database persistence |
| `redis-data` | `/data` | Redis persistence (RDB + AOF) |
| `uploads-data` | `/app/storage/uploads` | Shared file storage between API and worker |

---

## Quick Start

### Prerequisites

- Docker Engine 24+
- Docker Compose 2.20+
- 4GB+ available RAM
- 10GB+ available disk space

### 1. Configure Environment

```bash
cd backend
cp .env.production .env
# Edit .env with your production values
```

### 2. Build and Start

```bash
# Production mode (without Flower)
docker compose up -d --build

# With Flower monitoring dashboard
docker compose --profile monitoring up -d --build
```

### 3. Verify Services

```bash
docker compose ps
docker compose logs -f api
docker compose logs -f worker
```

### 4. Run Migrations

Migrations run automatically via the API entrypoint. To run manually:

```bash
docker compose exec api alembic upgrade head
```

### 5. Stop Services

```bash
docker compose down
# With volume cleanup (DESTRUCTIVE):
docker compose down -v
```

---

## File Structure

```
backend/
├── Dockerfile                  # Multi-stage API build
├── Dockerfile.worker           # Multi-stage worker build
├── docker-compose.yml          # Production orchestration
├── docker-compose.override.yml # Local development overrides
├── .dockerignore               # Build context exclusions
├── .env.production             # Production env template
├── entrypoint.sh               # API startup script
├── worker-entrypoint.sh        # Worker startup script
├── app/
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── celery_app.py       # Celery configuration
│   │   └── config.py           # Settings management
│   ├── services/
│   │   └── reconciliation_service.py  # Business logic + async dispatch
│   └── workers/
│       └── reconciliation_worker.py    # Celery task definitions
├── migrations/                 # Alembic database migrations
└── requirements.txt            # Python dependencies
```

---

## Key Production Features

### 1. Multi-Stage Docker Builds

Both the API and worker use multi-stage builds to minimize image size:

- **Stage 1 (Builder)**: Installs system dependencies and Python packages
- **Stage 2 (Runtime)**: Copies only installed packages and application code

**Result**: ~300MB API image, ~350MB worker image (vs ~1.5GB single-stage).

### 2. Non-Root User

Both containers run as `appuser` (UID/GID created at build time) to reduce blast radius if compromised.

### 3. Health Checks

| Service | Check Method | Interval | Retries |
|---------|-------------|----------|---------|
| `api` | HTTP `/health` endpoint | 30s | 3 |
| `worker` | `celery inspect ping` | 30s | 3 |
| `postgres` | `pg_isready` | 10s | 5 |
| `redis` | `redis-cli ping` | 10s | 5 |

### 4. Resource Limits

All services have CPU and memory limits to prevent noisy neighbors:

| Service | CPU Limit | Memory Limit | CPU Reserve | Memory Reserve |
|---------|-----------|--------------|-------------|----------------|
| `api` | 2 cores | 1GB | 0.5 cores | 256MB |
| `worker` | 4 cores | 2GB | 1 core | 512MB |
| `postgres` | 2 cores | 2GB | 0.5 cores | 512MB |
| `redis` | 1 core | 512MB | 0.25 cores | 128MB |
| `flower` | 0.5 cores | 256MB | 0.1 cores | 64MB |

### 5. Redis Persistence & Memory Management

- **Persistence**: RDB snapshots (every 60s if 1+ keys changed, every 30s if 1000+ keys) + AOF every second
- **Memory Policy**: `allkeys-lru` - evicts least recently used keys when memory limit is reached
- **Max Memory**: 256MB with automatic eviction

### 6. PostgreSQL Configuration

- **InitDB Args**: UTF-8 encoding with en_US locale
- **Connection Pooling**: Application-side via SQLAlchemy `pool_pre_ping=True`, `pool_recycle=1800`
- **Port Binding**: `127.0.0.1:5432` only (not exposed to external network)

### 7. Celery Worker Configuration

```python
worker_prefetch_multiplier = 1      # One task per worker process at a time
task_acks_late = True               # Acknowledge after completion
task_reject_on_worker_lost = True   # Requeue if worker dies
broker_connection_retry_on_startup = True  # Auto-reconnect on startup
```

### 8. Environment Variable Management

- **`.env`**: Loaded by Docker Compose into all services
- **`.env.production`**: Template with documentation
- **Never committed**: Ensure `.env` is in `.gitignore`

### 9. Storage Architecture

```
/uploads-data volume
└── /app/storage/uploads/    <-- Shared between API and worker
    ├── company_file_1.csv
    └── processor_file_1.xlsx
```

Both API and worker mount the same named volume, ensuring files uploaded via the API are accessible to background workers.

### 10. CORS Configuration

Configured in `app/main.py` with environment-aware origins:

```python
origins = [
    "http://localhost:5500",   # Local dev
    "http://127.0.0.1:5500",   # Local dev alternate
    "https://lucilla-unvisionary-unadmissibly.ngrok-free.dev",  # Ngrok
]
# For production, add your actual domain
```

---

## Async Task Flow

```
Client Request
     |
     v
POST /api/reconciliation/{job_id}/run
     |
     v
ReconciliationService.enqueue()
     |
     +--[RECONCILIATION_MODE=sync]--> ReconciliationService.run() --> Response
     |
     +--[RECONCILIATION_MODE=async]--> Celery Task (redis://...)
                                         |
                                         v
                                   run_reconciliation_task
                                         |
                                         v
                                   ReconciliationService.run()
                                         |
                                         v
                                   Job marked COMPLETED
                                         |
                                   Notification sent
```

### Enabling Async Mode

Set in `.env`:

```env
RECONCILIATION_MODE=async
```

The API will:
1. Mark the job as `QUEUED`
2. Dispatch a Celery task to Redis
3. Return immediately with status `QUEUED`

The worker will:
1. Pick up the task from Redis
2. Mark the job as `PROCESSING`
3. Execute the reconciliation
4. Mark the job as `COMPLETED` or `FAILED`
5. Send notifications via the activity service

---

## Monitoring with Flower

Access Flower at `http://127.0.0.1:5555` (credentials from `.env`):

```bash
# Start with Flower
docker compose --profile monitoring up -d --build

# View logs
docker compose logs -f flower

# Check active tasks
curl -u admin:admin http://127.0.0.1:5555/api/tasks
```

---

## Common Operations

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f worker --tail 100

# Last 50 lines of all services
docker compose logs --tail 50
```

### Execute Commands

```bash
# Open shell in API container
docker compose exec api sh

# Run migrations
docker compose exec api alembic upgrade head

# Check Celery status
docker compose exec worker celery -A app.core.celery_app inspect active
docker compose exec worker celery -A app.core.celery_app inspect scheduled
```

### Rebuild After Code Changes

```bash
docker compose up -d --build
```

### Database Backup

```bash
docker compose exec postgres pg_dump -U recon recon > backup.sql
```

### Database Restore

```bash
docker compose exec -T postgres psql -U recon recon < backup.sql
```

### Scale Workers

```bash
# Run 4 worker instances
docker compose up -d --scale worker=4
```

---

## Security Hardening

1. **Secrets Management**: Use Docker secrets or a vault (HashiCorp Vault, AWS Secrets Manager) for production. Never hardcode secrets in images.
2. **Network Policies**: The bridge network isolates services. Add firewall rules for additional defense.
3. **TLS**: Terminate TLS at a reverse proxy (nginx, Caddy) in front of the API.
4. **Scanning**: Regularly scan images with `docker scout` or `trivy`.
5. **Updates**: Pin exact image digests and update regularly.

```bash
# Example with pinned digests
services:
  postgres:
    image: postgres@sha256:abc123...
```

---

## Troubleshooting

### Worker not picking up tasks

```bash
# Check Redis connectivity
docker compose exec worker python -c "import redis; r=redis.Redis(host='redis', password='...'); print(r.ping())"

# Check Celery status
docker compose exec worker celery -A app.core.celery_app inspect ping
```

### Database connection refused

```bash
# Verify Postgres is healthy
docker compose ps postgres
docker compose logs postgres

# Test connection from API
docker compose exec api python -c "
import psycopg2
conn = psycopg2.connect('postgresql://recon:recon@postgres:5432/recon')
print('Connected!')
conn.close()
"
```

### Volume permission issues

```bash
# Fix ownership
docker compose exec api chown -R appuser:appuser /app/storage
docker compose exec worker chown -R appuser:appuser /app/storage
```

---

## Performance Tuning

### API Server

- **Workers**: Start with `4` uvicorn workers. Scale based on CPU cores.
- **Workers formula**: `(2 x CPU cores) + 1`
- **Gunicorn alternative**: For higher load, consider `gunicorn` with `uvicorn.workers.UvicornWorker`.

### Celery Worker

- **Concurrency**: Start with `4` processes. Monitor with Flower.
- **Max tasks per child**: Set to `100` to prevent memory leaks.
- **Pool**: `solo` for local dev, `prefork` or `threads` for production (requires appropriate OS tuning).

### PostgreSQL

- **shared_buffers**: 25% of RAM
- **effective_cache_size**: 50-75% of RAM
- **maintenance_work_mem**: 10% of RAM
- **max_connections**: 200

### Redis

- Current config (256MB limit, allkeys-lru) is sufficient for task queuing.
- For high-throughput: Consider Redis Cluster or Redis Sentinel.
