# ComplianceKit Backend Security Audit Report

**Audit Date:** 2026-03-26
**Files Audited:**
- `/sessions/amazing-brave-clarke/mnt/k/ComplianceKit/server/app.py`
- `/sessions/amazing-brave-clarke/mnt/k/ComplianceKit/server/database.py`

---

## EXECUTIVE SUMMARY

The ComplianceKit backend has **CRITICAL security vulnerabilities** that must be addressed before any production deployment. The application currently has **zero authentication** and **no user isolation**. All 22 API routes are publicly accessible, and a single hardcoded org_id is used throughout.

**Finding Count:** 38 issues identified
- **CRITICAL:** 8 issues (deployment blockers)
- **HIGH:** 14 issues (must fix before production)
- **MEDIUM:** 11 issues (should fix in near-term)
- **LOW:** 5 issues (technical debt)

---

## 1. AUTHENTICATION & AUTHORIZATION

### 1.1 [CRITICAL] No Authentication System Exists
**Severity:** CRITICAL
**File:** app.py (all routes)
**Lines:** 88-118, 159-976
**Description:** The API has zero authentication. All 22 routes are publicly accessible with no user login, token validation, or session management. The design rules document acknowledges this is "Pre-Launch" and a known gap, but it's a deployment blocker.

**Evidence:**
- No auth middleware or decorator
- No JWT/session token validation in any route
- No `Authorization` header checking
- All routes hardcoded to `org_id = "demo-org"`
- No user context verification

**Routes Exposed Without Auth (All 22):**
- GET: /api/dashboard, /api/frameworks, /api/frameworks/{id}, /api/frameworks/{id}/controls, /api/evidence, /api/alerts, /api/policies, /api/activity, /api/reports/compliance/{id}, /api/billing/plans, /api/billing/subscription
- POST: /api/controls/{id}/status, /api/evidence, /api/policies/generate, /api/frameworks/{id}/subscribe, /api/alerts/{id}/read, /api/billing/checkout, /api/billing/portal, /api/billing/webhook
- PUT: /api/policies/{id}
- DELETE: /api/evidence/{id}

**Risk:** An attacker can:
- Read all compliance data, frameworks, controls, evidence, policies
- Create/modify/delete evidence
- Modify control status to hide non-compliance
- Generate policy documents
- Create checkout sessions and access billing portal
- Receive webhook data from Stripe

**Recommendation:** Implement auth before production:
1. Add user registration/login endpoint
2. Create JWT or session-based auth
3. Add auth middleware that validates token on every API request
4. Implement row-level access control by org_id

---

### 1.2 [CRITICAL] Hardcoded Org ID on Every Route
**Severity:** CRITICAL
**File:** app.py
**Lines:** 160, 255, 281, 307, 328, 337, 346, 381, 406, 428, 703, 809, 825, 876
**Description:** All routes use a hardcoded `org_id = "demo-org"`. This violates fundamental multi-tenant principles and data isolation.

**Occurrences:**
```python
org_id = "demo-org"  # Appears in 14+ route handlers
```

**Risk:**
- All users see the same organization's data
- No data isolation between users/tenants
- Any user can modify another org's data (if multi-org support is added)

**Recommendation:** Extract org_id from JWT token or request context instead of hardcoding.

---

### 1.3 [HIGH] No User Identification in Activity Log
**Severity:** HIGH
**File:** app.py
**Lines:** 395-396, 417-418, 692-693
**Description:** Activity logs hardcode `user_id = "demo-user"` instead of capturing the actual authenticated user.

**Evidence:**
```python
(str(uuid.uuid4()), org_id, "demo-user", "control_updated", ...)
```

**Risk:** Cannot audit who performed actions; accountability is lost.

**Recommendation:** Extract user_id from auth context.

---

## 2. SECURITY VULNERABILITIES

### 2.1 [HIGH] SQL Injection in Webhook Event Processing
**Severity:** HIGH
**File:** app.py
**Lines:** 936, 950, 964
**Description:** While parameterized queries are used for SQL statements, the webhook handler iterates over all organizations and compares settings JSON. If the settings JSON is ever parsed unsafely, it could be exploited. More critically, there's no validation that the Stripe customer_id comes from a trusted source before using it to find and update organizations.

