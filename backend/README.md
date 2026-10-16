# 🚀 Control de Red Backend v9

Backend modular en Python para control de red vía ARP spoofing.

## 📁 Estructura

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuración
│   ├── api/                 # Endpoints REST
│   │   ├── __init__.py
│   │   ├── devices.py       # (Sesión 2)
│   │   └── windows.py       # (Futuro)
│   ├── services/            # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── scanner.py       # (Sesión 2)
│   │   └── arp_blocker.py   # (Sesión 3)
│   ├── models/              # Schemas y DB
│   │   ├── __init__.py
│   │   ├── database.py      # SQLAlchemy models ✅
│   │   └── device.py        # Pydantic schemas ✅
│   ├── utils/
│   │   └── __init__.py
│   └── tests/               # Tests (Sesión 4)
│       └── __init__.py
├── requirements.txt         # Dependencias ✅
├── .env.example            # Template config ✅
└── README.md               # Esta documentación
```

## ⚙️ Setup

### 1. Crear entorno virtual

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus valores
```

### 4. Ejecutar servidor

```bash
# Desde directorio backend/
python -m src.main

# O con uvicorn directamente
uvicorn src.main:app --reload
```

## 🌐 Endpoints

### Health Check
```bash
GET http://localhost:8000/
```

### Status
```bash
GET http://localhost:8000/api/status
```

### Documentación interactiva
```
http://localhost:8000/docs        # Swagger UI
http://localhost:8000/redoc       # ReDoc
```

## 🗄️ Base de Datos

SQLite (desarrollo):
- Archivo: `control_red.db` (auto-creado)
- 4 tablas: devices, schedules, audit_logs, network_scans
- Migrations: (futuro) Alembic

## 🧪 Tests

```bash
pytest
pytest --cov                # Con coverage
pytest -v                   # Verbose
```

## 🔧 Desarrollo

### Estado actual (Sesión 1 ✅)

- ✅ Estructura de carpetas
- ✅ FastAPI app base
- ✅ SQLAlchemy models (4 tablas)
- ✅ Pydantic schemas
- ✅ Configuración con Settings
- ✅ CORS configurado
- ✅ Logging configurado

### Próximos pasos (Sesión 2)

- ⏳ NetworkScanner service (ARP + nmap)
- ⏳ API endpoints /api/devices
- ⏳ Tests unitarios scanner

### Roadmap

- Sesión 2: Scanner + API (2h)
- Sesión 3: ARP Blocker (3h)
- Sesión 4: Tests completos (1.5h)

## 🔐 Seguridad

**ADVERTENCIA:** ARP spoofing es técnicamente un ataque MITM.

- ⚠️ Solo usar en redes propias
- ⚠️ Requiere permisos root/sudo
- ⚠️ Puede ser ilegal en redes ajenas

## 📝 Licencia

MIT - Héctor Alejandro Pérez (@halexespejo-cmd)

## 🆘 Troubleshooting

### Error: Module not found

```bash
# Asegúrate de estar en venv
source venv/bin/activate

# Reinstala dependencias
pip install -r requirements.txt
```

### Error: Permission denied (ARP)

```bash
# Ejecutar con sudo (solo cuando blocker esté implementado)
sudo -E venv/bin/python -m src.main
```

### Error: Database locked

```bash
# Eliminar DB y recrear
rm control_red.db
python -m src.main  # Recreará tablas
```

---

**Versión:** 9.0.0-dev.1  
**Última actualización:** 16 Octubre 2026
