# ComplianceKit App.html Audit Report
**Date:** 2026-03-26
**File:** /sessions/amazing-brave-clarke/mnt/k/ComplianceKit/public/app.html
**Total Lines:** 2285

---

## CRITICAL ISSUES

### 1. DESIGN VIOLATIONS - Dark Mode Instead of Light Mode

**SEVERITY:** CRITICAL | **LINE NUMBERS:** 18-43

The entire design system uses dark mode colors, violating the LIGHT MODE ONLY requirement from design.md.

```
Root CSS Variables:
  --bg: #0a0a0f;              (Dark black)
  --bg-card: #12121a;         (Dark card)
  --bg-sidebar: #0d0d14;      (Dark sidebar)
  --text: #e4e4e7;            (Light text)
  --border: #1e1e2e;          (Dark border)
```

**Expected:** White backgrounds, light gray (#f8f9fa / #fafbfc), gray-50 sidebar, etc.

**Impact:** Entire UI is inverted from spec. Requires full color system replacement.

---

### 2. GRADIENTS USED IN PRODUCTION - Violates No-Gradient Rule

**SEVERITY:** CRITICAL | **LINE NUMBERS:** 108, 197, 769

Gradients are explicitly forbidden in design.md but are used throughout:

```jsx
Line 108:  background: linear-gradient(135deg, var(--primary), #8b5cf6);  // Logo icon
Line 197:  background: linear-gradient(135deg, #6366f1, #ec4899);         // User avatar
Line 769:  background: linear-gradient(135deg, #fff 0%, #e4e4e7 50%, #9393a8 100%);  // Hero title
```

**Expected:** Solid colors only.

**Impact:** Visual inconsistency with design system. Premium/gimmicky look violates restraint guidelines.

---

### 3. MISSING KEYS ON LIST RENDERS - React Warning/Bug

**SEVERITY:** HIGH | **LINE NUMBERS:** 2133

```jsx
Line 2133: {plan.features.map((f, i) => <li key={i}>{f}</li>)}
```

Using array index as key is an anti-pattern. If features array is reordered, DOM will be misaligned.

**Fix:** Use unique feature ID or ensure features never reorder.

---

### 4. NO ERROR HANDLING ON API CALLS

**SEVERITY:** HIGH | **LINE NUMBERS:** 1035-1059, throughout

API layer has zero error handling:

```jsx
Lines 1035-1059:
const api = {
  get: async (path) => {
    const res = await fetch(`${API}${path}`);
    return res.json();  // ← No error check. What if 404? 500? Network failure?
  },
  post: async (path, body) => {
    const res = await fetch(`${API}${path}`, { ... });
    return res.json();  // ← No error check
  },
  // ... same for put, del
};
```

**Impact:**
- Network failures silently fail
- Failed requests return undefined, crashing components
- No user feedback on API errors
- Silent state corruption

**Example failure point (Line 1419):**
```jsx
useEffect(() => { api.get('/frameworks').then(setFrameworks); }, []);
// If /frameworks returns 500, setFrameworks(undefined) and list renders undefined
```

---

### 5. STALE CLOSURE BUG IN useCallback

**SEVERITY:** MEDIUM | **LINE NUMBERS:** 2167-2174

```jsx
const loadDashboard = useCallback(async () => {
  try {
    const data = await api.get('/dashboard');
    setDashboard(data);
  } catch (e) {
    console.error('Failed to load dashboard:', e);
  }
}, []);  // ← Empty dependency array

useEffect(() => {
  if (page !== 'landing') {
    loadDashboard();
  }
}, [page, loadDashboard]);  // ← loadDashboard is a dependency
```

**Issue:** `loadDashboard` is defined with empty dependencies but used as a dependency in another useEffect. This creates unnecessary re-renders and potential memory leaks. Should either remove loadDashboard from deps or add page to loadDashboard's deps.

---

### 6. BROKEN STATE MANAGEMENT - LocalStorage Auth

**SEVERITY:** HIGH | **LINE NUMBERS:** 2186-2187, 1220-1221

Auth is entirely client-side with no backend validation:

```jsx
Line 2186-2187:
const user = localStorage.getItem('ck_user');
if (user) { setTimeout(() => setPage('dashboard'), 0); return null; }

Line 1220-1221:
localStorage.setItem('ck_user', JSON.stringify({ email, name: ... }));
onEnterApp();
```

**Issues:**
1. No backend session validation
2. User can manually edit localStorage and create any identity
3. No CSRF protection
4. No JWT/session tokens
5. `setTimeout(..., 0)` is an anti-pattern (use dependency array instead)

**Security Risk:** Anyone can become any user by editing browser storage.

---

## MAJOR ISSUES

### 7. Missing/Broken Error States

**SEVERITY:** HIGH | **MULTIPLE LINES**

Components render data without checking if it exists:

```jsx
Line 1296: if (!dashboard) return <div className="loading">Loading...</div>;
// But FrameworksPage (Line 1412) has no loading state at all

Line 1419: useEffect(() => { api.get('/frameworks').then(setFrameworks); }, []);
// If this fails, frameworks = [], but no error message to user
```

**Affected Components:**
- FrameworksPage: No loading state, no error state
- EvidencePage: No error handling on api.get('/evidence')
- AlertsPage: No error handling
- PoliciesPage: No error handling
- ReportsPage: No error handling
- BillingPage: No error handling on api.get('/billing/plans')

---

### 8. Missing Empty States in Data Tables

**SEVERITY:** MEDIUM | **MULTIPLE LINES**

Tables render without checking if they're empty:

```jsx
Line 1626: {evidence.map(ev => (  // What if evidence.length === 0?
  <div key={ev.id} className="evidence-item" ...>

Line 1728: {alerts.map(alert => (  // What if alerts.length === 0?
  <div key={alert.id} className={`alert-item ...} ...>