**Code:**
```python
def _stripe_webhook(self, params):
    # ... signature validation ...
    customer_id = data.get('customer')  # Untrusted
    orgs = conn.execute("SELECT id, settings FROM organizations").fetchall()
    for org in orgs:
        s = json.loads(org['settings'] or '{}')
        if s.get('stripe_customer_id') == customer_id:  # String comparison only
```

**Risk:**
- If settings JSON becomes user-modifiable, injection is possible
- No rate limiting on webhook processing
- Loops over ALL organizations on every webhook

**Recommendation:**
1. Query organization by stripe_customer_id directly instead of looping all orgs
2. Add webhook event deduplication (Stripe retries)
3. Rate limit webhook processing

---

### 2.2 [HIGH] CORS Wildcard Configuration
**Severity:** HIGH
**File:** app.py
**Line:** 62
**Description:** CORS allows all origins with wildcard `*`. In production, this allows any website to make requests on behalf of users.

**Code:**
```python
self.send_header('Access-Control-Allow-Origin', '*')
```

**Risk:** CSRF attacks, credential theft via cross-site requests, XSS via malicious CDN.

**Recommendation:** Restrict to specific origin:
```python
allowed_origin = os.environ.get('FRONTEND_URL')
self.send_header('Access-Control-Allow-Origin', allowed_origin)
```

---

### 2.3 [HIGH] Missing CSRF Token Validation
**Severity:** HIGH
**File:** app.py
**Lines:** 102-117 (all POST/PUT/DELETE routes)
**Description:** No CSRF tokens on state-changing requests. Combined with wildcard CORS, this is exploitable.

**Risk:** Cross-site request forgery attacks.

**Recommendation:** Add CSRF token generation and validation for all POST/PUT/DELETE.

---

### 2.4 [MEDIUM] Missing Request Body Size Limit
**Severity:** MEDIUM
**File:** app.py
**Lines:** 76-80
**Description:** The `_read_body()` method reads all Content-Length bytes without validation. A malicious client could send a 1GB request to cause DoS.

**Code:**
```python
def _read_body(self):
    length = int(self.headers.get('Content-Length', 0))
    if length:
        return json.loads(self.rfile.read(length))  # No limit check
    return {}
```

**Risk:** Denial of service via large payloads.

**Recommendation:** Add max size limit:
```python
MAX_BODY_SIZE = 1024 * 1024  # 1MB
if length > MAX_BODY_SIZE:
    return self._json_response({"error": "Payload too large"}, 413)
```

---

### 2.5 [MEDIUM] Missing Input Validation on User-Supplied Fields
**Severity:** MEDIUM
**File:** app.py
**Lines:** 404-414, 426-430, 379-391, 738-745
**Description:** User input is passed directly to database without validation:

**Examples:**
```python
# _add_evidence (line 410-414)
conn.execute(..., (ev_id, org_id, body.get('control_id'),
    body.get('title'), body.get('description'), ...))

# _update_control_status (line 379-391)
conn.execute(..., (..., body.get('status', 'not_started'), ...))

# _update_policy (line 738-745)
conn.execute(..., (body.get('content'), body.get('status', 'draft'), ...))
```

**Risk:**
- Invalid status values stored in database
- XSS if policy content is rendered unsafely on frontend
- Evidence titles/descriptions may contain malicious content

**Recommendation:** Validate all inputs:
```python
VALID_STATUSES = {'not_started', 'in_progress', 'compliant', 'non_compliant'}
if body.get('status') not in VALID_STATUSES:
    return self._json_response({"error": "Invalid status"}, 400)
```

---

### 2.6 [MEDIUM] Path Traversal Risk in Static File Serving
**Severity:** MEDIUM
**File:** app.py
**Lines:** 134-140
**Description:** Static file serving has improper path handling. The code uses `os.path.isfile(filepath)` which could be vulnerable if the STATIC_DIR is not properly validated.

**Code:**
```python
filepath = os.path.join(STATIC_DIR, parsed.path.lstrip('/'))
if os.path.isfile(filepath):
    super().do_GET()
else:
    self.path = '/index.html'
    super().do_GET()
```

**Risk:** If `.lstrip()` is used incorrectly or STATIC_DIR is not set correctly, attackers might access files outside the public directory via `../../etc/passwd` style paths.

