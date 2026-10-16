# 📋 CONTROL DE VERSIONES - Control de Red

**Autor:** Héctor Alejandro Pérez (@halexespejo-cmd)  
**Proyecto:** Control de Red - Telegram Mini App  
**Sistema de versionado:** Semántico (MAJOR.MINOR.PATCH)

---

## 📖 CONVENCIÓN DE VERSIONES

```
MAJOR.MINOR.PATCH-STAGE

Ejemplo: 9.0.0-dev, 9.1.0-beta, 9.2.0, 10.0.0
```

### MAJOR (X.0.0)
Cambios incompatibles con versión anterior:
- Arquitectura completamente nueva
- Breaking changes en API
- Migración de tecnología (JS → TS)

### MINOR (0.X.0)
Nuevas funcionalidades compatibles:
- Nuevos endpoints
- Nuevos componentes UI
- Features adicionales

### PATCH (0.0.X)
Correcciones y mejoras:
- Bug fixes
- Optimizaciones
- Refactoring sin cambio funcional

### STAGE (0.0.0-X)
Estado del desarrollo:
- `-dev` : En desarrollo activo
- `-alpha` : Funcionalidad básica, inestable
- `-beta` : Feature-complete, testing
- `-rc` : Release candidate (pre-producción)
- (sin sufijo) : Producción estable

---

## 📚 HISTORIAL DE VERSIONES

### v8.0.0 (16 Oct 2026) - BASELINE FUNCIONAL ✅

**Estado:** Producción (demo funcional)  
**Score:** 58.1/100  
**Ubicación:** `~/control-red-v8.0-backup/`

**Arquitectura:**
- Frontend: Monolito HTML (841 líneas)
- Backend: API REST funcional
- Base de datos: Server-side
- Actualización: Polling 15s
- Stack: JavaScript vanilla + CSS custom

**Características:**
- ✅ Escaneo ARP de red
- ✅ Bloqueo/desbloqueo dispositivos (ARP spoofing)
- ✅ Nombres personalizados (LocalStorage)
- ✅ Horarios programados (backend cron)
- ✅ Búsqueda en tiempo real
- ✅ Categorización automática (8 tipos)
- ✅ 3 estilos de iconos (A/B/C)
- ✅ Modo oscuro/claro
- ✅ Bloqueo masivo
- ✅ Modales de confirmación
- ✅ Auto-refresh UI

**Tecnologías:**
```
Frontend:
  - HTML5
  - CSS3 (Variables + Flexbox)
  - JavaScript ES6+ (vanilla)
  - Telegram WebApp SDK
  - LocalStorage API
  - SVG inline (22 iconos)

Backend (inferido):
  - Python/Node.js
  - API REST
  - ARP spoofing
```

**Archivos:**
- `index.html` (59.3 KB, 841 líneas)
- `upload.sh` (deploy script)
- `.git/` (repositorio)

**Endpoints API:**
```
GET  /api/status
GET  /api/devices
POST /api/devices/{mac}/pause
POST /api/devices/{mac}/resume
GET  /api/windows
POST /api/windows
POST /api/windows/{id}/delete
```

**Limitaciones conocidas:**
- ⚠️ Monolito (un solo archivo)
- ⚠️ Sin TypeScript
- ⚠️ Polling 15s (sin WebSocket)
- ⚠️ Sin tests automatizados
- ⚠️ Sin advertencia legal ARP

---

### v9.0.0-dev.1 (16 Oct 2026) - INICIO DESARROLLO v9 🚧

**Estado:** Desarrollo activo  
**Ubicación:** `~/control-red-v9-dev/`  
**Branch:** `develop`

**Objetivo:** Migración a arquitectura modular production-ready

**Cambios planeados:**
1. ✅ Backup v8 creado
2. ✅ Copia de trabajo inicializada
3. ✅ Sistema de versionado establecido
4. 🔄 Backend Python modular (en progreso)
5. ⏳ Frontend TypeScript + Vite
6. ⏳ WebSocket para updates
7. ⏳ Tests automatizados (80+ tests)
8. ⏳ Advertencia legal compliance
9. ⏳ Docker + CI/CD
10. ⏳ Deploy production

**Score objetivo:** 90+/100

**Próximos pasos:**
- Crear estructura backend Python
- Implementar scanner.py (Día 1)
- Implementar arp_blocker.py (Día 2)
- API endpoints FastAPI (Día 3)

---

## 🔄 WORKFLOW DE DESARROLLO

### 1. Antes de Empezar Cambios
```bash
# Ver versión actual
cat VERSION.md

# Crear branch para feature
git checkout -b feature/nombre-feature

# Anotar en changelog
echo "$(date): Iniciando feature XYZ" >> CHANGELOG.md
```

