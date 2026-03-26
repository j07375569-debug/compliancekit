# ComplianceKit — Product Blueprint
**Last updated:** March 26, 2026
**Status:** In active development — backend live, frontend QA in progress

---

## What This Is

ComplianceKit is an AI-powered compliance SaaS tool for small businesses and startups. It automates SOC 2, HIPAA, and GDPR compliance — evidence collection, policy generation, audit-ready reports — without requiring a compliance expert on staff.

**Target customer:** Early-stage startups (5–100 employees) who need compliance for enterprise deals or investor due diligence but can't afford a $50k/year compliance consultant.

**Business model:** Monthly SaaS subscription via Stripe. Three tiers.

---

## Pricing

| Plan | Shown Price | Strikethrough | Save |
|------|-------------|---------------|------|
| Starter | $49.99/mo | ~~$64.99/mo~~ | 23% |
| Growth | $99.99/mo | ~~$114.99/mo~~ | 13% |
| Pro | $149.99/mo | ~~$164.99/mo~~ | 9% |

All plans have CTA buttons linking to `/app.html` (the dashboard).

---

## Tech Stack

### Frontend
- **Landing page:** `/public/index.html` — Single-file HTML/CSS/JS, ~1,015 lines
  - MagicUI design language: particle canvas, blur-fade-in, shimmer borders, bento grid, number ticker, animated gradient text, marquee
  - ShadCN design tokens: zinc palette, Inter font
  - Zero dependencies — pure vanilla JS
- **App dashboard:** `/public/app.html` — Single-file React SPA, ~2,320 lines
  - React loaded via CDN (no build step)
  - Pages: Dashboard, Frameworks, Evidence, Alerts, Policies, Reports, Billing
  - API base URL hardcoded: `https://web-production-be130.up.railway.app`

### Backend
- **Server:** `/server/app.py` — Pure Python stdlib HTTP server, ~998 lines
  - No Flask, no FastAPI, no external dependencies
  - Serves static files from `/public/` directory
  - Full REST API at `/api/*`
- **Database:** `/server/database.py` — ~392 lines
  - SQLite (file-based, no database server needed)
  - Auto-seeds demo data on first run

### Infrastructure
| Service | Provider | URL / Status |
|---------|----------|--------------|
| Backend | Railway | `web-production-be130.up.railway.app` — **LIVE** |
| Frontend | Vercel | **NOT YET DEPLOYED** |
| Payments | Stripe | Test mode — keys set, price IDs missing |
| Domain | Namecheap | **NOT YET PURCHASED** |
| Code repo | GitHub | Connected to Railway (auto-deploy) |

---

## File Structure

```
ComplianceKit/
├── public/
│   ├── index.html          ← Landing page (marketing site)
│   └── app.html            ← React SPA dashboard
├── server/
│   ├── app.py              ← Python HTTP server + all API routes
│   └── database.py         ← SQLite schema + seed data
├── data/                   ← SQLite database file lives here
├── Procfile                ← Railway start command
├── nixpacks.toml           ← Railway build config
├── railway.json            ← Railway project config
├── vercel.json             ← Vercel deploy config
├── start.sh                ← Server startup script
├── DEPLOY.md               ← Deployment notes
├── landing.html            ← Old landing page (superseded, ignore)
└── BLUEPRINT.md            ← This file
```

---

## API Routes

### GET Endpoints
| Route | Description |
|-------|-------------|
| `/api/dashboard` | Dashboard stats summary |
| `/api/frameworks` | List all compliance frameworks |
| `/api/frameworks/:id` | Single framework detail |
| `/api/frameworks/:id/controls` | Controls for a framework |
| `/api/evidence` | All uploaded evidence |
| `/api/alerts` | Compliance alerts |
| `/api/policies` | Policy documents |
| `/api/activity` | Recent activity log |
| `/api/reports/compliance/:id` | Compliance audit report |
| `/api/billing/plans` | Available subscription plans |
| `/api/billing/subscription` | Current user subscription |

### POST Endpoints
| Route | Description |
|-------|-------------|
| `/api/controls/:id/status` | Update control pass/fail status |
| `/api/evidence` | Upload new evidence item |
| `/api/policies/generate` | AI-generate a policy document |
| `/api/frameworks/:id/subscribe` | Subscribe to a framework |
| `/api/alerts/:id/read` | Mark alert as read |
| `/api/billing/checkout` | Create Stripe checkout session |
| `/api/billing/portal` | Create Stripe customer portal session |
| `/api/billing/webhook` | Receive Stripe webhook events |

### PUT / DELETE
| Route | Description |
|-------|-------------|
| `PUT /api/policies/:id` | Update a policy |
| `DELETE /api/evidence/:id` | Delete an evidence item |

---

## Environment Variables (Railway)

These 7 variables must be set in Railway → Variables:

| Variable | Status | Value |
|----------|--------|-------|
| `PORT` | ✅ Set | 3000 |
| `FRONTEND_URL` | ✅ Set | Your Vercel URL (update after deploy) |
| `STRIPE_SECRET_KEY` | ✅ Set | `sk_test_51TF3ww...` (test mode) |
| `STRIPE_WEBHOOK_SECRET` | ⚠️ Placeholder | Need real value from Stripe Dashboard |
| `STRIPE_PRICE_STARTER` | ⚠️ Missing | Get from Stripe Dashboard → Products |
| `STRIPE_PRICE_GROWTH` | ⚠️ Missing | Get from Stripe Dashboard → Products |
| `STRIPE_PRICE_PRO` | ⚠️ Missing | Get from Stripe Dashboard → Products |

---

