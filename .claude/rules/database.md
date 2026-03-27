# Database Rules

## Engine
SQLite3 via Python stdlib. No ORM. Raw SQL only.

## Schema Location
All tables defined in `server/database.py` → `init_db()` function.

## Current Tables
- frameworks — compliance frameworks (SOC 2, HIPAA, GDPR)
- controls — individual controls within frameworks
- evidence — uploaded compliance evidence
- policies — generated policy documents
- alerts — compliance notifications
- activity — activity log entries
- subscriptions — Stripe subscription records

## Rules
1. All tables have `id INTEGER PRIMARY KEY AUTOINCREMENT`
2. All tables have `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
3. Use parameterized queries exclusively: `cursor.execute("SELECT * FROM t WHERE id = ?", (id,))`
4. Never use string concatenation or f-strings for SQL
5. Wrap writes in try/except with rollback
6. Demo data seeded in `seed_data()` — called automatically if tables are empty

## Known Issue
SQLite on Railway has no persistence. DB file gets wiped on deploy/restart.
Fix options: (a) mount Railway persistent volume, (b) migrate to Postgres.
