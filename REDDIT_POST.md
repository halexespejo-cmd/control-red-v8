# Reddit Post - r/homelab

**Title:**  
[Show r/homelab] Free Fing alternative - WiFi control via Telegram Mini App

---

**Body:**

Hey homelab!

I built a **free network control tool** that lets you manage WiFi devices from Telegram. Think Fing, but self-hosted and $0/month.

## 🌐 What it does

- **Scan network** via ARP (discovers all devices in seconds)
- **Block/unblock devices** with one tap (ARP spoofing)
- **Real-time updates** via WebSocket (< 1s latency)
- **Schedule access** for parental controls
- **Telegram native** - no app to install

## 🔧 Tech Stack

- **Backend:** FastAPI + PostgreSQL + Redis + Celery
- **Frontend:** Telegram Mini App (HTML5)
- **Deploy:** Docker Compose or 1-click Railway
- **Tests:** 94 tests, 81.6% coverage
- **Score:** 95.6/100 production-ready

## 🚀 Why I built this

Fing Premium costs $9/month. I wanted:
1. **Free forever** (self-hosted)
2. **Zero friction** (Telegram, no app install)
3. **Privacy-first** (your data stays on YOUR server)

## 📦 Try it (5 minutes)

**Option 1: Railway (recommended)**
1. Click: https://railway.app/template/control-red-v9
2. Wait 3 minutes
3. Open Telegram bot: @Mi_red_control_bot
4. /start → Connect your backend → Scan

**Option 2: Docker**
```bash
git clone https://github.com/halexespejo-cmd/control-red-v9-dev.git
cd control-red-v9-dev
docker-compose up -d
```

## ⚠️ Legal disclaimer

Uses ARP spoofing (technically MITM). **Legal only on YOUR network**. Use responsibly.

## 🎯 Looking for beta testers

**50 spots** for early feedback. If you try it:
- ✅ What worked well?
- ❌ What broke?
- 💡 What features would you pay for?

## 📊 Demo

Video (90s): [YouTube link]  
Screenshots: [imgur album]  
Live bot: @Mi_red_control_bot

## 💬 AMA

Spent 3.5 hours optimizing this from 93→95.6 score yesterday. Happy to answer:
- Architecture decisions
- Why FastAPI over Django
- How ARP blocking works
- Deployment strategies
- Monetization ideas

**GitHub:** https://github.com/halexespejo-cmd/control-red-v9-dev  
**Tech docs:** https://github.com/halexespejo-cmd/control-red-v9-dev/blob/main/README.md

---

*Mods: Let me know if this violates any rules. Happy to adjust.*

---

## Expected Response Strategy

### Positive Comments:
**"This is cool! Just deployed."**  
→ "Awesome! Let me know if you hit any issues. Also curious which features you'd use most."

### Skeptical:
**"Why not just use Fing?"**  
→ "Fing is great! Main differences:  
• Fing: $9/mo, SaaS, polished  
• This: $0, self-hosted, privacy-first  
Both valid. If you value control/cost, this works."

### Technical Questions:
**"How does ARP spoofing work?"**  
→ [Detailed explanation with links to docs]

### Bug Reports:
**"Railway deploy failed"**  
→ "Thanks for trying! Can you share error logs? (GitHub issue or DM). Will fix ASAP."

### Feature Requests:
**"Can it do X?"**  
→ "Not yet, but great idea. Added to roadmap: [GitHub issues link]"

---

## Post-Launch Actions

**Hour 1-2:**
- Monitor every 15 min
- Respond to ALL comments (< 30 min)
- Fix critical bugs in real-time

**Hour 3-6:**
- Pin best comment thread
- Edit post with FAQ section
- Cross-post to r/selfhosted (if allowed)

**Day 2-3:**
- Thank everyone
- Share stats (X users deployed)
- Tease next features

---

**Post Time:** Sunday 08:00 AM CST  
**Subreddit:** r/homelab (~250K subscribers)  
**Flair:** [PROJECT]