## Stripe Setup Status

- [x] Stripe account created
- [x] Test API keys obtained (`sk_test_...`)
- [x] 3 products created in Stripe Dashboard:
  - ComplianceKit Starter
  - ComplianceKit Growth
  - ComplianceKit Pro
- [ ] Price IDs collected (format: `price_XXXXX`) — **PENDING**
- [ ] Webhook endpoint registered in Stripe (`/api/billing/webhook`)
- [ ] Webhook secret added to Railway
- [ ] Switch to live mode keys before launch

---

## Landing Page Sections (index.html)

In order, top to bottom:

1. **Navigation** — Logo + links + "Start Free Trial" shimmer button
2. **Hero** — Blur-fade headline, animated gradient text, dual CTA buttons
3. **Product mockup** — Shine-border card with simulated dashboard UI
4. **Marquee** — Scrolling framework logos (SOC 2, HIPAA, GDPR, ISO 27001, PCI DSS, etc.)
5. **Bento grid features** — 6 feature cards with border-beam hover effect
6. **Number ticker stats** — 99.9% uptime, 500+ teams, 3 frameworks, 10x faster
7. **How it works** — 3-step visual (Connect → Analyze → Certify)
8. **Pricing** — 3 cards with strikethrough anchor pricing
9. **Testimonials** — 6 fake social proof cards
10. **CTA banner** — Shine-border gradient CTA section
11. **Footer** — Links, legal, copyright

---

## What's Done

- [x] Python backend server written
- [x] SQLite database with schema + seed data
- [x] Full REST API (12 GET, 8 POST, 1 PUT, 1 DELETE routes)
- [x] Stripe integration (checkout, portal, webhook handler)
- [x] React dashboard app (`app.html`) with 7 pages
- [x] MagicUI landing page built (`index.html`)
- [x] Strikethrough anchor pricing added
- [x] Backend deployed to Railway (live)
- [x] GitHub repo connected to Railway (auto-deploy on push)
- [x] Stripe account + 3 products created

---

## What's Left (In Order)

### 1. Stripe Price IDs (30 min)
Go to Stripe Dashboard → Products → each plan → copy the `price_XXXXX` ID.
Add all 3 to Railway environment variables.

### 2. Stripe Webhook (15 min)
In Stripe Dashboard → Developers → Webhooks → Add endpoint:
URL: `https://web-production-be130.up.railway.app/api/billing/webhook`
Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
Copy the signing secret → add as `STRIPE_WEBHOOK_SECRET` in Railway.

### 3. Landing Page QA + Bug Fix (1–2 hrs)
Finish reviewing `index.html` for:
- `@property --shimmer-angle` Firefox compatibility
- Number ticker with decimal (99.9) rendering correctly
- Price amounts not overflowing at 52px font size
- Mobile responsiveness
- All buttons link to `/app.html`

### 4. Push Latest Code to GitHub (5 min)
```bash
cd ~/Documents/Claude/Projects/k/ComplianceKit
git add -A
git commit -m "Landing page MagicUI redesign + app.html split"
git push
```

### 5. Deploy Frontend to Vercel (30 min)
```bash
cd ~/Documents/Claude/Projects/k/ComplianceKit
npx vercel --prod
```
Or connect GitHub repo at vercel.com/new.

### 6. Update Railway FRONTEND_URL (5 min)
After Vercel deploys, copy the `.vercel.app` URL and update the `FRONTEND_URL` variable in Railway.

### 7. Buy Domain on Namecheap (15 min)
Options:
- `compliancekit.com` — check availability
- `compliancekit.io` — likely available
- `getcompliancekit.com` — backup option

Budget: $10–15/year for .com, $30–50/year for .io

### 8. Point Domain to Vercel (15 min)
In Vercel: Settings → Domains → Add your domain
In Namecheap: Add Vercel's nameservers or CNAME record
Propagation: 5 min to 48 hours

### 9. Switch Stripe to Live Mode (before launch)
- Get live secret key (`sk_live_...`) from Stripe
- Update Railway `STRIPE_SECRET_KEY`
- Update Railway `STRIPE_PRICE_*` with live price IDs
- Re-register webhook with live mode

### 10. Launch
- Announce on Twitter, Reddit (r/entrepreneur, r/SaaS), Product Hunt
- Set up a basic email capture for leads

---

## Known Issues / Risks

| Issue | Severity | Notes |
|-------|----------|-------|
| No authentication | High | App has no login/signup — anyone who visits /app.html gets full access. Need auth before real launch. |
| SQLite on Railway | Medium | Railway restarts wipe the SQLite file. Need to mount a persistent volume or migrate to Postgres. |
| `@property` CSS not in Firefox | Low | Shimmer animation won't work in Firefox. Degrades gracefully. |
| Stripe in test mode | High | No real money collected until you switch to live keys. |
| No email system | Medium | No transactional emails (signup confirmation, invoice receipts, etc.) |
| Single-tenant database | High | All users share one SQLite DB. No user accounts = no data isolation. |

---

## Launch Checklist

- [ ] Stripe price IDs collected and in Railway
- [ ] Stripe webhook configured and verified
- [ ] Landing page QA complete, bugs fixed
- [ ] Latest code pushed to GitHub
- [ ] Frontend live on Vercel
- [ ] Custom domain purchased and pointed to Vercel
- [ ] Railway FRONTEND_URL updated
- [ ] Stripe switched to live mode
- [ ] Manual end-to-end test: visit site → click pricing → checkout completes
- [ ] Launch

---

*Built with: Python stdlib, SQLite, React CDN, Stripe API, Railway, Vercel*