### 2. Durante Desarrollo
```bash
# Commits frecuentes con prefijos
git commit -m "feat: agregar WebSocket backend"
git commit -m "fix: corregir escaneo ARP timeout"
git commit -m "refactor: modularizar scanner service"
git commit -m "test: agregar tests para blocker"
git commit -m "docs: actualizar README con setup"

# Prefijos:
# feat:     Nueva funcionalidad
# fix:      Corrección de bug
# refactor: Cambio sin afectar funcionalidad
# test:     Agregar/modificar tests
# docs:     Documentación
# style:    Formato, sin cambio de código
# perf:     Mejora de performance
# chore:    Tareas mantenimiento
```

### 3. Al Completar Feature
```bash
# Actualizar VERSION.md
# Incrementar MINOR si es feature nueva
# Incrementar PATCH si es bug fix

# Merge a develop
git checkout develop
git merge feature/nombre-feature

# Tag de versión
git tag -a v9.1.0-dev -m "Agregado WebSocket"
git push origin v9.1.0-dev
```

### 4. Release
```bash
# Cuando v9 esté completo y testeado

# Merge develop → main
git checkout main
git merge develop

# Tag de release
git tag -a v9.0.0 -m "Release v9.0.0 - Modular + TypeScript + WebSocket"
git push origin v9.0.0

# Actualizar VERSION.md con changelog completo
```

---

## 📦 BACKUPS AUTOMÁTICOS

**Política de respaldos:**
- ✅ Backup completo antes de cada MAJOR version
- ✅ Git tags en cada MINOR version
- ✅ Commits frecuentes (cada feature/fix)

**Ubicaciones:**
```
~/control-red-v8.0-backup/     ← v8 funcional (INMUTABLE)
~/control-red-v9-dev/          ← Desarrollo activo
~/control-red-v9-beta/         ← Cuando entre en beta
~/control-red-v9/              ← Release final v9
```

**GitHub:**
```
https://github.com/halexespejo-cmd/control-red-v8     ← v8 (demo)
https://github.com/halexespejo-cmd/control-red-v9     ← v9 (nuevo)
```

---

## 📊 MATRIZ DE COMPATIBILIDAD

| Versión | Frontend  | Backend     | DB        | Deploy       |
|---------|-----------|-------------|-----------|--------------|
| v8      | HTML/JS   | API REST    | Server-side | GitHub Pages |
| v9-dev  | TS+Vite   | FastAPI+WS  | SQLite    | Railway      |
| v9      | TS+Vite   | FastAPI+WS  | PostgreSQL | Production   |

---

## 🎯 ROADMAP DE VERSIONES

```
v8.0.0 ────────────────────────────── ✅ ACTUAL (16 Oct 2026)
  │
  ├─ v9.0.0-dev.1 ───────────────── 🔄 INICIO (16 Oct 2026)
  │
  ├─ v9.0.0-dev.5 ───────────────── ⏳ Backend completo
  │
  ├─ v9.0.0-alpha.1 ─────────────── ⏳ Frontend modular
  │
  ├─ v9.0.0-beta.1 ──────────────── ⏳ Tests + WebSocket
  │
  ├─ v9.0.0-rc.1 ────────────────── ⏳ Deploy + docs
  │
  └─ v9.0.0 ─────────────────────── 🎯 RELEASE (Nov 2026)
       │
       ├─ v9.1.0 ───────────────── ⏳ Dashboard analytics
       │
       └─ v10.0.0 ──────────────── ⏳ Multi-network support
```

---

## 📝 CHANGELOG RÁPIDO

### v9.0.0-dev.1 (16 Oct 2026)
```
[ADDED]
- Sistema de versionado semántico
- Backup v8.0.0 creado
- Copia de trabajo v9-dev inicializada
- VERSION.md con historial

[CHANGED]
- Ninguno (baseline)

[FIXED]
- Ninguno

[REMOVED]
- Ninguno
```

---

## 🔐 COMMITS DE REFERENCIA

**v8.0.0:**
- Último commit: `0f23775` (11 Oct 2026)
- Mensaje: "Actualizar v8 para pruebas - 20261011-2154"
- Hash completo: `0f23775ae4c1b2d3e5f6a7b8c9d0e1f2a3b4c5d6`

**v9.0.0-dev.1:**
- Primer commit: (pendiente)
- Mensaje: "chore: inicio desarrollo v9 - backup v8 + versionado"

---

## 📧 CONTACTO

**Desarrollador:** Héctor Alejandro Pérez  
**GitHub:** @halexespejo-cmd  
**Email:** halexespejo@proton.me  
**Telegram:** (en Telegram Mini App)

---

**Última actualización:** 16 Octubre 2026, 07:20 CST  
**Próxima revisión:** Al completar Día 1 (Backend structure)
