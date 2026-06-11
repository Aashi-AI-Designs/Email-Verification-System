# Email Verification System

A full-stack email verification tool built with **FastAPI**, **PostgreSQL**, and **HTML/JS**. Validates email format, checks DNS/MX records, detects disposable domains, and flags role-based emails.

**Status:** Production-ready prototype  
**Tech Stack:** Python, FastAPI, PostgreSQL, HTML/CSS/JS

---

## 📋 Architecture Overview

### Components

```
┌─────────────────┐
│    Frontend     │ (HTML/CSS/JS)
│  - Form UI      │
│  - Results      │
│  - History      │
└────────┬────────┘
         │ HTTP (REST API)
         ▼
┌─────────────────┐
│  FastAPI        │ (Backend)
│  - /api/verify  │
│  - /api/history │
│  - /api/stats   │
└────────┬────────┘
         │ SQL
         ▼
┌─────────────────┐
│  PostgreSQL     │
│  - email_       │
│    verifications│
│  - verification │
│    _history     │
└─────────────────┘
```

### Data Flow

1. **User enters email** → Frontend form
2. **Send to API** → `/api/verify` endpoint
3. **Validation checks:**
   - Format validation (regex)
   - Domain extraction
   - DNS/MX record lookup (async)
   - Disposable domain check
   - Role-based email check
4. **Determine status** → valid/risky/invalid
5. **Store in database** → For caching + history
6. **Return result** → Display to user
---
## 📝 License

MIT - Free to use and modify


