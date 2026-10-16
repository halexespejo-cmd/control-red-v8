# Troubleshooting

## Common Issues

### WebSocket Not Connecting

**Symptom:** Console error "WebSocket connection failed"

**Solutions:**
1. Check backend is running: `curl http://localhost:8000/`
2. Verify WebSocket endpoint: `curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8000/ws`
3. Check Nginx config (if using reverse proxy)

### Device Blocking Fails

**Symptom:** POST `/api/devices/{mac}/block` returns 500

**Solutions:**
1. Check root/sudo permissions: ARP spoofing requires elevated privileges
2. Verify network interface: `ip link show`
3. Check iptables rules: `sudo iptables -L`
4. Logs: `docker-compose logs backend`

### Scan Returns No Devices

**Symptom:** POST `/api/devices/scan` returns 0 devices

**Solutions:**
1. Verify network range: GET `/api/devices/network/info`
2. Check firewall blocking ICMP
3. Run manual scan: `sudo nmap -sn 192.168.1.0/24`

### Redis Connection Failed

**Symptom:** Error "Redis connection refused"

**Solutions:**
1. Start Redis: `docker-compose up -d redis` or `redis-server`
2. Check Redis port: `redis-cli ping` should return `PONG`
3. Verify REDIS_URL in .env

### JWT Token Expired

**Symptom:** 401 Unauthorized on protected routes

**Solutions:**
1. Login again: POST `/api/auth/login`
2. Check token expiry: DEFAULT 30 minutes
3. Verify SECRET_KEY is same across restarts

### High CPU Usage

**Symptom:** Server using 100% CPU

**Solutions:**
1. Check Celery tasks: `celery -A src.celery_app inspect active`
2. Verify no infinite loops in scan
3. Profile slow endpoints: `/metrics`
4. Scale workers: increase `--workers` flag

### Database Lock

**Symptom:** "database is locked" error (SQLite)

**Solutions:**
1. Switch to PostgreSQL for production
2. Reduce concurrent DB writes
3. Increase timeout: `PRAGMA busy_timeout = 10000`

## Logs

### Backend Logs

```bash
# Docker
docker-compose logs -f backend

# Direct
tail -f logs/app.log
```

### Celery Logs

```bash
docker-compose logs -f celery-worker
```

### Redis Logs

```bash
docker-compose logs -f redis
```

## Performance

### Slow API Response

**Check:**
1. Redis cache hit rate: `/metrics` → `redis_hits / redis_requests`
2. Database query time: Enable query logging
3. Network latency: Ping gateway

**Optimize:**
1. Add indexes: `CREATE INDEX idx_device_mac ON devices(mac);`
2. Increase cache TTL: 30s → 60s
3. Enable gzip compression

## Support

GitHub Issues: https://github.com/halexespejo-cmd/control-red-v9-dev/issues
