# Tools & Services Reference

## Active Services

### Railway (Backend Hosting)
- Dashboard: railway.app
- App URL: https://web-production-be130.up.railway.app
- Auto-deploys from GitHub on push
- Env vars managed in Railway dashboard
- Required vars: PORT, FRONTEND_URL, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_STARTER, STRIPE_PRICE_GROWTH, STRIPE_PRICE_PRO

### Stripe (Payments)
- Mode: TEST
- Test key prefix: sk_test_51TF3ww...
- 3 products created: Starter ($49.99), Growth ($99.99), Pro ($149.99)
- Endpoints: /api/billing/checkout, /api/billing/portal, /api/billing/webhook
- Webhook events needed: checkout.session.completed, customer.subscription.updated, customer.subscription.deleted

### Vercel (Frontend Hosting — Pending)
- Config: vercel.json in project root
- Deploy: `npx vercel --prod` or connect GitHub repo
- Will serve: public/index.html and public/app.html

### GitHub (Code Repository)
- Connected to Railway for auto-deploy
- Push to main → Railway rebuilds

## API Base URL
- Production: https://web-production-be130.up.railway.app
- Local dev: http://localhost:3000
- Hardcoded in app.html — update if URL changes

## Database
- Engine: SQLite3
- File: data/compliancekit.db
- Auto-seeds demo data on first run
- WARNING: No persistence on Railway without volume mount
