# 📝 CHANGELOG - Control de Red

Registro de cambios siguiendo [Conventional Commits](https://www.conventionalcommits.org/)

---

## [9.0.0-dev.1] - 2026-10-16

### 🎉 Changed
- **INICIO DESARROLLO v9**: Migración a arquitectura modular production-ready
- Creado sistema de versionado semántico (MAJOR.MINOR.PATCH-STAGE)
- Backup completo v8.0.0 preservado en `~/control-red-v8.0-backup/`

### ✅ Added
- `VERSION` - Archivo con número de versión actual
- `VERSION.md` - Documentación completa del sistema de versionado
- `CHANGELOG.md` - Este archivo
- Git repository inicializado en v9-dev

### 📋 Notes
- v8.0.0 sigue siendo la versión funcional demo
- v9-dev es copia de trabajo para desarrollo modular
- Próximo: Crear estructura backend Python (Día 1)

---

## [8.0.0] - 2026-10-11

### 🎊 Release
- **VERSIÓN FUNCIONAL BASE** (demo operativo)
- Score: 58.1/100
- Monolito HTML: 841 líneas (59.3 KB)

### ✅ Features
- Escaneo ARP de red local
- Bloqueo/desbloqueo dispositivos vía ARP spoofing
- Nombres personalizados (LocalStorage)
- Horarios programados (backend)
- Búsqueda en tiempo real
- Categorización automática (8 tipos dispositivos)
- 3 estilos de iconos (A/B/C)
- Modo oscuro/claro
- Bloqueo masivo
- Modales de confirmación
- Auto-refresh cada 15s

### 🏗️ Architecture
- Frontend: HTML + CSS + JavaScript vanilla
- Backend: API REST (Python/Node.js)
- Database: Server-side
- Deploy: GitHub Pages + raw.githack.com
- Telegram: WebApp SDK integrado

### 📦 Files
- `index.html` - App completa (841 líneas)
- `upload.sh` - Script deploy GitHub API

### 🌐 Endpoints
```
GET  /api/status
GET  /api/devices
POST /api/devices/{mac}/pause
POST /api/devices/{mac}/resume
GET  /api/windows
POST /api/windows
POST /api/windows/{id}/delete
```

### ⚠️ Known Issues
- Monolito difícil de mantener
- Sin TypeScript (bugs de tipos)
- Polling 15s en vez de WebSocket
- Sin tests automatizados
- Sin advertencia legal ARP spoofing
- Sin build system (HTML directo)

---

## Convenciones de Commits

```
feat:     Nueva funcionalidad
fix:      Corrección de bug
refactor: Cambio sin afectar funcionalidad
test:     Agregar/modificar tests
docs:     Documentación
style:    Formato, sin cambio de código
perf:     Mejora de performance
chore:    Tareas mantenimiento
build:    Cambios en build/dependencias
ci:       Cambios en CI/CD
```

**Ejemplos:**
```bash
git commit -m "feat: agregar WebSocket para updates en tiempo real"
git commit -m "fix: corregir escaneo ARP timeout en redes grandes"
git commit -m "refactor: separar scanner.py en módulo independiente"
git commit -m "test: agregar 15 tests para ARP blocker"
git commit -m "docs: actualizar README con instrucciones Docker"
git commit -m "perf: optimizar categorización de dispositivos (30% faster)"
git commit -m "chore: actualizar dependencias a últimas versiones"
```

---

## Versiones Futuras (Planeado)

### [9.0.0-dev.5] - Backend Completo
- Backend Python modular (FastAPI)
- Scanner service (ARP + nmap)
- ARP blocker con threads
- Database models (SQLAlchemy)
- Tests unitarios (pytest)

### [9.0.0-alpha.1] - Frontend Modular
- Migración a TypeScript
- Vite build system
- Componentes separados
- Tests frontend (Jest)

### [9.0.0-beta.1] - WebSocket + Tests
- WebSocket backend
- WebSocket frontend
- 80+ tests (coverage >80%)
- E2E tests (Playwright)

### [9.0.0-rc.1] - Pre-Release
- Docker + docker-compose
- CI/CD (GitHub Actions)
- Deploy Railway/Render
- Advertencia legal compliance
- Documentación completa

### [9.0.0] - Release Production
- Score objetivo: 90+/100
- Production-ready
- Deploy estable
- Monitoreo + logs

---

**Autor:** Héctor Alejandro Pérez (@halexespejo-cmd)  
**Proyecto:** Control de Red - Telegram Mini App  
**Licencia:** MIT
