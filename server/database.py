"""
ComplianceKit Database Layer
SQLite database with full compliance framework schema
"""
import sqlite3
import json
import uuid
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'compliancekit.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Organizations
    c.execute('''CREATE TABLE IF NOT EXISTS organizations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        industry TEXT,
        size TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        settings TEXT DEFAULT '{}'
    )''')

    # Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        org_id TEXT REFERENCES organizations(id),
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'member',
        password_hash TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )''')

    # Compliance Frameworks
    c.execute('''CREATE TABLE IF NOT EXISTS frameworks (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        short_name TEXT NOT NULL,
        description TEXT,
        version TEXT,
        category TEXT,
        total_controls INTEGER DEFAULT 0
    )''')

    # Controls (requirements within frameworks)
    c.execute('''CREATE TABLE IF NOT EXISTS controls (
        id TEXT PRIMARY KEY,
        framework_id TEXT REFERENCES frameworks(id),
        control_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT,
        severity TEXT DEFAULT 'medium',
        implementation_guidance TEXT
    )''')

    # Organization Framework Subscriptions
    c.execute('''CREATE TABLE IF NOT EXISTS org_frameworks (
        id TEXT PRIMARY KEY,
        org_id TEXT REFERENCES organizations(id),
        framework_id TEXT REFERENCES frameworks(id),
        status TEXT DEFAULT 'active',
        started_at TEXT DEFAULT (datetime('now')),
        UNIQUE(org_id, framework_id)
    )''')

    # Control Status (per org)
    c.execute('''CREATE TABLE IF NOT EXISTS control_status (
        id TEXT PRIMARY KEY,
        org_id TEXT REFERENCES organizations(id),
        control_id TEXT REFERENCES controls(id),
        status TEXT DEFAULT 'not_started',
        assignee_id TEXT,
        notes TEXT,
        last_reviewed TEXT,
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(org_id, control_id)
    )''')

    # Evidence Items
    c.execute('''CREATE TABLE IF NOT EXISTS evidence (
        id TEXT PRIMARY KEY,
        org_id TEXT REFERENCES organizations(id),
        control_id TEXT REFERENCES controls(id),
        title TEXT NOT NULL,
        description TEXT,
        type TEXT,
        source TEXT,
        file_path TEXT,
        status TEXT DEFAULT 'pending',
        uploaded_by TEXT,
        uploaded_at TEXT DEFAULT (datetime('now')),
        expires_at TEXT,
        metadata TEXT DEFAULT '{}'
    )''')

    # Policies (AI-generated)
    c.execute('''CREATE TABLE IF NOT EXISTS policies (
        id TEXT PRIMARY KEY,
        org_id TEXT REFERENCES organizations(id),
        title TEXT NOT NULL,
        content TEXT,
        framework_id TEXT,
        status TEXT DEFAULT 'draft',
        version INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        created_by TEXT
    )''')

    # Regulatory Alerts
    c.execute('''CREATE TABLE IF NOT EXISTS regulatory_alerts (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        summary TEXT,
        source TEXT,
        source_url TEXT,
        published_at TEXT,
        severity TEXT DEFAULT 'info',
        frameworks_affected TEXT DEFAULT '[]',
        industries_affected TEXT DEFAULT '[]',
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )''')

    # Audit Reports
    c.execute('''CREATE TABLE IF NOT EXISTS audit_reports (
        id TEXT PRIMARY KEY,
        org_id TEXT REFERENCES organizations(id),
        framework_id TEXT REFERENCES frameworks(id),
        title TEXT NOT NULL,
        generated_at TEXT DEFAULT (datetime('now')),
        data TEXT,
        status TEXT DEFAULT 'generated'
    )''')

    # Activity Log
    c.execute('''CREATE TABLE IF NOT EXISTS activity_log (
        id TEXT PRIMARY KEY,
        org_id TEXT REFERENCES organizations(id),
        user_id TEXT,
        action TEXT NOT NULL,
        entity_type TEXT,
        entity_id TEXT,
        details TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )''')

    # Performance indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_control_status_org_control ON control_status(org_id, control_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_evidence_org ON evidence(org_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_evidence_org_control ON evidence(org_id, control_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_controls_framework ON controls(framework_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_org_frameworks_org ON org_frameworks(org_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_policies_org ON policies(org_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_activity_log_org ON activity_log(org_id)")

    conn.commit()
    conn.close()

def seed_frameworks():
    """Seed real compliance framework data"""
    conn = get_db()
    c = conn.cursor()

    # Check if already seeded
    count = c.execute("SELECT COUNT(*) FROM frameworks").fetchone()[0]
    if count > 0:
        conn.close()
        return

    frameworks = [
        {
            "id": "soc2",
            "name": "SOC 2 Type II",
            "short_name": "SOC 2",
            "description": "Service Organization Control 2 - Trust Services Criteria for security, availability, processing integrity, confidentiality, and privacy.",
            "version": "2022",
            "category": "Security",
            "controls": [
                {"id": "CC1.1", "title": "COSO Principle 1: Integrity and Ethical Values", "category": "Control Environment", "severity": "high", "desc": "The entity demonstrates a commitment to integrity and ethical values.", "guidance": "Establish a code of conduct. Ensure leadership models ethical behavior. Create whistleblower policies."},
                {"id": "CC1.2", "title": "COSO Principle 2: Board Independence", "category": "Control Environment", "severity": "medium", "desc": "The board of directors demonstrates independence from management and exercises oversight.", "guidance": "Document board charter. Maintain independent directors. Regular board meetings with documented minutes."},
                {"id": "CC1.3", "title": "COSO Principle 3: Management Structure", "category": "Control Environment", "severity": "medium", "desc": "Management establishes structures, reporting lines, and appropriate authorities.", "guidance": "Create org chart. Define reporting structure. Document authority levels and approval chains."},
                {"id": "CC2.1", "title": "COSO Principle 13: Quality Information", "category": "Information & Communication", "severity": "high", "desc": "The entity obtains or generates relevant, quality information.", "guidance": "Implement logging and monitoring. Use SIEM tools. Ensure data quality controls."},
                {"id": "CC2.2", "title": "COSO Principle 14: Internal Communication", "category": "Information & Communication", "severity": "medium", "desc": "The entity internally communicates information necessary to support functioning.", "guidance": "Regular security awareness training. Internal communication policies. Incident communication procedures."},
                {"id": "CC3.1", "title": "COSO Principle 6: Risk Objectives", "category": "Risk Assessment", "severity": "high", "desc": "The entity specifies objectives with sufficient clarity to enable identification of risks.", "guidance": "Annual risk assessment. Document risk appetite. Maintain risk register."},
                {"id": "CC3.2", "title": "COSO Principle 7: Risk Identification", "category": "Risk Assessment", "severity": "high", "desc": "The entity identifies risks to the achievement of its objectives.", "guidance": "Threat modeling. Vulnerability assessments. Third-party risk assessments."},
                {"id": "CC4.1", "title": "COSO Principle 16: Monitoring Activities", "category": "Monitoring", "severity": "high", "desc": "The entity selects, develops, and performs ongoing and/or separate evaluations.", "guidance": "Continuous monitoring tools. Regular internal audits. Automated compliance checks."},
                {"id": "CC5.1", "title": "COSO Principle 10: Control Activities", "category": "Control Activities", "severity": "high", "desc": "The entity selects and develops control activities that mitigate risks.", "guidance": "Implement access controls. Change management procedures. Segregation of duties."},
                {"id": "CC5.2", "title": "COSO Principle 11: Technology Controls", "category": "Control Activities", "severity": "high", "desc": "The entity selects and develops general control activities over technology.", "guidance": "Firewall configurations. Encryption standards. Endpoint protection."},
                {"id": "CC6.1", "title": "Logical and Physical Access", "category": "Logical & Physical Access", "severity": "critical", "desc": "The entity implements logical access security controls.", "guidance": "MFA enforcement. RBAC implementation. Password policies. SSH key management."},
                {"id": "CC6.2", "title": "User Authentication", "category": "Logical & Physical Access", "severity": "critical", "desc": "Prior to issuing system credentials, the entity registers and authorizes new users.", "guidance": "User provisioning process. Background checks. Access request workflows."},
                {"id": "CC6.3", "title": "Access Removal", "category": "Logical & Physical Access", "severity": "critical", "desc": "The entity removes access to protected information when no longer required.", "guidance": "Offboarding procedures. Quarterly access reviews. Automated deprovisioning."},
                {"id": "CC7.1", "title": "Threat Detection", "category": "System Operations", "severity": "critical", "desc": "The entity uses detection and monitoring procedures to identify changes to configurations.", "guidance": "IDS/IPS deployment. File integrity monitoring. Security event alerting."},
                {"id": "CC7.2", "title": "Anomaly Monitoring", "category": "System Operations", "severity": "high", "desc": "The entity monitors system components for anomalies that are indicative of malicious acts.", "guidance": "SIEM configuration. Anomaly detection rules. 24/7 monitoring or managed SOC."},
                {"id": "CC7.3", "title": "Security Incident Response", "category": "System Operations", "severity": "critical", "desc": "The entity evaluates security events to determine whether they could constitute incidents.", "guidance": "Incident response plan. Incident classification matrix. Response team assignments."},
                {"id": "CC7.4", "title": "Incident Remediation", "category": "System Operations", "severity": "high", "desc": "The entity responds to identified security incidents by executing a defined response process.", "guidance": "Remediation procedures. Post-incident reviews. Lessons learned documentation."},
                {"id": "CC8.1", "title": "Change Management", "category": "Change Management", "severity": "high", "desc": "The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, and implements changes.", "guidance": "Change advisory board. Code review requirements. Staging environment testing. Rollback procedures."},
                {"id": "CC9.1", "title": "Vendor Risk Management", "category": "Risk Mitigation", "severity": "high", "desc": "The entity identifies, selects, and develops risk mitigation activities for risks from business partners.", "guidance": "Vendor assessment questionnaires. Annual vendor reviews. SLA monitoring."},
                {"id": "A1.1", "title": "System Availability", "category": "Availability", "severity": "high", "desc": "The entity maintains, monitors, and evaluates current processing capacity and availability.", "guidance": "Uptime monitoring. Capacity planning. Auto-scaling configuration. SLA tracking."},
                {"id": "A1.2", "title": "Disaster Recovery", "category": "Availability", "severity": "critical", "desc": "The entity authorizes, designs, develops and implements recovery procedures.", "guidance": "DR plan. Backup procedures. RTO/RPO definitions. Annual DR testing."},
                {"id": "C1.1", "title": "Confidential Information", "category": "Confidentiality", "severity": "high", "desc": "The entity identifies and maintains confidential information.", "guidance": "Data classification policy. Encryption at rest and in transit. DLP tools."},
                {"id": "PI1.1", "title": "Processing Integrity", "category": "Processing Integrity", "severity": "medium", "desc": "The entity obtains or generates, uses, and communicates relevant quality information.", "guidance": "Input validation. Data reconciliation. Error handling procedures."},
                {"id": "P1.1", "title": "Privacy Notice", "category": "Privacy", "severity": "high", "desc": "The entity provides notice to data subjects about its privacy practices.", "guidance": "Privacy policy. Cookie consent. Data collection disclosure."},
            ]
        },
        {
            "id": "hipaa",
            "name": "HIPAA Security Rule",
            "short_name": "HIPAA",
            "description": "Health Insurance Portability and Accountability Act - Security standards for protecting electronic protected health information (ePHI).",
            "version": "2024",
            "category": "Healthcare",
            "controls": [
                {"id": "164.308(a)(1)", "title": "Security Management Process", "category": "Administrative Safeguards", "severity": "critical", "desc": "Implement policies and procedures to prevent, detect, contain, and correct security violations.", "guidance": "Risk analysis. Risk management plan. Sanction policy. Information system activity review."},
                {"id": "164.308(a)(2)", "title": "Assigned Security Responsibility", "category": "Administrative Safeguards", "severity": "high", "desc": "Identify the security official responsible for developing and implementing security policies.", "guidance": "Designate a HIPAA Security Officer. Document role and responsibilities."},
                {"id": "164.308(a)(3)", "title": "Workforce Security", "category": "Administrative Safeguards", "severity": "high", "desc": "Implement policies and procedures to ensure workforce members have appropriate access.", "guidance": "Authorization procedures. Workforce clearance. Termination procedures."},
                {"id": "164.308(a)(4)", "title": "Information Access Management", "category": "Administrative Safeguards", "severity": "critical", "desc": "Implement policies and procedures for authorizing access to ePHI.", "guidance": "Access authorization. Access establishment and modification. Isolating healthcare clearinghouse functions."},
                {"id": "164.308(a)(5)", "title": "Security Awareness and Training", "category": "Administrative Safeguards", "severity": "high", "desc": "Implement a security awareness and training program for all workforce members.", "guidance": "Security reminders. Protection from malicious software. Login monitoring. Password management training."},
                {"id": "164.308(a)(6)", "title": "Security Incident Procedures", "category": "Administrative Safeguards", "severity": "critical", "desc": "Implement policies and procedures to address security incidents.", "guidance": "Response and reporting procedures. Incident documentation. Breach notification plan."},
                {"id": "164.308(a)(7)", "title": "Contingency Plan", "category": "Administrative Safeguards", "severity": "critical", "desc": "Establish policies and procedures for responding to an emergency.", "guidance": "Data backup plan. Disaster recovery plan. Emergency mode operation plan. Testing and revision."},
                {"id": "164.308(a)(8)", "title": "Evaluation", "category": "Administrative Safeguards", "severity": "high", "desc": "Perform periodic technical and nontechnical evaluation of security policies.", "guidance": "Annual security evaluation. Compliance audit schedule. Remediation tracking."},
                {"id": "164.310(a)(1)", "title": "Facility Access Controls", "category": "Physical Safeguards", "severity": "high", "desc": "Implement policies to limit physical access to electronic information systems.", "guidance": "Contingency operations. Facility security plan. Access control and validation. Maintenance records."},
                {"id": "164.310(b)", "title": "Workstation Use", "category": "Physical Safeguards", "severity": "medium", "desc": "Implement policies specifying proper functions and physical attributes of workstations.", "guidance": "Workstation use policy. Screen lock requirements. Clean desk policy."},
                {"id": "164.310(c)", "title": "Workstation Security", "category": "Physical Safeguards", "severity": "medium", "desc": "Implement physical safeguards for all workstations that access ePHI.", "guidance": "Physical security measures. Cable locks. Restricted areas."},
                {"id": "164.310(d)(1)", "title": "Device and Media Controls", "category": "Physical Safeguards", "severity": "high", "desc": "Implement policies governing the receipt and removal of hardware and electronic media.", "guidance": "Disposal procedures. Media re-use. Accountability. Data backup and storage."},
                {"id": "164.312(a)(1)", "title": "Access Control", "category": "Technical Safeguards", "severity": "critical", "desc": "Implement technical policies to allow access only to authorized persons.", "guidance": "Unique user IDs. Emergency access procedures. Automatic logoff. Encryption and decryption."},
                {"id": "164.312(b)", "title": "Audit Controls", "category": "Technical Safeguards", "severity": "high", "desc": "Implement mechanisms to record and examine activity in systems containing ePHI.", "guidance": "Audit logging. Log review procedures. Log retention. SIEM integration."},
                {"id": "164.312(c)(1)", "title": "Integrity", "category": "Technical Safeguards", "severity": "high", "desc": "Implement policies to protect ePHI from improper alteration or destruction.", "guidance": "Mechanism to authenticate ePHI. Data integrity verification."},
                {"id": "164.312(d)", "title": "Person or Entity Authentication", "category": "Technical Safeguards", "severity": "critical", "desc": "Implement procedures to verify the identity of persons seeking access to ePHI.", "guidance": "MFA implementation. Biometric authentication where appropriate. Token-based auth."},
                {"id": "164.312(e)(1)", "title": "Transmission Security", "category": "Technical Safeguards", "severity": "critical", "desc": "Implement measures to guard against unauthorized access to ePHI during transmission.", "guidance": "Integrity controls. Encryption (TLS 1.2+). VPN for remote access."},
            ]
        },
        {
            "id": "gdpr",
            "name": "General Data Protection Regulation",
            "short_name": "GDPR",
            "description": "EU regulation on data protection and privacy for all individuals within the European Union and European Economic Area.",
            "version": "2018 (Amended 2024)",
            "category": "Privacy",
            "controls": [
                {"id": "Art.5", "title": "Principles of Processing", "category": "Data Processing Principles", "severity": "critical", "desc": "Personal data shall be processed lawfully, fairly and in a transparent manner.", "guidance": "Document lawful basis for each processing activity. Data minimization review. Purpose limitation documentation."},
                {"id": "Art.6", "title": "Lawfulness of Processing", "category": "Data Processing Principles", "severity": "critical", "desc": "Processing is lawful only with valid legal basis.", "guidance": "Identify and document legal basis (consent, contract, legal obligation, vital interests, public task, legitimate interests)."},
                {"id": "Art.7", "title": "Conditions for Consent", "category": "Consent", "severity": "high", "desc": "Where processing is based on consent, the controller must demonstrate consent was given.", "guidance": "Consent management platform. Granular consent options. Easy withdrawal mechanism. Consent records."},
                {"id": "Art.12", "title": "Transparent Information", "category": "Data Subject Rights", "severity": "high", "desc": "Information provided to data subjects must be concise, transparent, intelligible.", "guidance": "Privacy notice in plain language. Layered privacy notices. Easy-to-find privacy information."},
                {"id": "Art.13-14", "title": "Information to be Provided", "category": "Data Subject Rights", "severity": "high", "desc": "Specific information must be provided when personal data is collected.", "guidance": "Identity of controller. Contact details of DPO. Purposes and legal basis. Recipients. Transfer information."},
                {"id": "Art.15", "title": "Right of Access", "category": "Data Subject Rights", "severity": "high", "desc": "Data subjects have the right to obtain confirmation and access to their personal data.", "guidance": "Subject access request (SAR) process. Identity verification. Response within 30 days. Secure delivery of data."},
                {"id": "Art.16", "title": "Right to Rectification", "category": "Data Subject Rights", "severity": "medium", "desc": "Data subjects have the right to have inaccurate personal data corrected.", "guidance": "Rectification request process. Data accuracy checks. Notification to recipients."},
                {"id": "Art.17", "title": "Right to Erasure", "category": "Data Subject Rights", "severity": "high", "desc": "Data subjects have the right to have personal data erased (right to be forgotten).", "guidance": "Erasure request workflow. Criteria evaluation. Backup handling. Third-party notification."},
                {"id": "Art.20", "title": "Right to Data Portability", "category": "Data Subject Rights", "severity": "medium", "desc": "Data subjects have the right to receive their personal data in a structured format.", "guidance": "Export functionality. Machine-readable format (JSON/CSV). Direct transfer mechanism."},
                {"id": "Art.25", "title": "Data Protection by Design", "category": "Technical Measures", "severity": "critical", "desc": "Implement appropriate technical measures designed to implement data-protection principles.", "guidance": "Privacy impact assessments. Default privacy settings. Pseudonymization. Data minimization in system design."},
                {"id": "Art.28", "title": "Processor Agreements", "category": "Third Parties", "severity": "high", "desc": "Processing by a processor shall be governed by a contract.", "guidance": "Data processing agreements (DPAs). Sub-processor management. Audit rights. Security requirements."},
                {"id": "Art.30", "title": "Records of Processing", "category": "Documentation", "severity": "high", "desc": "Each controller shall maintain a record of processing activities.", "guidance": "ROPA (Record of Processing Activities). Regular updates. Categories of data subjects and data. Retention periods."},
                {"id": "Art.32", "title": "Security of Processing", "category": "Technical Measures", "severity": "critical", "desc": "Implement appropriate technical and organizational measures to ensure security.", "guidance": "Pseudonymization and encryption. Ensure confidentiality, integrity, availability. Regular testing. Resilience of systems."},
                {"id": "Art.33", "title": "Breach Notification to Authority", "category": "Breach Response", "severity": "critical", "desc": "Notify supervisory authority within 72 hours of becoming aware of a personal data breach.", "guidance": "Breach detection procedures. 72-hour notification process. Documentation of breaches. Communication templates."},
                {"id": "Art.34", "title": "Breach Notification to Data Subjects", "category": "Breach Response", "severity": "critical", "desc": "Communicate personal data breach to affected data subjects when high risk.", "guidance": "Risk assessment criteria. Communication procedures. Plain language notifications."},
                {"id": "Art.35", "title": "Data Protection Impact Assessment", "category": "Risk Management", "severity": "high", "desc": "Carry out a DPIA where processing is likely to result in high risk.", "guidance": "DPIA methodology. Systematic assessment. Consultation with DPO. Mitigation measures."},
                {"id": "Art.37", "title": "Data Protection Officer", "category": "Governance", "severity": "high", "desc": "Designate a data protection officer in required circumstances.", "guidance": "DPO appointment criteria. Independence requirements. Contact details publication. Adequate resources."},
                {"id": "Art.44-49", "title": "International Transfers", "category": "Cross-Border", "severity": "high", "desc": "Transfers of personal data to third countries require appropriate safeguards.", "guidance": "Adequacy decisions. Standard contractual clauses. Binding corporate rules. Transfer impact assessments."},
            ]
        }
    ]

    for fw in frameworks:
        c.execute(
            "INSERT INTO frameworks (id, name, short_name, description, version, category, total_controls) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (fw["id"], fw["name"], fw["short_name"], fw["description"], fw["version"], fw["category"], len(fw["controls"]))
        )
        for ctrl in fw["controls"]:
            c.execute(
                "INSERT INTO controls (id, framework_id, control_id, title, description, category, severity, implementation_guidance) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (f"{fw['id']}_{ctrl['id']}", fw["id"], ctrl["id"], ctrl["title"], ctrl["desc"], ctrl["category"], ctrl["severity"], ctrl["guidance"])
            )

    conn.commit()
    conn.close()

def seed_demo_data():
    """Seed demo organization with realistic data"""
    conn = get_db()
    c = conn.cursor()

    count = c.execute("SELECT COUNT(*) FROM organizations").fetchone()[0]
    if count > 0:
        conn.close()
        return

    org_id = "demo-org"
    user_id = "demo-user"

    # Create demo org
    c.execute("INSERT INTO organizations (id, name, industry, size) VALUES (?, ?, ?, ?)",
              (org_id, "Acme SaaS Co.", "saas", "11-25"))

    # Create demo user
    c.execute("INSERT INTO users (id, org_id, email, name, role) VALUES (?, ?, ?, ?, ?)",
              (user_id, org_id, "admin@acmesaas.com", "Jordan Chen", "admin"))

    # Subscribe to SOC 2 and GDPR
    c.execute("INSERT INTO org_frameworks (id, org_id, framework_id) VALUES (?, ?, ?)",
              (str(uuid.uuid4()), org_id, "soc2"))
    c.execute("INSERT INTO org_frameworks (id, org_id, framework_id) VALUES (?, ?, ?)",
              (str(uuid.uuid4()), org_id, "gdpr"))

    # Set some control statuses for SOC 2
    import random
    controls = c.execute("SELECT id FROM controls WHERE framework_id IN ('soc2', 'gdpr')").fetchall()
    statuses = ['compliant', 'compliant', 'compliant', 'in_progress', 'in_progress', 'not_started', 'non_compliant']

    for ctrl in controls:
        status = random.choice(statuses)
        c.execute(
            "INSERT INTO control_status (id, org_id, control_id, status, updated_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), org_id, ctrl['id'], status, datetime.now().isoformat())
        )

    # Add some evidence
    evidence_items = [
        ("MFA Enforcement Screenshot", "Screenshot showing MFA is enforced for all users", "screenshot", "Google Workspace Admin"),
        ("Access Review Q1 2026", "Quarterly access review completed March 2026", "document", "Internal Audit"),
        ("Encryption Configuration", "TLS 1.3 configuration for all endpoints", "config", "AWS Console"),
        ("Security Training Completion", "All employees completed annual security training", "certificate", "KnowBe4"),
        ("Incident Response Plan v3.1", "Updated incident response plan", "policy", "Internal"),
        ("Vulnerability Scan Report", "Monthly vulnerability scan results", "report", "Qualys"),
        ("Vendor Risk Assessment - AWS", "Annual vendor risk assessment for AWS", "assessment", "Internal"),
        ("Data Processing Agreement - Stripe", "Signed DPA with Stripe", "contract", "Legal"),
        ("Privacy Policy v2.4", "Updated privacy policy with AI disclosure", "policy", "Legal"),
        ("Backup Verification Log", "Monthly backup restoration test results", "log", "DevOps"),
    ]

    soc2_controls = c.execute("SELECT id FROM controls WHERE framework_id = 'soc2'").fetchall()
    for i, (title, desc, etype, source) in enumerate(evidence_items):
        ctrl = soc2_controls[i % len(soc2_controls)]
        c.execute(
            "INSERT INTO evidence (id, org_id, control_id, title, description, type, source, status, uploaded_by, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), org_id, ctrl['id'], title, desc, etype, source,
             random.choice(['approved', 'approved', 'pending', 'approved']),
             user_id, datetime.now().isoformat())
        )

    # Add regulatory alerts
    alerts = [
        ("FTC Finalizes AI Transparency Rule", "The Federal Trade Commission has finalized rules requiring businesses to disclose AI-generated content and automated decision-making processes. Effective July 1, 2026.", "Federal Trade Commission", "critical", '["soc2","gdpr"]', '["saas","healthcare","fintech"]'),
        ("EU AI Act Compliance Deadline Approaching", "Organizations must comply with EU AI Act risk classification requirements by August 2026. High-risk AI systems require conformity assessments.", "European Commission", "high", '["gdpr"]', '["saas","healthcare"]'),
        ("NIST Cybersecurity Framework 2.1 Released", "NIST has released CSF 2.1 with expanded governance and supply chain risk management guidance.", "NIST", "medium", '["soc2"]', '["saas","fintech"]'),
        ("California Privacy Rights Act Update", "CPRA enforcement actions increased 340% in Q1 2026. New automated decision-making requirements now active.", "California Privacy Protection Agency", "high", '["gdpr"]', '["saas","ecommerce"]'),
        ("SEC Cybersecurity Incident Reporting Changes", "SEC has shortened the cybersecurity incident materiality determination window from 4 days to 48 hours.", "SEC", "critical", '["soc2"]', '["fintech","saas"]'),
        ("HIPAA Right of Access Initiative Expansion", "OCR announces expanded enforcement of patient right of access, including digital health platforms.", "HHS OCR", "high", '["hipaa"]', '["healthcare"]'),
    ]

    for title, summary, source, severity, fw, ind in alerts:
        c.execute(
            "INSERT INTO regulatory_alerts (id, title, summary, source, severity, frameworks_affected, industries_affected, published_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), title, summary, source, severity, fw, ind, datetime.now().isoformat())
        )

    # Add activity log
    activities = [
        ("evidence_uploaded", "evidence", "MFA Enforcement Screenshot uploaded"),
        ("control_updated", "control", "CC6.1 marked as compliant"),
        ("policy_generated", "policy", "AI-generated Acceptable Use Policy"),
        ("framework_added", "framework", "GDPR framework activated"),
        ("alert_received", "alert", "FTC AI Transparency Rule alert"),
        ("evidence_approved", "evidence", "Vendor Risk Assessment approved"),
        ("report_generated", "report", "Q1 2026 SOC 2 compliance report generated"),
        ("control_updated", "control", "Art.32 Security of Processing in progress"),
    ]

    for action, entity_type, details in activities:
        c.execute(
            "INSERT INTO activity_log (id, org_id, user_id, action, entity_type, details) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), org_id, user_id, action, entity_type, details)
        )

    # Add a sample policy
    c.execute(
        "INSERT INTO policies (id, org_id, title, content, framework_id, status, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), org_id, "Acceptable Use Policy",
         "# Acceptable Use Policy\n\n## Purpose\nThis policy establishes acceptable use guidelines for Acme SaaS Co. information systems and resources.\n\n## Scope\nThis policy applies to all employees, contractors, and third-party users who access company systems.\n\n## Policy\n\n### General Use\n- Company systems are provided primarily for business purposes\n- Limited personal use is permitted if it does not interfere with work duties\n- All usage is subject to monitoring and audit\n\n### Prohibited Activities\n- Unauthorized access to systems or data\n- Installation of unauthorized software\n- Sharing credentials with others\n- Accessing inappropriate or illegal content\n- Using company systems for personal commercial activities\n\n### Security Requirements\n- Use multi-factor authentication on all accounts\n- Lock workstations when unattended\n- Report suspected security incidents immediately\n- Keep software and systems updated\n\n### Data Handling\n- Classify data according to company data classification policy\n- Encrypt sensitive data in transit and at rest\n- Do not store sensitive data on personal devices without approval\n\n## Enforcement\nViolations may result in disciplinary action up to and including termination.",
         "soc2", "approved", user_id)
    )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_frameworks()
    seed_demo_data()
    print("Database initialized and seeded successfully.")
