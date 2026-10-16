# 🚂 DEPLOY A RAILWAY - GUÍA DE 5 MINUTOS

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/control-red-v9)

Control de Red backend production-ready en Railway con PostgreSQL + Redis incluidos.

---

## 📋 PRE-REQUISITOS

- ✅ Cuenta Railway (gratis: $5 crédito incluido)
- ✅ Cuenta GitHub (para conectar repo)
- ⏱️ **Tiempo:** 5 minutos

---

## 🚀 OPCIÓN 1: ONE-CLICK DEPLOY (RECOMENDADO)

### **Paso 1: Click al botón**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/control-red-v9)

### **Paso 2: Conecta GitHub**

Railway pedirá acceso a tu GitHub → **Autorizar**

### **Paso 3: Configura variables (auto)**

Railway detectará `railway.toml` y creará:
- ✅ PostgreSQL database
- ✅ Redis cache
- ✅ Environment variables
- ✅ Secret keys (auto-generated)

**No toques nada**, déjalo en defaults.

### **Paso 4: Deploy**

Click **"Deploy"** → Esperar 2-3 minutos

### **Paso 5: Obtén tu URL**

Una vez deployed:
1. Click en tu servicio
2. Pestaña **"Settings"** → **"Domains"**
3. Click **"Generate Domain"**
4. Copia tu URL: `https://control-red-production-XXXX.up.railway.app`

### **Paso 6: Verifica**

Abre tu URL en navegador:
```json
{
  "app": "control-red",
  "version": "9.0.0-dev.13",
  "status": "healthy"
}
```

✅ **¡Listo!** Tu backend está corriendo.

---

## 🔧 OPCIÓN 2: MANUAL (si quieres control)

### **Paso 1: Fork el repo**

```bash
# En tu terminal local
git clone https://github.com/halexespejo-cmd/control-red-v9-dev.git
cd control-red-v9-dev
```

### **Paso 2: Crear proyecto Railway**

1. Ve a [railway.app/new](https://railway.app/new)
2. Click **"Deploy from GitHub repo"**
3. Selecciona tu fork `control-red-v9-dev`
4. Railway auto-detecta `Dockerfile`

### **Paso 3: Agregar PostgreSQL**

En tu proyecto Railway:
1. Click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway crea variable `DATABASE_URL` automáticamente

### **Paso 4: Agregar Redis**

1. Click **"+ New"** → **"Database"** → **"Redis"**
2. Railway crea variable `REDIS_URL` automáticamente

### **Paso 5: Variables de entorno**

Railway Settings → Variables:

**Auto-generadas (Railway):**
- ✅ `DATABASE_URL` - PostgreSQL connection
- ✅ `REDIS_URL` - Redis connection
- ✅ `PORT` - Puerto asignado

**Agregar manualmente:**
```env
APP_NAME=control-red
DEBUG=false
LOG_LEVEL=INFO
VERSION=9.0.0-dev.13

# Security (click "Generate" en Railway UI)
SECRET_KEY=<railway-generated>
JWT_SECRET_KEY=<railway-generated>
```

### **Paso 6: Deploy**

Railway auto-deploys en cada `git push main`

Ver logs:
```bash
railway logs
```

---

## 🔐 VARIABLES DE ENTORNO

### **Requeridas (Railway auto-genera):**

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://default:pass@host:6379` |
| `PORT` | Puerto HTTP | `8000` |

### **Opcionales (mejorar experiencia):**

| Variable | Descripción | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Session encryption | (required) |
| `JWT_SECRET_KEY` | JWT tokens | (required) |
| `SENTRY_DSN` | Error tracking | (optional) |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## 🧪 TESTING LOCAL

### **Antes de deployar, probar localmente:**

```bash
# 1. Instalar dependencias
cd backend
pip install -r requirements.txt

# 2. Variables locales
cp .env.example .env
# Editar .env con tus valores

# 3. Levantar PostgreSQL + Redis (Docker)
cd ..
docker-compose up -d postgres redis

# 4. Run backend
cd backend
uvicorn src.main:app --reload

# 5. Verificar
curl http://localhost:8000/
```

---

## 📊 MONITOREO

### **Railway Dashboard:**

1. **Metrics:** CPU, RAM, Network
2. **Logs:** Real-time streaming
3. **Deployments:** Historial + rollback
4. **Usage:** Costos estimados

### **Health checks:**

Railway ejecuta:
```bash
GET https://tu-app.railway.app/
```

Cada 30 segundos. Si falla 3 veces → restart automático.

---

## 💰 COSTOS

### **Railway Free Tier:**

- ✅ $5 crédito inicial (gratis)
- ✅ ~500 horas compute/mes
- ✅ Domains HTTPS gratis
- ✅ GitHub auto-deploy

**Uso típico Control de Red:**
- Backend: ~$2-3/mes
- PostgreSQL: ~$2/mes
- Redis: ~$1/mes
- **Total: ~$5-6/mes**

**Free tier dura:** ~1 mes con crédito $5

### **Después del free tier:**

Opciones:
1. **Pagar Railway:** $5-10/mes (tarjeta crédito)
2. **Migrar a VPS:** DigitalOcean/Linode $5/mes
3. **Volver a local:** Docker Compose gratis

---

## 🐛 TROUBLESHOOTING

### **"Build failed"**

```bash
# Ver logs build
railway logs --deployment

# Causa común: requirements.txt missing
cd backend
pip freeze > requirements.txt
git add requirements.txt
git commit -m "fix: add requirements"
git push
```

### **"Database connection failed"**

Verificar `DATABASE_URL` está seteada:
```bash
railway variables
```

Si falta:
1. Asegurar PostgreSQL service creado
2. Railway Settings → restart service

### **"Port binding error"**

Railway inyecta variable `PORT`, asegúrate tu app la use:

```python
# src/main.py
import os
PORT = int(os.getenv("PORT", 8000))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
```

### **"ARP blocking not working"**

⚠️ **Normal en Railway:** Containers no tienen permisos `CAP_NET_ADMIN`

**Soluciones:**
1. **Local only:** ARP blocker requiere `sudo`
2. **VPS con Docker:** `--cap-add=NET_ADMIN`
3. **Railway:** Usar API externa (future feature)

---

## 🔄 UPDATES

### **Auto-deploy en cada push:**

```bash
# Local
git add .
git commit -m "feat: nueva feature"
git push origin main

# Railway detecta push → build → deploy automático
```

### **Rollback:**

Railway Dashboard → Deployments → Click deploy anterior → **"Redeploy"**

---

## 📞 SOPORTE

**Problemas con deploy:**
- GitHub Issues: [control-red-v9-dev/issues](https://github.com/halexespejo-cmd/control-red-v9-dev/issues)
- Railway Docs: [docs.railway.app](https://docs.railway.app)

**Telegram:**
- Bot: @Mi_red_control_bot
- DM: @halexespejo

---

## ✅ CHECKLIST POST-DEPLOY

Después de deployar, verifica:

- [ ] Health check: `GET /` retorna 200
- [ ] Database: `GET /api/devices/` retorna `[]` (vacío ok)
- [ ] Auth: `POST /api/auth/register` funciona
- [ ] WebSocket: `wss://tu-url/ws` conecta
- [ ] Logs: No errores en Railway dashboard
- [ ] Domain: HTTPS funcionando (Railway automático)

**Si todo ✅ → Conectar Telegram Mini App**

---

**Última actualización:** 16 Octubre 2026  
**Railway Template:** [railway.app/template/control-red-v9](https://railway.app/template/control-red-v9)
