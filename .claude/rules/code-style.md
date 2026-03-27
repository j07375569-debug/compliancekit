# Code Style Rules

## Python (Backend)
- Pure stdlib only. No pip packages. No requirements.txt.
- Snake_case for functions and variables.
- Classes for database models, functions for route handlers.
- All routes registered in `setup_routes()` in app.py.
- SQL queries use parameterized strings (? placeholders). Never f-strings for SQL.
- Error responses: `{"error": "message"}` with appropriate HTTP status codes.
- CORS headers on every response via `do_OPTIONS` and `end_headers` override.

## HTML/CSS/JS (Frontend)
- Single-file architecture. No separate .css or .js files.
- Landing page: vanilla JS only. Zero npm dependencies.
- Dashboard: React via CDN. No JSX compilation — use `React.createElement` or htm tagged templates.
- CSS: inline `<style>` blocks. Follow DESIGN-BLUEPRINT.md tokens exactly.
- No Tailwind CSS classes in HTML — we use custom properties matching Tailwind values.

## Naming
- Files: lowercase-with-hyphens
- CSS variables: --kebab-case
- JS functions: camelCase
- Python: snake_case
- API routes: /api/resource-name (plural nouns, kebab-case)

## Git
- Commit messages: imperative mood, <72 chars. "Add pricing section" not "Added pricing section"
- Never commit: .env, *.db, __pycache__, node_modules, .vercel
- Push to main only. No feature branches (solo developer).
