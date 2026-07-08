# Security Policy

## Supported Versions

Aeviternus is currently under active development.

Supported versions:

| Version | Supported |
|---|---|
| v0.2.x | Yes |

---

# Reporting a Vulnerability

If you discover a security issue, please do not open a public issue.

Report vulnerabilities privately through GitHub Security Advisories.

When reporting a vulnerability, please provide:

- description of the issue
- affected component
- reproduction steps
- potential impact

---

# Responsible Disclosure Policy

We appreciate responsible disclosure of security vulnerabilities.

## Process

1. Report the vulnerability privately through GitHub Security Advisories
2. We will acknowledge receipt within 48 hours
3. We will investigate and assess the severity
4. We will provide a timeline for remediation
5. We will coordinate disclosure with the reporter
6. We will credit the reporter in the fix

## Timeline

- Critical vulnerabilities: 7 days
- High severity: 14 days
- Medium severity: 30 days
- Low severity: 90 days

These timelines may be adjusted based on complexity and coordination requirements.

---

# Security Principles

Aeviternus follows:

- No hardcoded secrets
- Environment-based configuration
- Local-first architecture
- Input validation and sanitization
- Runtime logging
- Explicit permission boundaries
- Controlled system access

---

# Sensitive Data

Private runtime data is excluded from the public repository.

Protected data includes:

- databases
- personal memory
- system prompts
- private identity files
- runtime logs
- environment configuration files
- API credentials

Sensitive information must never be committed to version control.