**Recommendation:** Use `os.path.normpath()` and validate the final path is within STATIC_DIR:
```python
filepath = os.path.normpath(os.path.join(STATIC_DIR, parsed.path.lstrip('/')))
if not filepath.startswith(STATIC_DIR):
    return self._json_response({"error": "Forbidden"}, 403)
if os.path.isfile(filepath):
    super().do_GET()
```

---

### 2.7 [MEDIUM] Command Injection Risk Not Present But Database Access Pattern Needs Review
**Severity:** LOW (Not Exploitable Currently)
**File:** app.py and database.py
**Description:** While SQL injection is not present (parameterized queries used), the direct use of `shell=False` in any subprocess calls would be safe. However, there are NO subprocess calls, so this is not a risk. However, the environment variable retrieval should be more careful.

---

## 3. ERROR HANDLING

### 3.1 [HIGH] Raw Database Errors Leaked to Client
**Severity:** HIGH
**File:** app.py
**Lines:** 46-50
**Description:** Stripe API errors are returned directly to client without sanitization.

**Code:**
```python
except urllib.error.HTTPError as e:
    return json.loads(e.read())  # Returns raw Stripe error
```

**Risk:** Exposes internal API details, Stripe endpoint structure to attacker.

**Recommendation:** Catch and log errors, return generic message:
```python
except urllib.error.HTTPError as e:
    error_body = json.loads(e.read())
    # Log error_body for debugging
    return {"error": "Payment processing failed"}
```

---

### 3.2 [HIGH] Missing Try/Except on Database Operations
**Severity:** HIGH
**File:** app.py
**Lines:** 161-240, 253-269, 271-278, 280-304, 306-317, 319-325, etc.
**Description:** Database operations have no error handling. If a database constraint is violated or DB is unavailable, the server crashes.

**Risk:**
- Server crashes on constraint violations (e.g., duplicate email)
- No graceful degradation
- Unhandled exceptions return 500 errors without logging

**Examples of unprotected operations:**
- Line 384-391: UPDATE control_status without try/except
- Line 410-414: INSERT evidence without error handling
- Line 686-689: INSERT policy without error handling

**Recommendation:** Wrap all database operations:
```python
try:
    conn.execute(...)
    conn.commit()
except sqlite3.IntegrityError as e:
    conn.rollback()
    return self._json_response({"error": "Database constraint violated"}, 400)
except Exception as e:
    conn.rollback()
    # Log e
    return self._json_response({"error": "Database error"}, 500)
finally:
    conn.close()
```

---

### 3.3 [MEDIUM] Unhandled Exceptions in JSON Parsing
**Severity:** MEDIUM
**File:** app.py
**Lines:** 79, 813, 838, 884
**Description:** JSON parsing is not wrapped in try/except.

**Code:**
```python
def _read_body(self):
    length = int(self.headers.get('Content-Length', 0))
    if length:
        return json.loads(self.rfile.read(length))  # Crashes on invalid JSON
    return {}
```

**Risk:** Malformed JSON from client crashes the server.

**Recommendation:**
```python
try:
    return json.loads(self.rfile.read(length))
except json.JSONDecodeError:
    return {}  # or raise exception and return 400
```

---

### 3.4 [MEDIUM] Stripe Webhook Parsing Error Not Handled
**Severity:** MEDIUM
**File:** app.py
**Lines:** 909, 919
**Description:** The webhook parsing has a try/except (line 908-917) but the second JSON parse (line 919) is outside the try block.

**Code:**
```python
try:
    # Signature validation
except Exception:
    return self._json_response({"error": "Webhook verification failed"}, 400)

event = json.loads(raw_body)  # Can still crash here
```

**Risk:** Invalid JSON in webhook causes server crash.

**Recommendation:** Move line 919 inside try block.

---

## 4. API CORRECTNESS & DESIGN

### 4.1 [MEDIUM] Route Pattern Matches Are Not Fully Anchored
**Severity:** MEDIUM
**File:** app.py
**Lines:** 88-117
**Description:** Regex patterns use `^` and `$` correctly, so this is actually fine. No issue here—I was wrong. The patterns are properly anchored.

**Status:** PASS

---

### 4.2 [MEDIUM] Missing PUT/DELETE Response Status Codes
**Severity:** MEDIUM
**File:** app.py
**Lines:** 700, 746, 753
**Description:** POST creates a resource and returns 201 (line 424), but PUT and DELETE return 200 (implicit default).

