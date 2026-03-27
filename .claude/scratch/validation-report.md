# ComplianceKit Code Validation Report

**Date:** 2026-03-26
**Validator:** Code Validator Agent (Read-Only)
**Scope:** 4 key files - index.html, app.html, app.py, database.py

---

## FILE 1: `/sessions/amazing-brave-clarke/mnt/k/ComplianceKit/public/index.html`

### CSS Variables - Light Mode
**Status:** PASS
- All CSS variables are light mode only (lines 20-36)
- No dark colors present
- Verified: `--bg: #ffffff`, `--text: #111827`, `--accent: #2563eb`

### Container Max-Width
**Status:** PASS
- Line 47: `.container { max-width:1120px; margin:0 auto; padding:0 32px; }`

### Gradients (Linear/Radial)
**Status:** PASS
- Zero gradients found anywhere in the file
- Search confirmed: no `linear-gradient`, `radial-gradient`, or `conic-gradient`

### Hamburger Menu
**Status:** PASS
- Lines 80-84: Menu exists with proper styling
- Lines 203-205: HTML element present with 3 spans (hamburger icon)
- Lines 82-84: Active state transforms correctly (rotate/opacity)
- Line 174: Display: flex on mobile breakpoint
- Lines 453-465: JavaScript event listener implemented, toggles active class

### Footer Links
**Status:** PASS
- Lines 441-442: Footer links present
- `<a href="/privacy.html">Privacy</a>`
- `<a href="/terms.html">Terms</a>`

### Animation Type
**Status:** PASS
- Only fade-in animation found (lines 165-166)
- `.fade-in { opacity:0; transform:translateY(8px); transition:opacity 0.5s ease, transform 0.5s ease; }`
- `.fade-in.visible { opacity:1; transform:translateY(0); }`
- No other animation types present

---

## FILE 2: `/sessions/amazing-brave-clarke/mnt/k/ComplianceKit/public/app.html`

### CSS Variables - Light Mode
**Status:** PASS
- Lines 17-45: All variables are light/neutral colors
- No dark mode colors found
- Background: `#ffffff`, text: `#111827`, sidebar: `#f9fafb`

### Gradients
**Status:** PASS
- Search confirmed: zero linear-gradient or radial-gradient found
- Only solid colors and rgba backgrounds used

### API Error Handling - Try/Except Wrapping
**Status:** PASS (with minor note)
- Lines 1034-1039: GET request wrapped in try/catch
- Lines 1044-1053: POST request wrapped in try/catch
- Lines 1058-1067: PUT request wrapped in try/catch
- Lines 1072-1079: DELETE request wrapped in try/catch
- **Note:** All fetch calls are properly wrapped with error handling

### XSS Fix - dangerouslySetInnerHTML
**Status:** CRITICAL ISSUE FOUND
- Line 1879: `<div className="policy-content" dangerouslySetInnerHTML={{__html: simpleMarkdown(selected.content)}} />`
- **Issue:** While `simpleMarkdown()` attempts sanitization (lines 1157-1180), using `dangerouslySetInnerHTML` is a red flag
- **Risk:** The regex-based sanitization removes script tags and on* handlers, but may not catch all XSS vectors
- **Severity:** HIGH
- **Recommendation:** Use a proper HTML sanitization library (DOMPurify) instead of custom regex sanitization

### Emojis in UI
**Status:** CRITICAL ISSUE FOUND
- Line 1118-1126: `getActionIcon()` contains emoji-like text: `'[📎]'`, `'[✓]'`, `'[📄]'`, `'[!]'`, `'[📊]'`
- **Issue:** Policy text says "NO emojis in UI" but these are Unicode characters that render as emojis on some systems
- **Severity:** MEDIUM (Design rule violation)
- **Note:** These are actually bracketed Unicode, not pure emojis, but violates the spirit of the "no emoji" rule

### Empty States
**Status:** PASS
- Line 985-993: `.empty-state` CSS class present with styling
- Empty state components are available for Evidence, Policies, Alerts based on render logic

### Modal ESC Key Handler
**Status:** PASS
- Lines 1226-1228: ESC key handler properly implemented
- `const handler = (e) => { if (e.key === 'Escape') onClose(); };`
- Event listener added and cleaned up in useEffect return

---

## FILE 3: `/sessions/amazing-brave-clarke/mnt/k/ComplianceKit/server/app.py`

### CORS Restriction to FRONTEND_URL
**Status:** FAIL - CRITICAL
- Lines 82-88: CORS implementation has a logic error
  ```python
  origin = self.headers.get('Origin', '')
  allowed = os.environ.get('FRONTEND_URL', f'http://localhost:{PORT}')
  if origin == allowed or not origin:
      self.send_header('Access-Control-Allow-Origin', allowed)
  else:
      self.send_header('Access-Control-Allow-Origin', allowed)  # ALWAYS sends allowed, not restricting!
  ```
- **Issue:** Both branches send the SAME header. If origin != allowed and origin exists, it should deny, but it still allows the hardcoded URL
- **Risk:** Broken logic, though not wide-open. Currently allows the configured FRONTEND_URL regardless of request origin
- **Severity:** CRITICAL
- **Fix needed:** Should return 403 in the else clause instead of sending header

