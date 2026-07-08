# Security Policy

## Supported Versions

Aeviternus is currently under active development.

Supported versions:

| Version | Supported |
|---|---|
| v2.x | Yes |

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