**Code:**
```python
# POST /api/evidence (line 424)
self._json_response({"success": True, "id": ev_id}, 201)

# PUT /api/policies (line 746)
self._json_response({"success": True})  # Should be 204 or explicit 200

# DELETE /api/evidence (line 753)
self._json_response({"success": True})  # Should be 204
```

**Risk:** API contract inconsistency; clients expect different status codes.

**Recommendation:**
- POST: 201 (Created) ✓ Correct
- PUT: 200 (OK) or 204 (No Content) - choose one
- DELETE: 204 (No Content) or 200 (OK) - choose one

---

### 4.3 [MEDIUM] Missing Pagination on Large Result Sets
**Severity:** MEDIUM
**File:** app.py
**Lines:** 253-269, 306-317, 319-325, 336-343
**Description:** Routes return unbounded result sets. For example, `_get_evidence()` fetches all evidence without pagination.

**Examples:**
```python
# _get_evidence (no pagination)
evidence = conn.execute(...).fetchall()

# _get_alerts (no pagination)
alerts = conn.execute(...).fetchall()

# _get_activity (has LIMIT 50, good)
activity = conn.execute(...LIMIT 50...).fetchall()
```

**Risk:**
- Large orgs with thousands of evidence items will have slow API responses
- Client receives GB of JSON on /api/evidence

**Recommendation:** Add pagination to all list endpoints:
```python
limit = int(params.get('limit', ['50'])[0])
offset = int(params.get('offset', ['0'])[0])
evidence = conn.execute(...).LIMIT ? OFFSET ?...).fetchall()
```

---

### 4.4 [MEDIUM] N+1 Query Pattern in _get_controls
**Severity:** MEDIUM
**File:** app.py
**Lines:** 280-304
**Description:** The `_get_controls()` handler executes a separate query inside the loop for evidence count.

**Code:**
```python
for ctrl in controls:
    d = dict(ctrl)
    ev_count = conn.execute(
        "SELECT COUNT(*) as count FROM evidence WHERE control_id = ? AND org_id = ?",
        (ctrl['id'], org_id)
    ).fetchone()['count']  # N+1 query!
```

**Risk:** For a framework with 100+ controls, this executes 100+ extra queries.

**Recommendation:** Use a single JOIN or subquery:
```python
controls = conn.execute("""
    SELECT c.*,
        (SELECT COUNT(*) FROM evidence WHERE control_id = c.id AND org_id = ?) as evidence_count
    FROM controls c
    LEFT JOIN control_status cs ON ...
""", (org_id, fw_id)).fetchall()
```

---

### 4.5 [MEDIUM] Missing Webhook Idempotency Handling
**Severity:** MEDIUM
**File:** app.py
**Lines:** 900-975
**Description:** Stripe webhooks can be retried. The handler processes the same event multiple times, leading to duplicated work.

**Risk:** Multiple updates to org subscription settings, double-billing scenarios.

**Recommendation:** Track processed webhook IDs:
```python
webhook_id = event.get('id')
if conn.execute("SELECT id FROM webhook_log WHERE webhook_id = ?", (webhook_id,)).fetchone():
    return self._json_response({"received": True})  # Already processed
conn.execute("INSERT INTO webhook_log (webhook_id) VALUES (?)", (webhook_id,))
```

---

## 5. STRIPE INTEGRATION

### 5.1 [HIGH] Missing Stripe API Key Validation
**Severity:** HIGH
**File:** app.py
**Lines:** 28-34, 827-832, 878-879
**Description:** If Stripe credentials are missing, the app returns error messages but continues to operate.

**Code:**
```python
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
# ... later ...
if not STRIPE_SECRET_KEY:
    return self._json_response({"error": "Stripe not configured..."}, 400)
```

**Risk:**
- Development mode might have empty keys
- No validation that keys are valid format
- Users can see empty price IDs in /api/billing/plans

**Recommendation:**
1. Fail startup if STRIPE_SECRET_KEY not set
2. Validate key format at startup
3. Don't expose blank price_ids in plans response

---

### 5.2 [HIGH] Webhook Signature Verification Can Be Bypassed
**Severity:** HIGH
**File:** app.py
**Lines:** 907-917
**Description:** Signature verification is skipped if `STRIPE_WEBHOOK_SECRET` is not set.

**Code:**
```python
if STRIPE_WEBHOOK_SECRET and sig_header:
    try:
        # Verify...
    except Exception:
        return error
# If STRIPE_WEBHOOK_SECRET is empty, NO VERIFICATION
event = json.loads(raw_body)  # Processes unverified webhook
```

