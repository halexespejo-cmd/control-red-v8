# Deployment Guide

## Docker Production

### 1. Build & Run

```bash
docker-compose up -d
```

### 2. Environment Variables

```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:pass@postgres/controlred
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-32-chars-min
SENTRY_DSN=https://xxx@sentry.io/yyy
DEBUG=False
```

### 3. Database Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Create Admin User

```bash
docker-compose exec backend python -m src.scripts.create_admin
```

## Manual Deployment

### Requirements

- Python 3.10+
- PostgreSQL 14+
- Redis 7.0

### Steps

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env

# 3. Migrations
alembic upgrade head

# 4. Run
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# 5. Celery Worker
celery -A src.celery_app worker --loglevel=info

# 6. Celery Beat
celery -A src.celery_app beat --loglevel=info
```

## Nginx Configuration

```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name controlred.example.com;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Kubernetes

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: controlred-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: controlred
  template:
    metadata:
      labels:
        app: controlred
    spec:
      containers:
      - name: backend
        image: controlred:9.0.0-dev.11
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: controlred-secrets
              key: database-url
```

## Monitoring

### Prometheus

```yaml
scrape_configs:
  - job_name: 'controlred'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import dashboard ID: (to be published)
