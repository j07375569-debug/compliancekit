# ComplianceKit — Core Identity

You are building ComplianceKit, an AI-powered compliance SaaS for startups (5–100 employees). SOC 2, HIPAA, GDPR automation. Monthly Stripe subscriptions across 3 tiers.

## Permanent Rules

1. **No hand-holding.** Make decisions. Ship code. Explain after.
2. **Light mode only.** Enterprise trust = white backgrounds, Inter font, Tailwind gray palette, zero gradients.
3. **Zero dependencies on frontend.** Landing = vanilla HTML/CSS/JS. Dashboard = React via CDN. No build tools.
4. **Backend = Python stdlib only.** No Flask, no FastAPI. Pure `http.server` + SQLite.
5. **Never commit secrets.** All keys live in Railway env vars. `.env.example` only.
6. **Multi-agent validation.** Never self-review. Spawn a separate validator agent for all non-trivial changes.
7. **Ship ugly before shipping late.** Working > perfect. Iterate in public.

## Design Tokens (Non-Negotiable)

- Accent: #2563eb (blue-600) — buttons and links ONLY
- Text: #111827 / Secondary: #4b5563 / Muted: #9ca3af
- Borders: #e5e7eb / Hover: #d1d5db
- Radius: 12px cards, 8px buttons, 100px badges
- Only animation: fade-in on scroll (opacity 0→1, translateY 6px→0, 0.4s)

## Agent Loop Protocol (Manus-Inspired)

Every task follows this loop. No exceptions.

1. **ANALYZE** — Read `todo.md`, `project_state.md`, `session_log.md`. Understand what's needed.
2. **PLAN** — Write numbered steps into `todo.md`. This is your attention anchor. Recite it.
3. **EXECUTE** — One tool call per iteration. Complete one step, check it off in `todo.md`, move to next.
4. **EXTERNALIZE** — Never hold raw data in context. Write search results, API responses, large outputs to files. Keep only conclusions and next-action in working memory.
5. **VALIDATE** — Spawn a separate read-only validator agent for anything >50 lines or touching security/payments/schema.
6. **LOG** — Update `session_log.md` with what happened. Update `project_state.md` if blockers changed.

## Context Rules (from Manus Context Engineering)

- **File system IS your memory.** Don't try to remember — write it down. Save raw data to files, keep only summaries in context.
- **Append-only context.** Never rewrite previous actions or observations mid-session. Only append.
- **Restorable compression.** When dropping context: keep file paths and URLs. Content can be re-read. Paths cannot be re-invented.
- **todo.md is your attention anchor.** Recite it at the start of each iteration to stay focused. It's not a checklist — it's a steering mechanism.
- **Stable prefixes.** Don't put timestamps or volatile data at the top of prompts. Keep the top of any file static.

## Before Every Task

1. Read `.claude/todo.md` — your current plan
2. Read `.claude/project_state.md` — what's blocked
3. Read `.claude/session_log.md` — what happened last
4. Read relevant `.claude/rules/` and `.claude/prompts/` files
5. After completion: update `todo.md`, `session_log.md`, `project_state.md`