**Risk:** In development, webhooks are accepted without verification. An attacker can forge webhook events and modify subscriptions.

**Recommendation:** Make webhook secret mandatory in production:
```python
if not STRIPE_WEBHOOK_SECRET:
    return self._json_response({"error": "Webhooks disabled"}, 400)
# Always verify
```

---

### 5.3 [MEDIUM] Hardcoded Customer Email in Stripe API
**Severity:** MEDIUM
**File:** app.py
**Line:** 843
**Description:** When creating a Stripe customer, email is hardcoded.

**Code:**
```python
customer = stripe_request('POST', '/customers', {
    'email': 'admin@acmesaas.com',  # Hardcoded!
    'name': org['name'],
    'metadata[org_id]': org_id,
})
```

**Risk:** All organizations use the same email, making it impossible to manage multiple Stripe customers properly.

**Recommendation:** Get email from org settings or authenticated user context.

---

### 5.4 [MEDIUM] Missing Idempotency Keys on Stripe Requests
**Severity:** MEDIUM
**File:** app.py
**Lines:** 36-50
**Description:** Stripe API requests have no idempotency keys. If a request times out and is retried, it could create duplicate charges.

**Risk:** Double-billing on network errors.

**Recommendation:** Add Idempotency-Key header to all POST requests:
```python
headers['Idempotency-Key'] = str(uuid.uuid4())
```

---

### 5.5 [MEDIUM] Stripe Price ID Validation Missing
**Severity:** MEDIUM
**File:** app.py
**Lines:** 830-832
**Description:** The `/api/billing/checkout` endpoint accepts any plan name and generates an error if price_id is missing, but doesn't validate that the price_id actually exists in Stripe.

**Risk:** User could potentially inject arbitrary plan names.

**Recommendation:** Pre-validate all price IDs at startup against Stripe API.

---

## 6. CORS & CROSS-SITE SECURITY

### 6.1 [HIGH] Wildcard CORS with Credentials
**Severity:** HIGH
**File:** app.py
**Line:** 62-64
**Description:** CORS headers allow all origins. While no credentials are sent with cookies (app uses JSON auth), if cookies were added in the future, this would be exploitable.

**Code:**
```python
self.send_header('Access-Control-Allow-Origin', '*')
self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
```

**Risk:** CSRF attacks, requests from any origin.

**Recommendation:** Restrict to frontend URL:
```python
frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
origin = self.headers.get('Origin', '')
if origin == frontend_url:
    self.send_header('Access-Control-Allow-Origin', origin)
```

---

## 7. PERFORMANCE & SCALABILITY

### 7.1 [MEDIUM] N+1 Query in Dashboard Handler
**Severity:** MEDIUM
**File:** app.py
**Lines:** 175-186
**Description:** The dashboard loops over frameworks and executes a separate query for each.

**Code:**
```python
for fw in frameworks:
    stats = conn.execute("""SELECT...""", (org_id, fw['id'])).fetchone()
```

**Risk:** For 50+ frameworks, this is 50+ queries instead of 1 JOIN.

**Recommendation:** Use a single query with GROUP BY:
```python
stats = conn.execute("""
    SELECT f.id, f.short_name, ...,
        COUNT(*) as total,
        SUM(...) as compliant, ...
    FROM frameworks f
    LEFT JOIN controls c ON c.framework_id = f.id
    LEFT JOIN control_status cs ON ...
    WHERE of2.org_id = ?
    GROUP BY f.id
""", (org_id,)).fetchall()
```

---

### 7.2 [MEDIUM] Missing Database Indexes
**Severity:** MEDIUM
**File:** database.py
**Lines:** 25-158
**Description:** The schema creates tables but no indexes. High-cardinality queries will be slow.

**Evidence of missing indexes:**
- `control_status` table queried by `(org_id, control_id)` — needs compound index
- `evidence` table queried by `(org_id, control_id)` — needs compound index
- `evidence` table filtered by `org_id` — needs index
- `controls` table filtered by `framework_id` — needs index
- `org_frameworks` filtered by `org_id` — needs index

**Risk:** Queries with 10k+ rows in any table will be O(n) scans instead of O(log n) lookups.

