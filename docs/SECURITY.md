# Aeviternus Security Model


## Overview

Security is designed around protecting:

- user data
- system integrity
- private memory
- runtime access


---

# Data Protection


Sensitive information is not stored in public repositories.


Excluded:

settings.env
data/
*.db
logs/
personal memory files


---

# Environment Variables


Secrets are stored externally:

Example:

DEEPSEEK_API_KEY
TELEGRAM_TOKEN
DIP_PASSWORD



They must never be committed.


---

# Filesystem Access


Aeviternus provides controlled filesystem interaction.


Protection:

- restricted directories
- logging
- backup before destructive actions


---

# Database Safety


Current:

- SQLite storage
- backups
- logging


Future:

- migrations
- transaction handling
- automated backups


---

# Future Security Improvements


Planned:

- authentication improvements
- permission system
- encrypted storage
- audit trail