```

**Issue:** No fallback for empty states. Users see blank screens instead of "No data" messages.

**Fixed Example (Line 1815-1820):**
```jsx
{policies.length === 0 && (
  <div className="empty-state">
    <div className="empty-state-icon">📄</div>
    <div className="empty-state-title">No policies yet</div>
    ...
  </div>
)}
```

**Unfixed:** Evidence, Alerts, Frameworks tables need same treatment.

---

### 9. Billing Page - Stripe Integration Incomplete

**SEVERITY:** HIGH | **LINE NUMBERS:** 2055-2158

Stripe checkout flow is broken:

```jsx
Line 2061-2062:
api.get('/billing/plans').then(d => setPlans(d.plans || []));
api.get('/billing/subscription').then(setSubscription);
// If /billing/subscription returns 500, subscription = undefined
// Line 2084: const currentPlan = subscription?.plan || 'trial';
// Line 2093: {subscription && ( ... )}  // Gracefully handles undefined

Line 2065-2074:
const checkout = async (planId) => {
  setLoading(planId);
  const result = await api.post('/billing/checkout', { plan: planId });
  setLoading(null);
  if (result.checkout_url) {
    window.location.href = result.checkout_url;  // ← Hard redirect, user loses state
  } else {
    alert(result.error || 'Failed to start checkout.');  // ← Using alert() is poor UX
  }
};
```

**Issues:**
1. No error handling on /billing/plans request
2. Hard redirects without confirmation
3. Using browser alert() instead of modal error
4. No loading timeout (stuck in loading state if network fails)
5. No validation of checkout_url before redirect

---

### 10. Modal Component Missing Key Props

**SEVERITY:** MEDIUM | **LINE NUMBERS:** 1189-1200

Modal component doesn't close on ESC or outside click properly:

```jsx
Line 1189-1200:
function Modal({ title, onClose, children }) {
  return (
    <div className="modal-overlay" onClick={onClose}>  // ← Closes on overlay click
      <div className="modal" onClick={e => e.stopPropagation()}>  // ← Prevents propagation
        ...
      </div>
    </div>
  );
}
```

**Issue:** Modal requires manual onClose handlers everywhere. No keyboard support (ESC key).

---

## MODERATE ISSUES

### 11. Responsive Design - Mobile Sidebar Hidden, Not Functional

**SEVERITY:** MEDIUM | **LINE NUMBERS:** 1009-1011

```css
@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); }  // Hidden
  .main-content { margin-left: 0; }
}
```

**Issue:** Sidebar is hidden on mobile with no toggle button. Users cannot navigate on mobile.

**Missing:** Hamburger menu button to show/hide sidebar.

---

### 12. Tables Not Sortable or Paginated

**SEVERITY:** MEDIUM | **LINE NUMBERS:** 1480-1525

Controls table (Frameworks page) renders all controls at once:

```jsx
Line 1480-1525:
<table className="controls-table">
  <thead>...</thead>
  <tbody>
    {filtered.map(ctrl => (  // ← Renders ALL filtered controls
      <tr key={ctrl.id}> ...
    ))}
  </tbody>
</table>
```

**Issues:**
1. No pagination - table becomes unwieldy with 100+ controls
2. No sorting by column (ID, Status, Severity, etc.)
3. Large datasets will cause performance issues
4. No scroll virtualization

---

### 13. Accessibility Issues

**SEVERITY:** MEDIUM | **MULTIPLE LINES**

#### A. Missing ARIA Labels (Lines 2225-2249)

```jsx
<button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} ...>
  <span className="nav-item-icon">{item.icon}</span>  // ← Icon only, no aria-label
  {item.label}