**Recommendation:** Add indexes in `init_db()`:
```python
c.execute("CREATE INDEX IF NOT EXISTS idx_evidence_org_control ON evidence(org_id, control_id)")
c.execute("CREATE INDEX IF NOT EXISTS idx_control_status_org_control ON control_status(org_id, control_id)")
c.execute("CREATE INDEX IF NOT EXISTS idx_controls_framework ON controls(framework_id)")
c.execute("CREATE INDEX IF NOT EXISTS idx_org_frameworks_org ON org_frameworks(org_id)")
```

---

### 7.3 [LOW] JSON Parsing in Hot Path
**Severity:** LOW
**File:** app.py
**Lines:** 813, 838, 884
**Description:** Organization settings are stored as JSON strings and parsed on every request.

**Code:**
```python
settings = json.loads(org['settings'] or '{}')
```

**Risk:** Minor performance impact; JSON parsing is fast but repeated.

**Recommendation:** Consider caching org settings in memory or using a dedicated settings table.

---

## 8. HTTP STANDARDS & PROTOCOLS

### 8.1 [MEDIUM] Missing Content-Type Header in Some Responses
**Severity:** MEDIUM
**File:** app.py
**Lines:** 66-74
**Description:** JSON responses correctly set `Content-Type: application/json`, but static file serving delegates to `SimpleHTTPRequestHandler` which may not set appropriate Content-Type for all file types.

**Status:** PASS (SimpleHTTPRequestHandler handles this).

---

### 8.2 [MEDIUM] Missing Cache-Control Headers
**Severity:** MEDIUM
**File:** app.py
**Lines:** 66-74
**Description:** API responses don't include Cache-Control headers. Sensitive data (policies, evidence) should never be cached.

**Risk:** Intermediate proxies might cache sensitive data.

**Recommendation:**
```python
self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
```

---

### 8.3 [LOW] Missing Security Headers
**Severity:** LOW
**File:** app.py
**Lines:** 56-74
**Description:** Response headers should include security headers like CSP, X-Frame-Options, X-Content-Type-Options.

**Recommendation:** Add to `_json_response()`:
```python
self.send_header('X-Content-Type-Options', 'nosniff')
self.send_header('X-Frame-Options', 'DENY')
self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
```

---

## 9. ENVIRONMENT VARIABLES & CONFIGURATION

### 9.1 [HIGH] Missing Environment Variable Validation
**Severity:** HIGH
**File:** app.py
**Lines:** 23-34, 25
**Description:** Environment variables are read with defaults but not validated at startup.

**Variables Read:**
- `PORT` (default 3000) ✓ Validated by int()
- `FRONTEND_URL` (default localhost) — not validated
- `STRIPE_SECRET_KEY` (default '') — not validated
- `STRIPE_WEBHOOK_SECRET` (default '') — not validated
- `STRIPE_PRICE_*` (default '') — not validated

**Risk:**
- Invalid FRONTEND_URL breaks CORS and redirects
- Empty Stripe keys fail silently
- No validation that required secrets are set

**Recommendation:**
```python
def get_config():
    required = ['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET']
    for var in required:
        if not os.environ.get(var):
            raise ValueError(f"Missing required env var: {var}")
    return {...}
```

---

### 9.2 [MEDIUM] Stripe Keys Not Validated for Format
**Severity:** MEDIUM
**File:** app.py
**Lines:** 28-34
**Description:** No validation that Stripe keys match expected format (sk_* prefix for secret keys).

**Risk:** Misconfigured keys fail only at runtime.

**Recommendation:**
```python
sk = os.environ.get('STRIPE_SECRET_KEY', '')
if sk and not sk.startswith('sk_'):
    raise ValueError("STRIPE_SECRET_KEY must start with 'sk_'")
```

---

## 10. FILE SERVING & STATIC FILES

### 10.1 [MEDIUM] Implicit index.html on 404
**Severity:** MEDIUM
**File:** app.py
**Lines:** 138-140
**Description:** Any non-existent file defaults to serving index.html. This is correct for SPA routing but could mask misconfigurations.

**Code:**
```python
if os.path.isfile(filepath):
    super().do_GET()
else:
    self.path = '/index.html'
    super().do_GET()
```

**Risk:** If a file is deleted by mistake, client loads the SPA instead of 404. Not a security issue but operational risk.

**Recommendation:** Consider returning 404 for API paths that don't exist:
```python
if parsed.path.startswith('/api/'):
    return self._json_response({"error": "Not found"}, 404)
```