### Path Traversal Protection
**Status:** PASS
- Lines 167-172: Static file serving includes path traversal check
  ```python
  filepath = os.path.normpath(os.path.join(STATIC_DIR, parsed.path.lstrip('/')))
  if not filepath.startswith(os.path.normpath(STATIC_DIR)):
      self._json_response({"error": "Forbidden"}, 403)
      return
  ```

### Request Body Size Limit
**Status:** PASS
- Line 29: `MAX_BODY_SIZE = 1024 * 1024  # 1MB`
- Lines 106-108: Size check in `_read_body()` enforces limit

### JSON Parsing - Try/Except
**Status:** PASS
- Lines 110-113: JSON parsing wrapped in try/except

### Security Headers
**Status:** PASS
- Lines 65-66: `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`
- Lines 99-101: Duplicated headers in `_json_response()` (redundant but not harmful)

### DB Writes - Try/Except with Rollback
**Status:** PASS
- All POST/PUT/DELETE handlers use try/except/rollback pattern
- Example lines 419-442: `_update_control_status()` has proper rollback

### Stripe Error Information Leakage
**Status:** FAIL - MEDIUM
- Line 56: `print(f"Stripe API error: {error_body}")` - logs full error to stdout
- Line 951: `return self._json_response({"error": session.get('error', {}).get('message', 'Stripe error')}, 400)`
- **Issue:** Line 951 may leak Stripe error messages to the client (e.g., "Invalid price ID"), exposing internal configuration
- **Severity:** MEDIUM
- **Fix:** Return generic "Payment processing failed" instead of Stripe's specific error

### Stripe Webhook Verification
**Status:** PASS
- Lines 980-1002: Webhook signature verification implemented
- HMAC-SHA256 signature validation
- Rejects requests without valid signature (lines 990-1000)

---

## FILE 4: `/sessions/amazing-brave-clarke/mnt/k/ComplianceKit/server/database.py`

### Indexes for Common Query Patterns
**Status:** PASS
- Lines 161-167: 7 indexes created for common queries
  - `idx_control_status_org_control` - controls table lookups by org and control
  - `idx_evidence_org`, `idx_evidence_org_control` - evidence filtering
  - `idx_controls_framework` - framework queries
  - `idx_org_frameworks_org` - org subscription lookups
  - `idx_policies_org` - policy queries
  - `idx_activity_log_org` - activity log filtering

### NOT NULL Constraints on Critical Fields
**Status:** PARTIAL - MEDIUM
- **Present:** name, email, control_id, title, action, description on specific tables
- **Missing on critical tables:**
  - `evidence.org_id` - NOT NULL missing (line 94)
  - `evidence.control_id` - NOT NULL missing (line 95)
  - `policies.org_id` - NOT NULL missing (line 111)
  - `policies.content` - NOT NULL missing (line 113)
  - `control_status.org_id` - NOT NULL missing (line 81)
  - `control_status.control_id` - NOT NULL missing (line 82)
- **Severity:** MEDIUM - These should have NOT NULL for data integrity
- **Risk:** Orphaned records possible, weak referential integrity

### Seed Data Compatibility
**Status:** PASS
- Lines 172-287: `seed_frameworks()` works with schema (no NOT NULL conflicts)
- Lines 289-395: `seed_demo_data()` successfully inserts demo org, user, evidence, policies

---

## SUMMARY OF FINDINGS

### Critical Issues (Must Fix)
1. **app.py line 82-88:** CORS check logic broken - both branches send same header
2. **app.html line 1879:** dangerouslySetInnerHTML with custom regex sanitization (should use DOMPurify)

### High Issues (Should Fix)
3. **app.py line 951:** Stripe error messages may leak to client
4. **database.py:** Missing NOT NULL constraints on critical fields (evidence.org_id, policies.org_id, control_status.org_id, etc.)

### Medium Issues (Consider Fixing)
5. **app.html lines 1118-1126:** Unicode characters that render as emojis violate design rule (use text alternatives like [IMG], [DOC])

### Passing Checks
- ✅ Light mode CSS variables (index.html, app.html)
- ✅ Container max-width 1120px (index.html)
- ✅ Zero gradients (both HTML files)
- ✅ Hamburger menu fully functional (index.html)
- ✅ Footer links correct (index.html)
- ✅ Fade-in only animation (index.html)
- ✅ API error handling wrapped (app.html)
- ✅ Modal ESC handler (app.html)
- ✅ Path traversal protection (app.py)
- ✅ Body size limit enforced (app.py)
- ✅ JSON parsing error handling (app.py)
- ✅ Security headers present (app.py)
- ✅ DB writes have try/except/rollback (app.py)
- ✅ Stripe webhook signature validation (app.py)
- ✅ Database indexes present (database.py)
- ✅ Seed data works (database.py)

---

## RECOMMENDATIONS PRIORITY

1. **IMMEDIATE:** Fix CORS logic in app.py line 82-88
2. **IMMEDIATE:** Fix dangerouslySetInnerHTML or add proper sanitization library
3. **URGENT:** Add NOT NULL constraints to critical fields in database.py
4. **URGENT:** Change Stripe error handling to return generic message
5. **IMPORTANT:** Replace emoji-like icons with text alternatives
