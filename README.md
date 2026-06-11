# Email Verification System

A full-stack email verification tool built with **FastAPI**, **PostgreSQL**, and **HTML/JS**. Validates email format, checks DNS/MX records, detects disposable domains, and flags role-based emails.

**Status:** ✅ Production-ready prototype  
**Time to Build:** 4 days  
**Tech Stack:** Python, FastAPI, PostgreSQL, HTML/CSS/JS

---

## 🚀 Quick Start (5 minutes)

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

## 🔌 API Endpoints

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

## 🧠 Interview Concepts Explained

### 1. API Design
- **REST principles:** Resources (emails) + HTTP methods (POST)
- **Request/Response validation:** Pydantic schemas prevent bad data
- **Status codes:** 200 OK, 400 Bad Request, 500 Server Error
- **Error handling:** Clear error messages for debugging

### 2. Database Design
- **Schema:** Two tables - current verification + history audit trail
- **Indexing:** Queries on `email`, `domain`, `created_at` are fast
- **ACID properties:** Data integrity guaranteed by PostgreSQL
- **Trade-off:** Extra storage for history, but valuable for analytics

### 3. Validation Logic
- **Format validation:** Regex catches 95% of invalid emails
- **DNS/MX lookup:** Proves domain actually accepts mail
- **Async I/O:** DNS lookups are slow (network I/O), so we use async
- **Caching:** Store results to avoid re-checking same email

### 4. Async/Await
DNS lookups are network I/O (slow). If we made them blocking (synchronous), only 1 request could process at a time.

With async, we can handle multiple requests concurrently:
```python
async def check_mx_records(domain):
    # This doesn't block the event loop
    # Other requests can be processed while we wait for DNS
    mx_records = await dns.resolver.resolve(domain, 'MX')
```

### 5. Function Composition
Breaking complex logic into small functions:
```
verify_email()
  ├─ validate_email_format()
  ├─ extract_domain()
  ├─ check_mx_records()
  ├─ is_disposable_domain()
  ├─ is_role_based_email()
  └─ determine_status()
```

**Why?** Easy to test, debug, and explain each step.

---

## 🧪 Testing

### Test Format Validation

```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid-email"}'
```

### Test Valid Email

```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "user@gmail.com"}'
```

### Test Disposable Domain

```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "test@tempmail.com"}'
```

### Test Role-Based Email

```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com"}'
```

---

## 📁 Project Structure

```
email-verifier/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── models.py         # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── validators.py     # Email validation logic
│   └── database.py       # Database connection & init
├── frontend/
│   └── index.html        # Complete HTML/CSS/JS UI
├── database/
│   └── schema.sql        # SQL table definitions
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Actual env (create from .example)
└── README.md             # This file
```

---

## 🎓 Key Learnings for Interviews

### Question: "How would you verify email addresses at scale?"

**Answer framework:**
1. **Format validation** - Quick regex check
2. **DNS/MX lookup** - Async to handle concurrency
3. **Caching** - Store results to avoid repeated checks
4. **Database** - Audit trail for compliance
5. **Monitoring** - Track success rates, latency
6. **Batch processing** - For bulk verification jobs

### Question: "What are the tradeoffs of disposable domain detection?"

**Answer:**
- **Pro:** Catch spam/temporary emails, improve campaign quality
- **Con:** Maintain list (Gmail users legitimate too), false positives
- **Solution:** Use API (like Rapid API) or ML model for classification

### Question: "Why use async for DNS lookups?"

**Answer:**
- DNS is network I/O (slow ~100-500ms per lookup)
- Synchronous code blocks the entire thread
- With async, 100 concurrent requests can be processed while waiting for DNS
- Leads to 10x-100x better throughput

---

## 🚀 Deployment

### Docker (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0"]
```

Build & run:
```bash
docker build -t email-verifier .
docker run -p 8000:8000 email-verifier
```

### Production Checklist

- [ ] Use environment variables for secrets
- [ ] Add HTTPS (SSL certificate)
- [ ] Rate limiting on API endpoints
- [ ] Database backups
- [ ] Monitoring & alerting
- [ ] Load testing
- [ ] API documentation (Swagger)

---

## 🛠️ Troubleshooting

### "Connection refused" on database

**Solution:**
```bash
# Check PostgreSQL is running
psql -U emailuser -d email_verifier

# Or restart service
brew services restart postgresql  # Mac
sudo service postgresql restart    # Linux
```

### "Module not found" errors

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend not connecting to backend

**Solution:**
- Check backend is running: `http://localhost:8000/health`
- CORS is enabled in backend
- Check browser console for errors

---

## 📊 Next Steps (Bonus Features)

1. **Batch verification** → `/api/verify-batch` for CSV uploads
2. **Confidence scoring** → ML model to predict deliverability
3. **Email enrichment** → Find name, company, phone number
4. **Webhooks** → Async notifications for long-running verifications
5. **Authentication** → JWT tokens for API access
6. **Rate limiting** → Prevent abuse

---

## 📝 License

MIT - Free to use and modify

---

## 💡 Questions? 

Refer to inline code comments for detailed explanations of each concept.