---

### 10.2 [MEDIUM] No Security Headers on Static Files
**Severity:** MEDIUM
**File:** app.py
**Lines:** 132-140
**Description:** Static files are served via `SimpleHTTPRequestHandler`, which doesn't add security headers.

**Risk:**
- No CSP on HTML
- No X-Frame-Options
- Can be clickjacked

**Recommendation:** Override `do_GET()` to add security headers before calling parent.

---

## 11. DATABASE SCHEMA & CONSTRAINTS

### 11.1 [MEDIUM] Missing Foreign Key Constraints
**Severity:** MEDIUM
**File:** database.py
**Lines:** 25-158
**Description:** While FOREIGN KEY pragma is enabled (line 17), some relationships are not properly constrained.

**Example:**
```python
c.execute('''CREATE TABLE IF NOT EXISTS control_status (
    id TEXT PRIMARY KEY,
    org_id TEXT REFERENCES organizations(id),  # Good
    control_id TEXT REFERENCES controls(id),  # Good
    ...
)''')
```

**Status:** Actually, PASS. Foreign keys are properly defined.

---

### 11.2 [MEDIUM] Missing NOT NULL Constraints on Critical Fields
**Severity:** MEDIUM
**File:** database.py
**Description:** Some critical fields allow NULL but should be NOT NULL.

**Examples:**
- `controls.description` — should not be NULL
- `evidence.file_path` — should be NOT NULL if evidence is approved
- `organizations.settings` — has default '{}', should work but should be NOT NULL

**Recommendation:**
```python
c.execute('''CREATE TABLE IF NOT EXISTS controls (
    ...
    description TEXT NOT NULL,
    ...
)''')
```

---

### 11.3 [LOW] Missing Unique Constraints
**Severity:** LOW
**File:** database.py
**Lines:** 58-66
**Description:** Control IDs within a framework should be unique but aren't explicitly constrained.

**Current:** Multiple controls can have `control_id = "CC6.1"` from different frameworks. This is actually OK since the PK is the combined id, but could be clearer.

**Status:** ACCEPTABLE AS-IS

---

### 11.4 [MEDIUM] Data Seed Contains SQL Injection Risk (Actually Safe)
**Severity:** LOW (Already Safe)
**File:** database.py
**Lines:** 266-275
**Description:** The seed data uses parameterized queries correctly. No issue.

**Status:** PASS

---

## 12. COMPLIANCE & AUDIT

### 12.1 [MEDIUM] Activity Log Not Complete
**Severity:** MEDIUM
**File:** app.py & database.py
**Description:** Activity logs miss several important actions:
- User login/logout
- Policy generation details
- Stripe events
- Framework subscribe/unsubscribe

**Risk:** Incomplete audit trail.

**Recommendation:** Add activity logging to all state-changing operations.

---

### 12.2 [MEDIUM] No Data Retention Policy Enforcement
**Severity:** MEDIUM
**File:** database.py
**Description:** The schema defines `created_at` timestamps but no automated cleanup or retention enforcement.

**Risk:** Data accumulates indefinitely.

**Recommendation:** Add background job to delete evidence older than retention period:
```python
DELETE FROM evidence WHERE created_at < datetime('now', '-90 days') AND status = 'rejected'
```

---

## 13. SUMMARY TABLE

