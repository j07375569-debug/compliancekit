# Project State

**Last updated:** March 26, 2026

## Status: Pre-Launch — Backend Live, Frontend Upgraded (Not Yet Deployed)

### BUILT & WORKING
- Python stdlib HTTP server (server/app.py) — deployed on Railway, security-hardened
- SQLite database with schema + seed data + performance indexes (server/database.py)
- Full REST API: 12 GET, 8 POST, 1 PUT, 1 DELETE routes — with error handling
- Stripe integration: checkout sessions, customer portal, webhook handler
- React SPA dashboard (public/app.html) — light mode, error handling, XSS-safe
- Landing page (public/index.html) — light mode, mobile responsive, comparison table
- GitHub repo connected to Railway (auto-deploy on push)
- Stripe account created with 3 test products

### RECENTLY FIXED (This Session)
- Dark mode → light mode on BOTH landing and dashboard
- All gradients removed
- CORS locked to FRONTEND_URL (no more wildcard)
- Path traversal protection on static files
- Request body size limit (1MB)
- Security headers on all responses
- Input validation on control statuses
- DB write error handling with rollback
- Stripe error messages no longer leak config details
- Webhook requires signature secret
- N+1 query in controls page optimized
- 7 database indexes added
- API error handling on all frontend fetch calls
- XSS sanitization on policy content
- Mobile hamburger menu on landing page
- Empty states on dashboard pages

### BLOCKED
| Item | Blocker | Severity |
|------|---------|----------|
| Stripe payments | Price IDs not in Railway env vars | HIGH |
| Stripe webhooks | Webhook secret not configured | HIGH |
| User data isolation | No authentication system | HIGH |
| Database persistence | SQLite wiped on Railway restart | MEDIUM |
| Frontend hosting | Not deployed to Vercel yet | MEDIUM |
| Custom domain | Not purchased | LOW |
| Email system | No transactional emails | MEDIUM |

### FILE MAP
```
public/index.html  — Landing page (light mode, mobile responsive)
public/app.html    — React dashboard (light mode, error handling, XSS-safe)
server/app.py      — Backend server + API routes (security-hardened)
server/database.py — SQLite schema + seed + indexes
data/              — SQLite DB file
BLUEPRINT.md       — Full product spec
DESIGN-BLUEPRINT.md — Visual design system
.claude/           — Modular context system (Manus-inspired)
```

### INFRASTRUCTURE
| Service | Status | URL |
|---------|--------|-----|
| Backend (Railway) | LIVE (old code — push needed) | web-production-be130.up.railway.app |
| Frontend (Vercel) | NOT DEPLOYED | — |
| Payments (Stripe) | TEST MODE | Missing price IDs |
| Domain | NOT PURCHASED | — |