</button>
```

**Issue:** Icon-only buttons need aria-label for screen readers.

#### B. Focus States Missing

```css
Lines 627-630:
.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;  // ← Removes browser focus ring
  border-color: var(--primary);  // ← Provides replacement, but too subtle
}
```

**Issue:** Focus ring is removed and replaced with only border color. Not enough contrast for keyboard users.

#### C. No Keyboard Navigation in Nav

Nav items are buttons but don't have visible focus states when tabbed.

---

### 14. XSS Vulnerability in Policy Content

**SEVERITY:** HIGH | **LINE NUMBER:** 1829

```jsx
<div className="policy-content" dangerouslySetInnerHTML={{__html: simpleMarkdown(selected.content)}} />
```

**Issue:** `dangerouslySetInnerHTML` with untrusted content. If `selected.content` contains `<script>` or event handlers, they execute.

**Simple Markdown Function (Lines 1125-1144):**
```jsx
function simpleMarkdown(text) {
  // ...
  return html;  // ← Just replaces patterns. No sanitization.
}
```

**Attack Vector:** API returns `content: "<img src=x onerror='alert(1)'>"` → Executes in browser.

**Fix:** Use DOMPurify library or sanitize HTML.

---

### 15. Missing Null Checks on Object Properties

**SEVERITY:** MEDIUM | **MULTIPLE LINES**

```jsx
Line 1751: JSON.parse(selected.frameworks_affected || '[]').join(', ').toUpperCase()
// If frameworks_affected is invalid JSON, JSON.parse throws

Line 1754: JSON.parse(selected.industries_affected || '[]').join(', ')
// Same issue

Line 1900: {fw.name} — Compliance Report  // If fw is undefined, crash
```

---

### 16. Race Conditions in State Updates

**SEVERITY:** MEDIUM | **LINES:** 1427-1431, 1592-1598

```jsx
Line 1427-1431:
const updateStatus = async (controlId, status) => {
  await api.post(`/controls/${controlId}/status`, { status });
  loadControls(selectedFw);  // ← Triggers API call
  setEditingControl(null);
};
```

**Issue:** If two rapid updateStatus calls happen, loadControls() is called twice, creating race condition. The second response might overwrite the first.

**Similar issues in addEvidence (1592-1598), generatePolicy (1774-1781), etc.**

---

## MINOR ISSUES

### 17. Emojis in UI (Design Violation)

**SEVERITY:** LOW | **MULTIPLE LINES**

Design.md says "No emojis in UI" but they're used throughout:

```jsx
Line 1086-1094:  Icons use emojis (📎, ✅, 📄, 🛡️, 🔔)
Line 1798:       "🤖 Generate Policy"
Line 1817:       "📄" empty state icon
Line 1963:       "📊 Generate Report"
Line 2254:       "💳" billing icon
```

---

### 18. Hard-coded Demo Data

**SEVERITY:** LOW | **LINES:** 1302, 1342, 1996-2015, 2024-2028

```jsx
Line 1302: "Welcome back, Jordan. Here's your compliance overview."
Line 1342: Dashboard subtitle: "Welcome back, Jordan."
Line 1996: defaultValue="Acme SaaS Co."
Line 2024: defaultValue="Jordan Chen"
Line 2028: defaultValue="admin@acmesaas.com"
```

**Issue:** Hard-coded names and company data. Should pull from user/organization API.

---

### 19. Broken Navigation on Error

**SEVERITY:** LOW | **LINE:** 2225-2249

If api.get('/frameworks') fails and returns undefined, clicking "Frameworks" nav item sets page='frameworks' but FrameworksPage component has no error state:

```jsx
const [frameworks, setFrameworks] = useState([]);  // Defaults to []
useEffect(() => { api.get('/frameworks').then(setFrameworks); }, []);
// If API fails, frameworks stays []
// User sees empty Frameworks page with no error message
```

---

## MISSING FEATURES

### 20. No Confirmation Dialogs

**SEVERITY:** LOW | **LINE:** 2070

```jsx
window.location.href = result.checkout_url;  // Hard redirect without confirmation
```

No confirmation before redirecting to Stripe checkout. Users might accidentally navigate away.

---

### 21. No Loading Timeouts

**SEVERITY:** LOW | **MULTIPLE LINES**

Loading states have no timeout. If API hangs, user sees "Loading..." forever.

---

### 22. No Offline Detection

**SEVERITY:** LOW**

No indication if user is offline. API calls silently fail.

---

## API INTEGRATION ISSUES

### 23. All Fetch Calls Use Correct URL

**SEVERITY:** PASS | **LINE:** 1032

```jsx
window.CK_API_URL = 'https://web-production-be130.up.railway.app';
const API = (window.CK_API_URL || '') + '/api';
```

✅ Correctly configured to hit Railway production endpoint.

---

### 24. Missing Loading States on Submit Actions

**SEVERITY:** MEDIUM | **MULTIPLE LINES**

```jsx
Line 1682: <button className="btn btn-primary" onClick={addEvidence} disabled={!form.title}>
// No loading state while POST /evidence is in flight

