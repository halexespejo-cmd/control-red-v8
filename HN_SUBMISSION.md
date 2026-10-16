# Hacker News Submission

**Title:**  
Show HN: Control WiFi from Telegram (self-hosted Fing alternative, 95% test coverage)

**URL:**  
https://github.com/halexespejo-cmd/control-red-v9-dev

---

## HN Comment (First Comment Strategy)

**Posted immediately after submission:**

Hey HN! I'm the developer.

**What:** Free Fing alternative that runs as Telegram Mini App. Scan network, block devices, schedule access - all from Telegram.

**Why I built it:**

Was paying $9/month for Fing Premium just to block my roommate's Xbox at night. Thought "this should be free and self-hostable."

3 months later: FastAPI backend, 81.6% test coverage, WebSocket real-time, 1-click Railway deploy.

**Tech highlights:**

- ARP spoofing for device blocking (requires sudo/Docker)
- PostgreSQL + Redis + Celery for background tasks
- Telegram Mini App = zero app install friction
- 95.6/100 production score (tests, CI/CD, docs, monitoring)

**Try it (5 min):**

Railway: https://railway.app/template/control-red-v9  
Or Docker: `docker-compose up -d`

Bot: @Mi_red_control_bot

**Looking for:**

- Beta testers (especially homelab folks)
- Feedback on monetization (managed hosting vs 100% free?)
- Ideas for features (speed tests? WiFi heatmaps?)

**Legal note:** Uses ARP spoofing (MITM technique). Legal only on YOUR network. Disclaimer in docs.

Happy to answer questions about:
- Why FastAPI over Flask/Django
- How ARP blocking works under the hood
- Telegram Mini Apps (underrated platform IMO)
- Self-hosting strategies
- Building to 95% test coverage

---

## HN Response Playbook

### Skeptics (common on HN)

**"ARP spoofing is a security risk"**  
→ "You're right. That's why it's local-only, requires explicit permissions, and includes legal warnings. Same technique Fing uses. Alternative would be router API integration (roadmap)."

**"Just use iptables/nftables"**  
→ "Correct, iptables is more robust. This trades technical complexity for UX simplicity. Target audience: non-sysadmins who want point-and-click control."

**"Why Telegram?"**  
→ "Fair question. Benefits:  
• 1B users, no app install  
• Push notifications free  
• Mini Apps = web tech, fast iteration  
• Privacy (self-hosted bot)  
Downside: Platform risk. Considering native apps v2."

**"This is just a Fing clone"**  
→ "Inspired by Fing, yes. Key differences:  
• Open roadmap (users vote features)  
• Self-hosted (privacy)  
• $0 forever (if you host)  
Not trying to compete with Fing's polish, but serve different audience."

### Technical Deep Dives

**"How does device identification work?"**  
→ "OUI (Organizationally Unique Identifier) lookup via MAC address. Maintains local database of ~30K vendor prefixes. Then heuristics (port scan, mDNS) for device type. Details: [link to code]"

**"95% test coverage - how?"**  
→ "pytest + pytest-asyncio + Playwright for E2E.  
Breakdown:  
• Unit: services, models (fast, ~60% coverage)  
• Integration: API endpoints (20%)  
• E2E: full user flows (15%)  
Took ~40 hours to reach 80%, diminishing returns after."

**"Why PostgreSQL instead of SQLite?"**  
→ "SQLite for v1-8. Migrated v9 for:  
• Better concurrent writes (Celery tasks)  
• Production-ready (Railway managed)  
• Future: Multi-tenant SaaS  
SQLite still works great for self-hosted single-user."

### Feature Requests

**"Can it do speed tests?"**  
→ "Roadmap! Week 3-4. Using iperf3 + speedtest-cli. Want any specific metrics?"

**"Support for multiple networks?"**  
→ "High priority. Current: 1 network/instance. v9.1: Multi-network with switch UI. ETA 4-6 weeks."

### Offers to Help

**"I'd like to contribute"**  
→ "Amazing! Best way:  
1. Try it, file issues (especially UX friction)  
2. Check 'good first issue' label: [link]  
3. Join Telegram group: @control_red_dev (new)  
Most wanted help: frontend redesign, router API integrations."

---

## Success Metrics

**Tier 1 (Realistic):**
- 100+ points (front page)
- 30+ comments
- 5+ GitHub stars during HN time
- 1-2 technical discussions

**Tier 2 (Optimistic):**
- Top 10 front page
- Feature in HN newsletter
- 50+ comments
- 20+ stars
- 1+ journalist reach out

**Tier 3 (Dream):**
- #1 for 1+ hour
- 100+ stars
- Viral on Twitter
- VC cold email (lol)

---

## Timing Strategy

**Best times HN (CST):**
- Sunday 8-10am (10-12am UTC) ← RECOMMENDED
- Weekday 8-9am (before work)
- Weekday 12-1pm (lunch)

**Avoid:**
- Friday evening (dead zone)
- Saturday (low activity)
- Major holidays

---

## Post-Submission Actions

**Minutes 1-30 (CRITICAL):**
- Refresh every 5 min
- Respond to EVERY comment (< 10 min)
- Upvote good questions (drives engagement)
- Fix typos in first comment

**Hour 1-3:**
- Deep technical answers (show expertise)
- Link to docs/code generously
- Stay humble ("still learning X")
- Acknowledge all criticism

**Hour 4-12:**
- Slower responses ok (30 min window)
- Batch similar questions
- Update GitHub README with FAQ

**Day 2:**
- Thank you comment
- Stats update ("20 deploys in 24h")
- Tease next feature based on feedback

---

**Submit Time:** Sunday 10:00 AM CST (12:00 PM UTC)  
**URL:** https://github.com/halexespejo-cmd/control-red-v9-dev  
**Title:** Show HN: Control WiFi from Telegram (self-hosted Fing alternative, 95% test coverage)

**Max title length:** 80 chars (current: 79 ✅)
