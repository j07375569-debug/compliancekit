# Security Rules

## Secrets Management
- ALL secrets in Railway environment variables. Never in code.
- .env.example shows variable names with placeholder values only.
- .gitignore must include: .env, *.db, __pycache__

## Current Gaps (Pre-Launch)
1. **No authentication** — /app.html is publicly accessible. Must add auth before real users.
2. **No user isolation** — Single SQLite DB, no user_id foreign keys. All data shared.
3. **CORS is wide open** — Currently allows all origins. Lock down to FRONTEND_URL before launch.
4. **Stripe in test mode** — No real money flows. Switch to live keys at launch.

## Before Launch Checklist
- [ ] Add authentication (email + password or OAuth)
- [ ] Add user_id to all tables, enforce row-level access
- [ ] Restrict CORS to production domain only
- [ ] Switch Stripe to live mode
- [ ] Add rate limiting to API
- [ ] Add HTTPS-only cookie flags
- [ ] Remove demo seed data from production