Line 1832-1837: <button className="btn btn-primary" onClick={async () => {
  await api.put(`/policies/${selected.id}`, ...);
  const data = await api.get('/policies');
  setPolicies(data);
  setSelected(null);
}}>Approve Policy</button>
// No loading indicator, disabled state
```

---

## ROUTING ISSUES

### 25. All 7 Pages Accessible

**SEVERITY:** PASS | **LINE NUMBERS:** 2191-2211, 2224-2260

Navigation setup includes all required pages:

- ✅ Dashboard (Line 2202)
- ✅ Frameworks (Line 2203)
- ✅ Evidence (Line 2204)
- ✅ Alerts (Line 2205)
- ✅ Policies (Line 2206)
- ✅ Reports (Line 2207)
- ✅ Billing (Line 2208)
- ✅ Settings (Line 2209)

All pages have corresponding nav items (Lines 2224-2260).

---

## FORMS & VALIDATION

### 26. Minimal Form Validation

**SEVERITY:** MEDIUM | **LINES:** 1649-1682

```jsx
<button className="btn btn-primary" onClick={addEvidence} disabled={!form.title}>
  Add Evidence
</button>
```

**Issues:**
1. Only checks form.title is non-empty
2. No validation on description, type, source
3. No feedback if form submission fails
4. No duplicate prevention
5. Form state not cleared on error (only on success at line 1597)

---

### 27. Login Form Missing Validation

**SEVERITY:** MEDIUM | **LINES:** 1249-1270

```jsx
Line 1224:
if (email && password) {
  // No validation that email is valid format
  // No min length check on password
  // Simulated auth with setTimeout (not real)
}
```

---

## PERFORMANCE ISSUES

### 28. No Pagination or Virtualization

**SEVERITY:** MEDIUM | **MULTIPLE LINES**

Tables render all rows:

```jsx
Line 1493: {filtered.map(ctrl => (  // Could be 100+ controls
Line 1626: {evidence.map(ev => (     // Could be 1000+ items
Line 1728: {alerts.map(alert => (    // Could be 500+ alerts
```

**Impact:** Rendering 1000+ DOM nodes causes browser lag.

---

### 29. useCallback Misuse

**SEVERITY:** LOW | **LINES:** 2167-2174

```jsx
const loadDashboard = useCallback(async () => { ... }, []);
```

useCallback is unnecessary here since no props depend on it. Adds complexity without benefit.

---

## DATA DISPLAY ISSUES

### 30. Table Column Widths Hardcoded

**SEVERITY:** LOW | **LINES:** 1483-1489

```jsx
<th style={{width:'10%'}}>ID</th>
<th style={{width:'30%'}}>Control</th>
<th style={{width:'15%'}}>Category</th>
...
```

Hardcoded widths don't adapt to content. Can cause text overflow on mobile.

---

## SUMMARY

| Category | Critical | High | Medium | Low | Pass |
|----------|----------|------|--------|-----|------|
| Design | 2 | 0 | 0 | 1 | 0 |
| React | 0 | 2 | 3 | 2 | 0 |
| API | 0 | 1 | 4 | 0 | 1 |
| Forms | 0 | 1 | 2 | 0 | 0 |
| Routing | 0 | 0 | 0 | 0 | 1 |
| Accessibility | 0 | 0 | 3 | 0 | 0 |
| Performance | 0 | 0 | 2 | 1 | 0 |
| Security | 0 | 1 | 1 | 0 | 0 |

---

## TOP 5 PRIORITY FIXES

1. **Fix Design System** (CRITICAL) - Replace all dark colors with light mode per spec
2. **Remove All Gradients** (CRITICAL) - Use solid colors only
3. **Add Error Handling to API Layer** (CRITICAL) - Prevent silent failures
4. **Add Confirmation Dialogs** (HIGH) - Prevent accidental actions
5. **Fix XSS in Policy Content** (HIGH) - Sanitize dangerouslySetInnerHTML
