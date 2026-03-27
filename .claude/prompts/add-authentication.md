# Prompt: Add Authentication

## Context
ComplianceKit currently has NO auth. Anyone visiting /app.html gets full dashboard access. This is the #1 blocker before real launch.

## Requirements
1. Email + password signup/login
2. Password hashing (use Python hashlib — no external deps)
3. Session tokens stored in cookies (httponly, secure)
4. New tables: users (id, email, password_hash, created_at), sessions (id, user_id, token, expires_at)
5. Middleware: check session token on all /api/* routes except /api/billing/webhook
6. Add user_id foreign key to: evidence, policies, subscriptions
7. Login page: centered card, white background, matches DESIGN-BLUEPRINT.md
8. Redirect unauthenticated users from /app.html to /login.html

## Multi-Agent Pattern
- Builder agent: implements auth in app.py, database.py, creates login.html
- Validator agent (read-only): reviews for security holes — SQL injection, timing attacks on password comparison, session fixation, missing CSRF protection