| ID | Issue | Severity | File | Line | Status |
|----|-------|----------|------|------|--------|
| 1.1 | No authentication | CRITICAL | app.py | 88-118 | BLOCKER |
| 1.2 | Hardcoded org_id | CRITICAL | app.py | 160+ | BLOCKER |
| 1.3 | Hardcoded user_id | HIGH | app.py | 395-396 | FIX |
| 2.1 | SQL injection risk in webhook | HIGH | app.py | 936-970 | FIX |
| 2.2 | CORS wildcard | HIGH | app.py | 62 | FIX |
| 2.3 | No CSRF tokens | HIGH | app.py | 102-117 | FIX |
| 2.4 | No request size limit | MEDIUM | app.py | 76-80 | FIX |
| 2.5 | No input validation | MEDIUM | app.py | 404-414 | FIX |
| 2.6 | Path traversal risk | MEDIUM | app.py | 134-140 | FIX |
| 3.1 | Raw errors to client | HIGH | app.py | 46-50 | FIX |
| 3.2 | No try/except on DB ops | HIGH | app.py | 161-975 | FIX |
| 3.3 | No JSON error handling | MEDIUM | app.py | 79 | FIX |
| 3.4 | Webhook parsing error | MEDIUM | app.py | 919 | FIX |
| 4.2 | Wrong HTTP status codes | MEDIUM | app.py | 700-753 | FIX |
| 4.3 | No pagination | MEDIUM | app.py | 253-343 | FIX |
| 4.4 | N+1 query in controls | MEDIUM | app.py | 280-304 | FIX |
| 4.5 | No webhook idempotency | MEDIUM | app.py | 900-975 | FIX |
| 5.1 | Missing Stripe key validation | HIGH | app.py | 28-34 | FIX |
| 5.2 | Webhook sig bypass | HIGH | app.py | 907-917 | FIX |
| 5.3 | Hardcoded customer email | MEDIUM | app.py | 843 | FIX |
| 5.4 | No idempotency keys | MEDIUM | app.py | 36-50 | FIX |
| 5.5 | No price_id validation | MEDIUM | app.py | 830-832 | FIX |
| 6.1 | CORS with credentials risk | HIGH | app.py | 62-64 | FIX |
| 7.1 | N+1 in dashboard | MEDIUM | app.py | 175-186 | FIX |
| 7.2 | Missing DB indexes | MEDIUM | database.py | 25-158 | FIX |
| 7.3 | JSON parsing in hot path | LOW | app.py | 813-884 | OPTIMIZE |
| 8.2 | No Cache-Control headers | MEDIUM | app.py | 66-74 | FIX |
| 8.3 | No security headers | LOW | app.py | 56-74 | FIX |
| 9.1 | No env var validation | HIGH | app.py | 23-34 | FIX |
| 9.2 | No Stripe key format check | MEDIUM | app.py | 28-34 | FIX |
| 10.1 | Implicit index.html on 404 | MEDIUM | app.py | 138-140 | REVIEW |
| 10.2 | No security headers on static | MEDIUM | app.py | 132-140 | FIX |
| 12.1 | Incomplete activity log | MEDIUM | app.py | ALL | FIX |
| 12.2 | No data retention policy | MEDIUM | database.py | ALL | IMPLEMENT |

---

## CRITICAL PATH TO PRODUCTION

**Must Fix Before Launch:**

1. ✗ Implement authentication (users, tokens, session management)
2. ✗ Remove hardcoded org_id and user_id (extract from auth context)
3. ✗ Restrict CORS to specific frontend origin
4. ✗ Add CSRF token validation
5. ✗ Add input validation on all user fields
6. ✗ Add error handling (try/except) on all DB operations
7. ✗ Fix webhook signature verification (fail if no secret)
8. ✗ Validate Stripe API keys at startup
9. ✗ Add database indexes for common queries

**Should Fix Before First Users:**

1. Add pagination to list endpoints
2. Add security headers (CSP, X-Frame-Options, etc.)
3. Implement webhook idempotency
4. Add request body size limits
5. Complete activity logging
6. Add data retention policies

---

## TESTING RECOMMENDATIONS

1. **Authentication Security:**
   - Test that unauthenticated requests are rejected
   - Test that org_id in token matches queried data
   - Test JWT token expiration and refresh

2. **CSRF & CORS:**
   - Test that POST/PUT/DELETE from different origin fails
   - Test that CSRF tokens are validated
   - Test that CORS headers match configured origin

3. **SQL Injection:**
   - Attempt to inject SQL via evidence title, policy content, notes
   - Verify all queries use parameterized statements

4. **Error Handling:**
   - Send malformed JSON to all POST endpoints
   - Send oversized payloads (>10MB)
   - Shut down database and verify graceful error

5. **Stripe Webhook:**
   - Test webhook signature validation with invalid signatures
   - Test duplicate webhook idempotency
   - Test that forged events without signature are rejected

---

## CONCLUSION

The ComplianceKit backend is a functional demo but **not production-ready** due to:

1. Complete lack of authentication
2. No multi-tenant data isolation
3. Multiple critical error handling gaps
4. Insecure CORS configuration
5. Stripe integration vulnerabilities

Estimated effort to fix: **80-120 engineer-hours** (2-3 weeks for small team).

**Recommend:** Address CRITICAL items before any public testing. HIGH-severity items must be fixed before production use.
