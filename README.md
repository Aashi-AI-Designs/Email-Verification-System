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

## Quick Start 

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- pip (Python package manager)

### 1. Clone & Setup

```bash
# Clone (or download files)
git clone <repo-url>
cd email-verifier

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup PostgreSQL

**Mac:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

**Windows:** Download from https://www.postgresql.org/download/windows/

### 3. Create Database

Open PostgreSQL and run:

```sql
CREATE USER emailuser WITH PASSWORD 'emailpass';
CREATE DATABASE email_verifier OWNER emailuser;
GRANT ALL PRIVILEGES ON DATABASE email_verifier TO emailuser;
```

Or create `.env` file (copy from `.env.example`):
```
DATABASE_URL=postgresql://emailuser:emailpass@localhost:5432/email_verifier
```

### 4. Initialize Database

```bash
python3 -c "from backend.database import init_db; init_db()"
```

### 5. Run Backend

```bash
python3 -m uvicorn backend.main:app --reload --port 8000
```

You should see:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 6. Run Frontend (new terminal)

```bash
cd frontend
python3 -m http.server 3000
```

### 7. Open Browser

Visit: **http://localhost:3000**

---
##  API Endpoints

### Verify Single Email

**POST** `/api/verify`

Request:
```json
{
  "email": "john@example.com"
}
```

Response:
```json
{
  "email": "john@example.com",
  "domain": "example.com",
  "is_valid_format": true,
  "domain_exists": true,
  "mx_found": true,
  "is_disposable": false,
  "is_role_based": false,
  "status": "valid",
  "reason": "Domain and MX records found, no red flags"
}
```

### Get Verification History

**GET** `/api/history?limit=10`

Response:
```json
{
  "total": 5,
  "records": [
    {
      "email": "john@example.com",
      "domain": "example.com",
      "status": "valid",
      "reason": "Domain and MX records found, no red flags",
      "created_at": "2024-06-11T10:30:45"
    }
  ]
}
```

### Get Statistics

**GET** `/api/stats`

Response:
```json
{
  "total_verified": 42,
  "valid": 38,
  "risky": 3,
  "invalid": 1
}
```
### Health Check

**GET** `/health`

Response:
```json
{
  "status": "ok",
  "service": "email-verifier"
}
```

---

##  License

MIT - Free to use and modify


