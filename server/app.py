"""
ComplianceKit API Server
Pure Python stdlib HTTP server with full REST API + Stripe billing
"""
import http.server
import json
import os
import sys
import uuid
import re
import urllib.request
import urllib.parse
import urllib.error
import base64
import hmac
import hashlib
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(__file__))
from database import get_db, init_db, seed_frameworks, seed_demo_data

PORT = int(os.environ.get('PORT', 3000))
STATIC_DIR = os.path.join(os.path.dirname(__file__), '..', 'public')
FRONTEND_URL = os.environ.get('FRONTEND_URL', f'http://localhost:{PORT}')

# Security constants
MAX_BODY_SIZE = 1024 * 1024  # 1MB
VALID_CONTROL_STATUSES = {'not_started', 'in_progress', 'compliant', 'non_compliant'}

# Stripe config from environment
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
STRIPE_PRICES = {
    'starter': os.environ.get('STRIPE_PRICE_STARTER', ''),
    'growth':  os.environ.get('STRIPE_PRICE_GROWTH', ''),
    'pro':     os.environ.get('STRIPE_PRICE_PRO', ''),
}

def stripe_request(method, path, data=None):
    """Make a Stripe API call without any SDK."""
    url = f'https://api.stripe.com/v1{path}'
    token = base64.b64encode(f'{STRIPE_SECRET_KEY}:'.encode()).decode()
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Stripe API error: {error_body}")  # Log for debugging
        return {"error": "Payment processing failed"}

class APIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        """Override to add security headers to all responses."""
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def _validate_status(self, status):
        """Validate control status is in allowed set."""
        if status not in VALID_CONTROL_STATUSES:
            self._json_response({"error": f"Invalid status: {status}"}, 400)
            return False
        return True

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _cors_headers(self):
        origin = self.headers.get('Origin', '')
        allowed = os.environ.get('FRONTEND_URL', f'http://localhost:{PORT}')
        if origin == allowed or not origin:
            self.send_header('Access-Control-Allow-Origin', allowed)
        # If origin doesn't match, no Access-Control-Allow-Origin header is sent,
        # which causes the browser to reject the cross-origin request.
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _json_response(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self._cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length > MAX_BODY_SIZE:
            return None
        if length:
            try:
                return json.loads(self.rfile.read(length))
            except json.JSONDecodeError:
                return None
        return {}

    def _route(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # API Routes
        routes = {
            'GET': [
                (r'^/api/dashboard$', self._dashboard),
                (r'^/api/frameworks$', self._get_frameworks),
                (r'^/api/frameworks/([^/]+)$', self._get_framework),
                (r'^/api/frameworks/([^/]+)/controls$', self._get_controls),
                (r'^/api/evidence$', self._get_evidence),
                (r'^/api/alerts$', self._get_alerts),
                (r'^/api/policies$', self._get_policies),
                (r'^/api/activity$', self._get_activity),
                (r'^/api/reports/compliance/([^/]+)$', self._get_compliance_report),
                (r'^/api/billing/plans$', self._get_plans),
                (r'^/api/billing/subscription$', self._get_subscription),
            ],
            'POST': [
                (r'^/api/controls/([^/]+)/status$', self._update_control_status),
                (r'^/api/evidence$', self._add_evidence),
                (r'^/api/policies/generate$', self._generate_policy),
                (r'^/api/frameworks/([^/]+)/subscribe$', self._subscribe_framework),
                (r'^/api/alerts/([^/]+)/read$', self._mark_alert_read),
                (r'^/api/billing/checkout$', self._create_checkout),
                (r'^/api/billing/portal$', self._create_portal),
                (r'^/api/billing/webhook$', self._stripe_webhook),
            ],
            'PUT': [
                (r'^/api/policies/([^/]+)$', self._update_policy),
            ],
            'DELETE': [
                (r'^/api/evidence/([^/]+)$', self._delete_evidence),
            ],
        }

        for pattern, handler in routes.get(method, []):
            match = re.match(pattern, path)
            if match:
                return handler(params, *match.groups())

        return None

    def do_GET(self):
        if self.path.startswith('/api/'):
            result = self._route('GET')
            if result is None:
                self._json_response({"error": "Not found"}, 404)
        else:
            # Serve static files with path traversal protection
            parsed = urlparse(self.path)
            filepath = os.path.normpath(os.path.join(STATIC_DIR, parsed.path.lstrip('/')))
            if not filepath.startswith(os.path.normpath(STATIC_DIR)):
                self._json_response({"error": "Forbidden"}, 403)
                return
            if os.path.isfile(filepath):
                super().do_GET()
            else:
                self.path = '/index.html'
                super().do_GET()

    def do_POST(self):
        result = self._route('POST')
        if result is None:
            self._json_response({"error": "Not found"}, 404)

    def do_PUT(self):
        result = self._route('PUT')
        if result is None:
            self._json_response({"error": "Not found"}, 404)

    def do_DELETE(self):
        result = self._route('DELETE')
        if result is None:
            self._json_response({"error": "Not found"}, 404)

    # ========= API HANDLERS =========

    def _dashboard(self, params):
        org_id = "demo-org"
        conn = get_db()

        # Get compliance scores per framework
        frameworks = conn.execute("""
            SELECT f.id, f.short_name, f.name, f.total_controls, f.category
            FROM frameworks f
            JOIN org_frameworks of2 ON f.id = of2.framework_id
            WHERE of2.org_id = ?
        """, (org_id,)).fetchall()

        framework_scores = []
        total_compliant = 0
        total_controls = 0

        for fw in frameworks:
            stats = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN cs.status = 'compliant' THEN 1 ELSE 0 END) as compliant,
                    SUM(CASE WHEN cs.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN cs.status = 'non_compliant' THEN 1 ELSE 0 END) as non_compliant,
                    SUM(CASE WHEN cs.status = 'not_started' THEN 1 ELSE 0 END) as not_started
                FROM controls c
                LEFT JOIN control_status cs ON c.id = cs.control_id AND cs.org_id = ?
                WHERE c.framework_id = ?
            """, (org_id, fw['id'])).fetchone()

            score = round((stats['compliant'] / stats['total'] * 100)) if stats['total'] > 0 else 0
            total_compliant += stats['compliant']
            total_controls += stats['total']

            framework_scores.append({
                "id": fw['id'],
                "name": fw['name'],
                "short_name": fw['short_name'],
                "category": fw['category'],
                "score": score,
                "total": stats['total'],
                "compliant": stats['compliant'],
                "in_progress": stats['in_progress'],
                "non_compliant": stats['non_compliant'],
                "not_started": stats['not_started'],
            })

        # Evidence stats
        evidence_stats = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
            FROM evidence WHERE org_id = ?
        """, (org_id,)).fetchone()

        # Unread alerts
        unread_alerts = conn.execute(
            "SELECT COUNT(*) as count FROM regulatory_alerts WHERE is_read = 0"
        ).fetchone()['count']

        # Critical alerts
        critical_alerts = conn.execute("""
            SELECT * FROM regulatory_alerts
            WHERE severity IN ('critical', 'high') AND is_read = 0
            ORDER BY published_at DESC LIMIT 5
        """).fetchall()

        # Recent activity
        activity = conn.execute("""
            SELECT * FROM activity_log WHERE org_id = ?
            ORDER BY created_at DESC LIMIT 10
        """, (org_id,)).fetchall()

        # Policies count
        policy_count = conn.execute(
            "SELECT COUNT(*) as count FROM policies WHERE org_id = ?", (org_id,)
        ).fetchone()['count']

        overall_score = round((total_compliant / total_controls * 100)) if total_controls > 0 else 0

        conn.close()

        self._json_response({
            "overall_score": overall_score,
            "frameworks": framework_scores,
            "evidence": dict(evidence_stats),
            "unread_alerts": unread_alerts,
            "critical_alerts": [dict(a) for a in critical_alerts],
            "recent_activity": [dict(a) for a in activity],
            "policy_count": policy_count,
            "org": {"name": "Acme SaaS Co.", "industry": "saas", "size": "11-25"},
        })

    def _get_frameworks(self, params):
        conn = get_db()
        org_id = "demo-org"
        frameworks = conn.execute("SELECT * FROM frameworks").fetchall()
        subscribed = conn.execute(
            "SELECT framework_id FROM org_frameworks WHERE org_id = ?", (org_id,)
        ).fetchall()
        sub_ids = {s['framework_id'] for s in subscribed}

        result = []
        for fw in frameworks:
            d = dict(fw)
            d['subscribed'] = fw['id'] in sub_ids
            result.append(d)

        conn.close()
        self._json_response(result)

    def _get_framework(self, params, fw_id):
        conn = get_db()
        fw = conn.execute("SELECT * FROM frameworks WHERE id = ?", (fw_id,)).fetchone()
        if not fw:
            conn.close()
            return self._json_response({"error": "Framework not found"}, 404)
        conn.close()
        self._json_response(dict(fw))

    def _get_controls(self, params, fw_id):
        org_id = "demo-org"
        conn = get_db()

        controls = conn.execute("""
            SELECT c.*, cs.status as compliance_status, cs.notes, cs.last_reviewed,
                   (SELECT COUNT(*) FROM evidence WHERE control_id = c.id AND org_id = ?) as evidence_count
            FROM controls c
            LEFT JOIN control_status cs ON c.id = cs.control_id AND cs.org_id = ?
            WHERE c.framework_id = ?
            ORDER BY c.control_id
        """, (org_id, org_id, fw_id)).fetchall()

        result = [dict(ctrl) for ctrl in controls]
        conn.close()
        self._json_response(result)

    def _get_evidence(self, params):
        org_id = "demo-org"
        conn = get_db()
        evidence = conn.execute("""
            SELECT e.*, c.control_id as control_ref, c.title as control_title, c.framework_id
            FROM evidence e
            LEFT JOIN controls c ON e.control_id = c.id
            WHERE e.org_id = ?
            ORDER BY e.uploaded_at DESC
        """, (org_id,)).fetchall()
        conn.close()
        self._json_response([dict(e) for e in evidence])

    def _get_alerts(self, params):
        conn = get_db()
        alerts = conn.execute(
            "SELECT * FROM regulatory_alerts ORDER BY published_at DESC"
        ).fetchall()
        conn.close()
        self._json_response([dict(a) for a in alerts])

    def _get_policies(self, params):
        org_id = "demo-org"
        conn = get_db()
        policies = conn.execute(
            "SELECT * FROM policies WHERE org_id = ? ORDER BY updated_at DESC", (org_id,)
        ).fetchall()
        conn.close()
        self._json_response([dict(p) for p in policies])

    def _get_activity(self, params):
        org_id = "demo-org"
        conn = get_db()
        activity = conn.execute(
            "SELECT * FROM activity_log WHERE org_id = ? ORDER BY created_at DESC LIMIT 50", (org_id,)
        ).fetchall()
        conn.close()
        self._json_response([dict(a) for a in activity])

    def _get_compliance_report(self, params, fw_id):
        org_id = "demo-org"
        conn = get_db()

        fw = conn.execute("SELECT * FROM frameworks WHERE id = ?", (fw_id,)).fetchone()
        if not fw:
            conn.close()
            return self._json_response({"error": "Framework not found"}, 404)

        controls = conn.execute("""
            SELECT c.*, cs.status as compliance_status, cs.notes
            FROM controls c
            LEFT JOIN control_status cs ON c.id = cs.control_id AND cs.org_id = ?
            WHERE c.framework_id = ?
            ORDER BY c.category, c.control_id
        """, (org_id, fw_id)).fetchall()

        evidence = conn.execute("""
            SELECT e.*, c.control_id as control_ref
            FROM evidence e
            JOIN controls c ON e.control_id = c.id
            WHERE c.framework_id = ? AND e.org_id = ?
        """, (fw_id, org_id)).fetchall()

        conn.close()

        self._json_response({
            "framework": dict(fw),
            "controls": [dict(c) for c in controls],
            "evidence": [dict(e) for e in evidence],
            "generated_at": datetime.now().isoformat(),
            "org": {"name": "Acme SaaS Co."},
        })

    def _update_control_status(self, params, control_id):
        body = self._read_body()
        if body is None:
            return self._json_response({"error": "Invalid request body"}, 400)

        org_id = "demo-org"
        status = body.get('status', 'not_started')

        if not self._validate_status(status):
            return

        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO control_status (id, org_id, control_id, status, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(org_id, control_id) DO UPDATE SET
                    status = excluded.status,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
            """, (str(uuid.uuid4()), org_id, control_id, status,
                  body.get('notes', ''), datetime.now().isoformat()))

            conn.execute(
                "INSERT INTO activity_log (id, org_id, user_id, action, entity_type, details) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), org_id, "demo-user", "control_updated", "control",
                 f"Control {control_id} updated to {status}")
            )

            conn.commit()
            conn.close()
            self._json_response({"success": True})
        except Exception as e:
            conn.rollback()
            conn.close()
            self._json_response({"error": "Database error"}, 500)

    def _add_evidence(self, params):
        body = self._read_body()
        if body is None:
            return self._json_response({"error": "Invalid request body"}, 400)

        org_id = "demo-org"
        ev_id = str(uuid.uuid4())
        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO evidence (id, org_id, control_id, title, description, type, source, status, uploaded_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 'demo-user')
            """, (ev_id, org_id, body.get('control_id'), body.get('title'),
                  body.get('description'), body.get('type', 'document'), body.get('source', 'Manual')))

            conn.execute(
                "INSERT INTO activity_log (id, org_id, user_id, action, entity_type, details) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), org_id, "demo-user", "evidence_uploaded", "evidence",
                 f"Evidence uploaded: {body.get('title')}")
            )

            conn.commit()
            conn.close()
            self._json_response({"success": True, "id": ev_id}, 201)
        except Exception as e:
            conn.rollback()
            conn.close()
            self._json_response({"error": "Database error"}, 500)

    def _generate_policy(self, params):
        body = self._read_body()
        if body is None:
            return self._json_response({"error": "Invalid request body"}, 400)

        org_id = "demo-org"
        policy_type = body.get('type', 'Acceptable Use Policy')
        framework = body.get('framework', 'soc2')

        # AI-generated policy templates
        templates = {
            "Acceptable Use Policy": {
                "title": "Acceptable Use Policy",
                "content": f"""# Acceptable Use Policy

## 1. Purpose
This Acceptable Use Policy establishes guidelines for the appropriate use of Acme SaaS Co.'s information technology resources, systems, and data. This policy is designed to protect our employees, customers, and the company from risks associated with improper use of technology resources.

## 2. Scope
This policy applies to all employees, contractors, consultants, temporary workers, and other personnel at Acme SaaS Co., including all personnel affiliated with third parties who access our information systems.

## 3. Policy Statements

### 3.1 General Use
- Company IT resources are provided primarily for business purposes
- Limited personal use is acceptable provided it does not interfere with job responsibilities, compromise security, or violate any company policy
- All activity on company systems is subject to monitoring and logging

### 3.2 Security Requirements
- Multi-factor authentication (MFA) must be enabled on all company accounts
- Workstations must be locked when unattended (max 5-minute auto-lock)
- Software installations require IT department approval
- Suspicious emails or security incidents must be reported within 1 hour

### 3.3 Prohibited Activities
- Unauthorized access or attempts to access systems, data, or accounts
- Sharing login credentials or authentication tokens
- Installing unauthorized or pirated software
- Circumventing security controls or monitoring systems
- Accessing, storing, or distributing inappropriate, illegal, or offensive content
- Using company resources for unauthorized commercial purposes or cryptocurrency mining
- Connecting unauthorized devices to the company network

### 3.4 Data Handling
- Data must be classified and handled according to the Data Classification Policy
- Sensitive data must be encrypted in transit (TLS 1.2+) and at rest (AES-256)
- Customer data must not be stored on personal devices without written approval
- Data sharing with external parties requires management and security team approval

### 3.5 Remote Work
- VPN must be used when accessing company resources from external networks
- Home networks must have WPA3 or WPA2 encryption enabled
- Company data must not be accessed from public or shared computers

## 4. Enforcement
Violations of this policy may result in disciplinary action, up to and including termination of employment and potential legal action. All suspected violations will be investigated by the Security team.

## 5. Review
This policy will be reviewed annually or upon significant changes to the threat landscape or regulatory requirements.

*Last Updated: {datetime.now().strftime('%B %d, %Y')}*
*Next Review: {datetime.now().strftime('%B %d, %Y').replace('2026', '2027')}*
*Owner: Security Team*
*Classification: Internal*"""
            },
            "Incident Response Plan": {
                "title": "Incident Response Plan",
                "content": f"""# Incident Response Plan

## 1. Purpose
This plan establishes procedures for identifying, containing, eradicating, and recovering from security incidents at Acme SaaS Co.

## 2. Incident Classification

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| Critical (P1) | Data breach, ransomware, system compromise | 15 minutes | CISO + Executive Team |
| High (P2) | Active intrusion attempt, malware detection | 1 hour | Security Lead |
| Medium (P3) | Suspicious activity, policy violation | 4 hours | Security Team |
| Low (P4) | Informational, minor policy deviation | 24 hours | IT Support |

## 3. Response Phases

### Phase 1: Detection & Identification
- Monitor SIEM alerts and security tool notifications
- Receive and triage employee reports via security@acmesaas.com
- Document initial findings in incident tracking system
- Assign severity classification

### Phase 2: Containment
- **Short-term**: Isolate affected systems, disable compromised accounts
- **Long-term**: Apply temporary fixes, implement additional monitoring
- Preserve forensic evidence before making changes
- Communicate status to stakeholders per escalation matrix

### Phase 3: Eradication
- Remove malware, backdoors, and unauthorized access
- Patch vulnerabilities that enabled the incident
- Reset credentials for affected accounts
- Verify eradication through scanning and monitoring

### Phase 4: Recovery
- Restore systems from verified clean backups
- Implement enhanced monitoring for recurrence
- Gradual return to normal operations
- Verify system integrity before full restoration

### Phase 5: Post-Incident Review
- Conduct lessons learned meeting within 5 business days
- Document root cause analysis
- Update procedures and controls as needed
- Brief executive team on findings and improvements

## 4. Breach Notification Requirements
- GDPR: 72 hours to supervisory authority
- HIPAA: 60 days to HHS, affected individuals, and media (if >500)
- State laws: Varies by jurisdiction (track in compliance system)
- Contractual: Per customer agreement SLAs

## 5. Contact Information
- Security Hotline: [CONFIGURE]
- Security Email: security@acmesaas.com
- CISO: [CONFIGURE]
- Legal Counsel: [CONFIGURE]
- Cyber Insurance: [CONFIGURE]

*Last Updated: {datetime.now().strftime('%B %d, %Y')}*"""
            },
            "Data Classification Policy": {
                "title": "Data Classification Policy",
                "content": f"""# Data Classification Policy

## 1. Purpose
This policy defines how data at Acme SaaS Co. is classified, handled, stored, and transmitted based on its sensitivity level.

## 2. Classification Levels

### Restricted (Highest Sensitivity)
**Examples**: Customer PII, payment data, authentication credentials, encryption keys, health records
**Handling**: Encrypted at rest and in transit. Access limited to need-to-know basis. Logged access. No personal device storage. Requires DPA for third-party sharing.

### Confidential
**Examples**: Internal financial data, employee records, proprietary source code, business strategies, customer contracts
**Handling**: Encrypted in transit. Access controlled by role. Internal sharing with manager approval. No public cloud storage without encryption.

### Internal
**Examples**: Internal communications, project plans, meeting notes, internal documentation, training materials
**Handling**: Available to all employees. Not to be shared externally without review. Standard access controls.

### Public
**Examples**: Marketing materials, published blog posts, public documentation, open-source code
**Handling**: No restrictions on distribution. Verify accuracy before publication. No sensitive data embedded.

## 3. Data Handling Requirements

| Requirement | Restricted | Confidential | Internal | Public |
|-------------|-----------|--------------|----------|--------|
| Encryption at rest | Required (AES-256) | Recommended | Optional | N/A |
| Encryption in transit | Required (TLS 1.2+) | Required | Recommended | Recommended |
| Access logging | Required | Required | Optional | N/A |
| Backup | Required | Required | Required | Optional |
| Retention limit | Per regulation | 7 years | 3 years | None |
| Disposal method | Crypto-shred | Secure delete | Standard delete | N/A |

## 4. Responsibilities
- **Data Owners**: Classify data, approve access, review periodically
- **Data Custodians**: Implement controls, manage storage, maintain backups
- **All Employees**: Handle data per classification, report mishandling

*Last Updated: {datetime.now().strftime('%B %d, %Y')}*"""
            },
            "Vendor Management Policy": {
                "title": "Vendor Management Policy",
                "content": f"""# Vendor Management Policy

## 1. Purpose
This policy establishes requirements for assessing, onboarding, monitoring, and offboarding third-party vendors who access Acme SaaS Co. systems or data.

## 2. Vendor Risk Tiers

| Tier | Criteria | Assessment Frequency | Examples |
|------|----------|---------------------|----------|
| Critical | Processes customer data, has system access | Annually + continuous monitoring | AWS, Stripe, Auth0 |
| High | Accesses internal data or systems | Annually | Slack, GitHub, HR platforms |
| Medium | Limited data access, business tools | Every 2 years | Marketing tools, analytics |
| Low | No data access, commodity services | At onboarding | Office supplies, facilities |

## 3. Assessment Requirements
- Security questionnaire (SIG Lite for Medium+, SIG Full for Critical)
- SOC 2 Type II report review (Critical and High vendors)
- Data Processing Agreement (DPA) execution for any vendor processing personal data
- Business Associate Agreement (BAA) for vendors accessing PHI
- Penetration test results review (Critical vendors)
- Insurance verification (Critical vendors)

## 4. Ongoing Monitoring
- Track vendor security posture changes via automated monitoring
- Review vendor incident disclosures within 48 hours
- Reassess vendors after any security incident
- Annual review of access permissions and data flows

## 5. Offboarding
- Revoke all access within 24 hours of contract termination
- Request data deletion confirmation
- Archive vendor assessment records per retention policy

*Last Updated: {datetime.now().strftime('%B %d, %Y')}*"""
            },
            "Access Control Policy": {
                "title": "Access Control Policy",
                "content": f"""# Access Control Policy

## 1. Purpose
This policy establishes requirements for managing access to Acme SaaS Co. information systems and data based on the principle of least privilege.

## 2. Access Principles
- **Least Privilege**: Users receive only the minimum access required for their role
- **Need to Know**: Access to data is granted based on business need
- **Separation of Duties**: Critical functions require multiple approvals
- **Defense in Depth**: Multiple layers of access controls

## 3. Authentication Requirements

| System Type | Minimum Requirement |
|-------------|-------------------|
| Production systems | MFA + SSH keys (no passwords) |
| Admin consoles | MFA + hardware security key |
| SaaS applications | MFA (TOTP or push) |
| VPN | MFA + certificate |
| Email | MFA (enforced via SSO) |

## 4. Access Lifecycle

### Provisioning
- Manager submits access request via ticketing system
- Security team reviews and approves within 1 business day
- IT provisions access per approved role template
- User completes security training before access activation

### Review
- Quarterly access reviews for all systems
- Monthly reviews for production and admin access
- Immediate review upon role change or transfer

### Deprovisioning
- Same-day revocation upon termination
- 24-hour revocation upon role change (for removed access)
- Automated deprovisioning via SCIM where supported

## 5. Privileged Access
- All privileged access requires justification and time-limited approval
- Admin actions logged and reviewed weekly
- Break-glass procedures documented and tested quarterly
- No shared admin accounts

*Last Updated: {datetime.now().strftime('%B %d, %Y')}*"""
            },
        }

        template = templates.get(policy_type, templates["Acceptable Use Policy"])

        policy_id = str(uuid.uuid4())
        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO policies (id, org_id, title, content, framework_id, status, created_by)
                VALUES (?, ?, ?, ?, ?, 'draft', 'demo-user')
            """, (policy_id, org_id, template["title"], template["content"], framework))

            conn.execute(
                "INSERT INTO activity_log (id, org_id, user_id, action, entity_type, details) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), org_id, "demo-user", "policy_generated", "policy",
                 f"AI-generated {template['title']}")
            )

            conn.commit()
            conn.close()

            self._json_response({"success": True, "id": policy_id, "title": template["title"], "content": template["content"]})
        except Exception as e:
            conn.rollback()
            conn.close()
            self._json_response({"error": "Database error"}, 500)

    def _subscribe_framework(self, params, fw_id):
        org_id = "demo-org"
        conn = get_db()

        existing = conn.execute(
            "SELECT id FROM org_frameworks WHERE org_id = ? AND framework_id = ?", (org_id, fw_id)
        ).fetchone()

        if existing:
            conn.close()
            return self._json_response({"error": "Already subscribed"}, 400)

        try:
            conn.execute(
                "INSERT INTO org_frameworks (id, org_id, framework_id) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), org_id, fw_id)
            )

            # Create control statuses
            controls = conn.execute("SELECT id FROM controls WHERE framework_id = ?", (fw_id,)).fetchall()
            for ctrl in controls:
                conn.execute(
                    "INSERT OR IGNORE INTO control_status (id, org_id, control_id, status) VALUES (?, ?, ?, 'not_started')",
                    (str(uuid.uuid4()), org_id, ctrl['id'])
                )

            conn.commit()
            conn.close()
            self._json_response({"success": True})
        except Exception as e:
            conn.rollback()
            conn.close()
            self._json_response({"error": "Database error"}, 500)

    def _mark_alert_read(self, params, alert_id):
        conn = get_db()
        try:
            conn.execute("UPDATE regulatory_alerts SET is_read = 1 WHERE id = ?", (alert_id,))
            conn.commit()
            conn.close()
            self._json_response({"success": True})
        except Exception as e:
            conn.rollback()
            conn.close()
            self._json_response({"error": "Database error"}, 500)

    def _update_policy(self, params, policy_id):
        body = self._read_body()
        if body is None:
            return self._json_response({"error": "Invalid request body"}, 400)

        conn = get_db()
        try:
            conn.execute("""
                UPDATE policies SET content = ?, status = ?, updated_at = ? WHERE id = ?
            """, (body.get('content'), body.get('status', 'draft'), datetime.now().isoformat(), policy_id))
            conn.commit()
            conn.close()
            self._json_response({"success": True})
        except Exception as e:
            conn.rollback()
            conn.close()
            self._json_response({"error": "Database error"}, 500)

    def _delete_evidence(self, params, ev_id):
        conn = get_db()
        try:
            conn.execute("DELETE FROM evidence WHERE id = ?", (ev_id,))
            conn.commit()
            conn.close()
            self._json_response({"success": True})
        except Exception as e:
            conn.rollback()
            conn.close()
            self._json_response({"error": "Database error"}, 500)

    # ========= BILLING HANDLERS =========

    def _get_plans(self, params):
        self._json_response({
            "plans": [
                {
                    "id": "starter",
                    "name": "Starter",
                    "price": 49,
                    "description": "For solo founders and micro-businesses",
                    "features": [
                        "1 compliance framework",
                        "Basic regulatory monitoring",
                        "Manual evidence collection",
                        "Audit-ready PDF exports",
                        "Email support"
                    ],
                    "price_id": STRIPE_PRICES.get('starter', ''),
                },
                {
                    "id": "growth",
                    "name": "Growth",
                    "price": 99,
                    "description": "The sweet spot for growing teams",
                    "popular": True,
                    "features": [
                        "Up to 3 frameworks",
                        "AI evidence auto-collection",
                        "AI policy generator",
                        "Priority regulatory alerts",
                        "10 tool integrations",
                        "Slack support"
                    ],
                    "price_id": STRIPE_PRICES.get('growth', ''),
                },
                {
                    "id": "pro",
                    "name": "Pro",
                    "price": 149,
                    "description": "For companies approaching enterprise",
                    "features": [
                        "Unlimited frameworks",
                        "Full automation suite",
                        "Custom integrations",
                        "White-label audit reports",
                        "Dedicated account manager",
                        "SSO & API access"
                    ],
                    "price_id": STRIPE_PRICES.get('pro', ''),
                },
            ]
        })

    def _get_subscription(self, params):
        org_id = "demo-org"
        conn = get_db()
        org = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
        conn.close()
        settings = json.loads(org['settings'] or '{}')
        self._json_response({
            "plan": settings.get('plan', 'trial'),
            "status": settings.get('subscription_status', 'trialing'),
            "stripe_customer_id": settings.get('stripe_customer_id'),
            "trial_ends_at": settings.get('trial_ends_at'),
            "current_period_end": settings.get('current_period_end'),
        })

    def _create_checkout(self, params):
        body = self._read_body()
        plan = body.get('plan', 'growth')
        org_id = "demo-org"

        if not STRIPE_SECRET_KEY:
            return self._json_response({"error": "Billing is not available right now."}, 503)

        price_id = STRIPE_PRICES.get(plan)
        if not price_id:
            return self._json_response({"error": "This plan is not available yet."}, 400)

        # Get or create Stripe customer
        conn = get_db()
        org = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
        conn.close()
        settings = json.loads(org['settings'] or '{}')
        customer_id = settings.get('stripe_customer_id')

        if not customer_id:
            customer = stripe_request('POST', '/customers', {
                'email': 'admin@acmesaas.com',
                'name': org['name'],
                'metadata[org_id]': org_id,
            })
            customer_id = customer.get('id')
            if customer_id:
                settings['stripe_customer_id'] = customer_id
                conn = get_db()
                conn.execute("UPDATE organizations SET settings = ? WHERE id = ?",
                             (json.dumps(settings), org_id))
                conn.commit()
                conn.close()

        # Create checkout session
        session = stripe_request('POST', '/checkout/sessions', {
            'customer': customer_id,
            'mode': 'subscription',
            'line_items[0][price]': price_id,
            'line_items[0][quantity]': '1',
            'success_url': f'{FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}',
            'cancel_url': f'{FRONTEND_URL}/billing',
            'subscription_data[trial_period_days]': '14',
            'allow_promotion_codes': 'true',
            'metadata[org_id]': org_id,
            'metadata[plan]': plan,
        })

        if 'url' not in session:
            print(f"Stripe checkout error: {session}")  # Log for debugging
            return self._json_response({"error": "Failed to create checkout session. Please try again."}, 400)

        self._json_response({"checkout_url": session['url'], "session_id": session['id']})

    def _create_portal(self, params):
        org_id = "demo-org"

        if not STRIPE_SECRET_KEY:
            return self._json_response({"error": "Stripe not configured."}, 400)

        conn = get_db()
        org = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
        conn.close()
        settings = json.loads(org['settings'] or '{}')
        customer_id = settings.get('stripe_customer_id')

        if not customer_id:
            return self._json_response({"error": "No Stripe customer found. Subscribe first."}, 400)

        session = stripe_request('POST', '/billing_portal/sessions', {
            'customer': customer_id,
            'return_url': f'{FRONTEND_URL}/billing',
        })

        if 'url' not in session:
            return self._json_response({"error": "Failed to create portal session."}, 400)

        self._json_response({"portal_url": session['url']})

    def _stripe_webhook(self, params):
        """Handle Stripe webhook events."""
        if not STRIPE_WEBHOOK_SECRET:
            return self._json_response({"error": "Webhook not configured"}, 503)

        length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(length)
        sig_header = self.headers.get('Stripe-Signature', '')

        # Require valid webhook signature
        if not sig_header:
            return self._json_response({"error": "Missing signature"}, 400)

        try:
            parts = {k: v for k, v in (p.split('=', 1) for p in sig_header.split(','))}
            timestamp = parts.get('t', '')
            sig = parts.get('v1', '')
            signed_payload = f"{timestamp}.".encode() + raw_body
            expected = hmac.new(STRIPE_WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, sig):
                return self._json_response({"error": "Invalid signature"}, 400)
        except Exception:
            return self._json_response({"error": "Webhook verification failed"}, 400)

        try:
            event = json.loads(raw_body)
        except json.JSONDecodeError:
            return self._json_response({"error": "Invalid JSON"}, 400)
        event_type = event.get('type', '')
        data = event.get('data', {}).get('object', {})

        try:
            if event_type in ('customer.subscription.created', 'customer.subscription.updated'):
                customer_id = data.get('customer')
                status = data.get('status')
                plan_name = 'growth'
                items = data.get('items', {}).get('data', [])
                if items:
                    price_id = items[0].get('price', {}).get('id', '')
                    for plan, pid in STRIPE_PRICES.items():
                        if pid == price_id:
                            plan_name = plan
                            break

                conn = get_db()
                orgs = conn.execute("SELECT id, settings FROM organizations").fetchall()
                for org in orgs:
                    s = json.loads(org['settings'] or '{}')
                    if s.get('stripe_customer_id') == customer_id:
                        s['plan'] = plan_name
                        s['subscription_status'] = status
                        s['current_period_end'] = data.get('current_period_end')
                        conn.execute("UPDATE organizations SET settings = ? WHERE id = ?",
                                     (json.dumps(s), org['id']))
                conn.commit()
                conn.close()

            elif event_type == 'customer.subscription.deleted':
                customer_id = data.get('customer')
                conn = get_db()
                orgs = conn.execute("SELECT id, settings FROM organizations").fetchall()
                for org in orgs:
                    s = json.loads(org['settings'] or '{}')
                    if s.get('stripe_customer_id') == customer_id:
                        s['plan'] = 'trial'
                        s['subscription_status'] = 'canceled'
                        conn.execute("UPDATE organizations SET settings = ? WHERE id = ?",
                                     (json.dumps(s), org['id']))
                conn.commit()
                conn.close()

            elif event_type == 'invoice.payment_failed':
                customer_id = data.get('customer')
                conn = get_db()
                orgs = conn.execute("SELECT id, settings FROM organizations").fetchall()
                for org in orgs:
                    s = json.loads(org['settings'] or '{}')
                    if s.get('stripe_customer_id') == customer_id:
                        s['subscription_status'] = 'past_due'
                        conn.execute("UPDATE organizations SET settings = ? WHERE id = ?",
                                     (json.dumps(s), org['id']))
                conn.commit()
                conn.close()
        except Exception as e:
            # Log but don't fail webhook processing
            print(f"Webhook processing error: {e}")

        self._json_response({"received": True})

    def log_message(self, format, *args):
        # Suppress request logging noise
        pass


def main():
    print("Initializing database...")
    init_db()
    seed_frameworks()
    seed_demo_data()
    print(f"Starting ComplianceKit server on port {PORT}...")
    print(f"Open http://localhost:{PORT}")

    server = http.server.HTTPServer(('0.0.0.0', PORT), APIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()

if __name__ == "__main__":
    main()
