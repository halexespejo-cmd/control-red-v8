# API Reference

**Base URL:** `http://localhost:8000`  
**WebSocket:** `ws://localhost:8000/ws`

---

## 🔐 Authentication

### POST `/api/auth/register`

Register new user.

**Request:**
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securepass123",
  "is_admin": false
}
```

**Response:** `201 Created`
```json
{
  "username": "testuser",
  "email": "test@example.com"
}
```

---

### POST `/api/auth/login`

Login and get JWT token.

**Request:**
```json
{
  "username": "testuser",
  "password": "securepass123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

### GET `/api/auth/me`

Get current user info.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "sub": "testuser",
  "user_id": 1,
  "role": "user"
}
```

---

## 📡 Devices

### GET `/api/devices/`

List all devices.

**Query params:**
- `category` (optional): Filter by category
- `status` (optional): Filter by status
- `skip` (default 0): Pagination offset
- `limit` (default 100): Page size

**Response:** `200 OK`
```json
[
  {
    "mac": "AA:BB:CC:DD:EE:FF",
    "ip": "192.168.1.100",
    "hostname": "laptop-work",
    "vendor": "Apple Inc.",
    "category": "Laptop",
    "is_blocked": false,
    "is_whitelisted": false,
    "first_seen": "2024-10-16T10:00:00",
    "last_seen": "2024-10-16T15:30:00"
  }
]
```

---

### GET `/api/devices/{mac}`

Get specific device.

**Response:** `200 OK`
```json
{
  "mac": "AA:BB:CC:DD:EE:FF",
  "ip": "192.168.1.100",
  "hostname": "laptop-work",
  "vendor": "Apple Inc.",
  "category": "Laptop",
  "is_blocked": false
}
```

---

### POST `/api/devices/scan`

Trigger network scan.

**Response:** `200 OK`
```json
{
  "ok": true,
  "scan_id": "scan_20241016_153045",
  "devices_found": 15,
  "duration": 8.5,
  "network": "192.168.1.0/24",
  "timestamp": "2024-10-16T15:30:45"
}
```

---

### POST `/api/devices/{mac}/block`

Block device via ARP spoofing.

**Response:** `200 OK`
```json
{
  "ok": true,
  "message": "Device blocked successfully",
  "mac": "AA:BB:CC:DD:EE:FF",
  "ip": "192.168.1.100"
}
```

---

### POST `/api/devices/{mac}/unblock`

Unblock device.

**Response:** `200 OK`
```json
{
  "ok": true,
  "message": "Device unblocked successfully",
  "mac": "AA:BB:CC:DD:EE:FF"
}
```

---

### PATCH `/api/devices/{mac}`

Update device properties.

**Request:**
```json
{
  "category": "Smartphone",
  "is_whitelisted": true
}
```

**Response:** `200 OK`

---

### GET `/api/devices/network/info`

Get network information.

**Response:** `200 OK`
```json
{
  "ok": true,
  "gateway": "192.168.1.1",
  "my_ip": "192.168.1.50",
  "network_range": "192.168.1.0/24",
  "ssid": "MyWiFi",
  "public_ip": "203.0.113.45"
}
```

---

## 🔄 Background Tasks

### POST `/api/tasks/scan`

Trigger async network scan (Celery).

**Response:** `200 OK`
```json
{
  "task_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "pending"
}
```

---

### GET `/api/tasks/{task_id}`

Check task status.

**Response:** `200 OK`
```json
{
  "task_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "SUCCESS",
  "result": {
    "devices_found": 15
  }
}
```

---

## 📊 Observability

### GET `/`

Health check.

**Response:** `200 OK`
```json
{
  "app": "Control de Red Backend",
  "version": "9.0.0-dev.11",
  "status": "running",
  "debug": false,
  "driver": "scapy"
}
```

---

### GET `/api/status`

API status.

**Response:** `200 OK`
```json
{
  "ok": true,
  "driver": "scapy",
  "gateway": "192.168.1.1",
  "my_ip": "192.168.1.50"
}
```

---

### GET `/metrics`

Prometheus metrics.

**Response:** `200 OK` (text/plain)
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/devices/"} 42.0
```

---

## 🔌 WebSocket

### Connection

**URL:** `ws://localhost:8000/ws`  
**Auth (optional):** `ws://localhost:8000/ws?token=<jwt_token>`

### Client → Server Messages

#### Ping

```json
{
  "type": "ping"
}
```

**Response:**
```json
{
  "type": "pong"
}
```

#### Subscribe

```json
{
  "type": "subscribe"
}
```

**Response:**
```json
{
  "type": "subscribed",
  "message": "Subscribed to real-time updates"
}
```

### Server → Client Events

#### Connection Established

```json
{
  "type": "connection_established",
  "message": "Connected to Control de Red WebSocket",
  "user_id": "testuser"
}
```

#### Scan Events

```json
{
  "type": "scan_event",
  "status": "scan_started",
  "timestamp": "2024-10-16T15:30:00",
  "data": {
    "message": "Network scan initiated"
  }
}
```

```json
{
  "type": "scan_event",
  "status": "scan_completed",
  "timestamp": "2024-10-16T15:30:15",
  "data": {
    "devices_found": 15,
    "scan_id": "scan_20241016_153000"
  }
}
```

#### Device Events

```json
{
  "type": "device_discovered",
  "timestamp": "2024-10-16T15:30:10",
  "data": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "ip": "192.168.1.100",
    "vendor": "Apple Inc."
  }
}
```

```json
{
  "type": "device_blocked",
  "timestamp": "2024-10-16T15:32:00",
  "data": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "ip": "192.168.1.100"
  }
}
```

#### Heartbeat

```json
{
  "type": "heartbeat",
  "timestamp": "2024-10-16T15:30:00"
}
```

---

## 📝 Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid MAC address format"
}
```

### 401 Unauthorized

```json
{
  "detail": "Invalid credentials"
}
```

### 403 Forbidden

```json
{
  "detail": "Admin access required"
}
```

### 404 Not Found

```json
{
  "detail": "Device not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

---

## 🔑 Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/` | 100 req/min |
| `/api/status` | 50 req/min |
| `/api/devices/` | 100 req/min |
| `/api/devices/scan` | 10 req/min |
| `/api/auth/login` | 20 req/min |

---

For architectural details, see [Architecture](architecture.md).
