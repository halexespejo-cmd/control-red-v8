# 🌐 Control de Red - Backend v9

[![Tests](https://github.com/halexespejo-cmd/control-red-v9-dev/actions/workflows/tests.yml/badge.svg)](https://github.com/halexespejo-cmd/control-red-v9-dev/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/badge/coverage-81.6%25-brightgreen)](https://github.com/halexespejo-cmd/control-red-v9-dev)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-9.0.0--dev.6-orange)](VERSION)

Backend modular en Python para control de red WiFi mediante ARP spoofing. Permite bloquear/desbloquear dispositivos, escanear red, y administrar acceso a internet desde una interfaz REST API.

**Autor:** Héctor Alejandro Pérez ([@halexespejo-cmd](https://github.com/halexespejo-cmd))

---

## ⚡ Quick Start

### Opción 1: Docker (Recomendado)

```bash
# Clonar repositorio
git clone https://github.com/halexespejo-cmd/control-red-v9-dev.git
cd control-red-v9-dev

# Levantar containers
docker-compose up -d

# Ver logs
docker-compose logs -f backend
```

**Hecho!** Backend disponible en `http://localhost:8000`

### Opción 2: Local (Desarrollo)

```bash
# Instalar dependencias
make install

# Run tests
make test

# Iniciar servidor
make run-dev
```

---

## 🏗️ Arquitectura

```
control-red-v9-dev/
├── backend/
│   ├── src/
│   │   ├── api/              # REST endpoints
│   │   │   └── devices.py
│   │   ├── services/         # Business logic
│   │   │   ├── scanner.py    # NetworkScanner (ARP + nmap)
│   │   │   └── arp_blocker.py # ARPBlocker (spoofing)
│   │   ├── models/           # DB models + Pydantic schemas
│   │   │   ├── database.py
│   │   │   └── device.py
│   │   ├── tests/            # 41 tests, 81.6% coverage
│   │   └── main.py           # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── Makefile
└── .github/workflows/        # CI/CD
```

---

## 🚀 Features

### ✅ Scanner de Red
- **ARP Scan:** Detecta dispositivos en la red local (scapy)
- **Vendor Lookup:** Identifica fabricante por MAC OUI
- **Categorización:** Router, TV, Phone, Laptop, IoT automático
- **Persistencia:** Guarda historial de escaneos en SQLite

### ✅ ARP Blocker
- **Bloqueo Real:** ARP spoofing continuo (paquetes cada 2s)
- **Threading:** 1 thread por dispositivo bloqueado
- **Restore Automático:** Al desbloquear o cerrar servidor
- **Seguro:** No bloquea router/self, validación pre-bloqueo

### ✅ REST API
- **10 Endpoints:** CRUD dispositivos, block/unblock, scan, network info
- **Async:** FastAPI + SQLAlchemy async
- **Rate Limiting:** 100 req/min (SlowAPI)
- **Documentación:** Swagger UI en `/docs`

### ✅ Production Ready
- **Docker:** Multi-stage build optimizado
- **CI/CD:** GitHub Actions (tests + lint)
- **Tests:** 41 tests, pytest, 81.6% coverage
- **Logs:** Structured logging
- **Health checks:** `/` endpoint

---

## 📡 API Endpoints

### Dispositivos

| Método | Endpoint | Descripción | Rate Limit |
|--------|----------|-------------|------------|
| `GET` | `/api/devices/` | Lista dispositivos | 50/min |
| `GET` | `/api/devices/{mac}` | Detalle dispositivo | 50/min |
| `PATCH` | `/api/devices/{mac}` | Actualizar nombre/categoría | 30/min |
| `POST` | `/api/devices/{mac}/block` | ⚠️ Bloquear (ARP spoofing) | 20/min |
| `POST` | `/api/devices/{mac}/unblock` | Desbloquear | 30/min |
| `POST` | `/api/devices/scan` | Escaneo manual | 10/min |
| `GET` | `/api/devices/network/info` | Info red actual | 30/min |
| `GET` | `/api/devices/blocked/active` | Bloqueos ARP activos | 30/min |

### Sistema

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/status` | Estado sistema + network |

**Documentación interactiva:** `http://localhost:8000/docs`

---

## 🧪 Testing

```bash
# Run all tests
make test

# Fast (sin coverage)
make test-fast

# Specific test file
cd backend && pytest src/tests/test_scanner.py -v
```

**Cobertura actual:** 81.6% (>80% ✅)

---

## 🔧 Desarrollo

### Comandos útiles (Makefile)

```bash
make help          # Ver todos los comandos
make install       # Setup completo
make run           # Iniciar backend
make run-dev       # Con hot reload
make test          # Tests + coverage
make format        # Black + isort
make lint          # Flake8
make check         # format + lint + test
make clean         # Limpiar cache
make docker-build  # Build imagen
make docker-up     # Levantar containers
make docker-logs   # Ver logs
```

### Pre-commit hooks

```bash
# Instalar hooks
pip install pre-commit
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

---

## ⚠️ Advertencia de Seguridad

**ARP spoofing es técnicamente un ataque MITM.**

- ✅ **Legal:** Solo en TU red
- ❌ **Ilegal:** En redes ajenas sin permiso
- 🔒 **Requiere:** Permisos root/sudo para scapy
- 📜 **Responsabilidad:** Usuario final

```bash
# Ejecutar con permisos (para ARP real)
sudo -E make run

# O con Docker (--cap-add=NET_ADMIN)
docker-compose up -d
```

---

## 📊 Tecnologías

- **FastAPI** 0.104 - Web framework async
- **SQLAlchemy** 2.0 - ORM async
- **Scapy** 2.5 - ARP spoofing
- **Pytest** 7.4 - Testing (41 tests)
- **Docker** - Containerización
- **GitHub Actions** - CI/CD

---

## 🗂️ Database Schema

**4 tablas (SQLite):**

1. **devices:** Dispositivos detectados (MAC, IP, vendor, category, is_blocked)
2. **schedules:** Horarios programados bloqueo (futuro)
3. **audit_logs:** Auditoría acciones (block/unblock/scan)
4. **network_scans:** Historial escaneos (devices_found, duration, timestamp)

---

## 📄 Licencia

MIT License - Héctor Alejandro Pérez

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea branch (`git checkout -b feature/amazing`)
3. Commit cambios (`git commit -m 'feat: add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Abre Pull Request

**Tests deben pasar** (make test) antes de PR.

---

## 📞 Contacto

- **GitHub:** [@halexespejo-cmd](https://github.com/halexespejo-cmd)
- **Email:** halexespejo@proton.me

---

**⭐ Si te fue útil, dale una estrella al repo!**
