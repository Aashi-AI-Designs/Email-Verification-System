# How to Add Bonus Features - Complete Step-by-Step Guide

---

# 1. Batch Verification Endpoint

## What It Does

Instead of verifying one email at a time, verify 1000+ emails in one API call.

### Example Request
```bash
curl -X POST http://localhost:8000/api/verify-batch \
  -H "Content-Type: application/json" \
  -d '{
    "emails": [
      "john@gmail.com",
      "admin@example.com",
      "test@tempmail.com",
      "invalid-email"
    ],
    "full_validation": false
  }'
```

### Example Response
```json
{
  "total": 4,
  "valid": 1,
  "risky": 2,
  "invalid": 1,
  "results": [
    {
      "email": "john@gmail.com",
      "status": "risky",
      "reason": "Disposable email domain"
    },
    {
      "email": "admin@example.com",
      "status": "risky",
      "reason": "Role-based email"
    },
    {
      "email": "test@tempmail.com",
      "status": "risky",
      "reason": "Disposable email domain"
    },
    {
      "email": "invalid-email",
      "status": "invalid",
      "reason": "Invalid email format"
    }
  ],
  "processing_time_ms": 1234.56
}
```

## Step-by-Step Implementation

### Step 1: Add Schema to `backend/schemas.py`

Add these classes at the end of the file:

```python
from typing import Optional

class BatchVerifyRequest(BaseModel):
    """Request schema for batch email verification"""
    emails: list[str] = Field(..., example=["john@gmail.com", "admin@example.com"])
    full_validation: bool = Field(default=False, description="Run full SMTP validation")

class BatchVerifyResult(BaseModel):
    """Individual result from batch verification"""
    email: str
    status: str  # valid, risky, invalid
    reason: str

class BatchVerifyResponse(BaseModel):
    """Response schema for batch verification"""
    total: int
    valid: int
    risky: int
    invalid: int
    results: list[BatchVerifyResult]
    processing_time_ms: float
```

### Step 2: Add Endpoint to `backend/main.py`

Add this new endpoint after your existing endpoints:

```python
import time

@app.post("/api/verify-batch", response_model=BatchVerifyResponse)
async def verify_batch(
    request: BatchVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify multiple emails in one request.
    
    Progressive validation:
    1. Format check (instant)
    2. Domain check (5 seconds)
    3. Full validation optional (30 seconds if enabled)
    """
    start_time = time.time()
    
    # Normalize emails
    emails = [e.strip().lower() for e in request.emails if e.strip()]
    
    if not emails:
        raise HTTPException(status_code=400, detail="No emails provided")
    
    if len(emails) > 10000:
        raise HTTPException(status_code=400, detail="Maximum 10000 emails per request")
    
    results = []
    
    # Step 1: Format validation (fast)
    formatted_emails = []
    for email in emails:
        is_valid_format, reason = validate_email_format(email)
        if is_valid_format:
            formatted_emails.append(email)
        else:
            results.append(BatchVerifyResult(
                email=email,
                status='invalid',
                reason=reason
            ))
    
    # Step 2: Domain validation (medium speed)
    domain_valid_emails = []
    for email in formatted_emails:
        try:
            domain = extract_domain(email)
            domain_exists, mx_found, reason = await check_mx_records(domain)
            
            if domain_exists and mx_found:
                domain_valid_emails.append(email)
            else:
                results.append(BatchVerifyResult(
                    email=email,
                    status='invalid',
                    reason=f"Domain check failed: {reason}"
                ))
        except Exception as e:
            results.append(BatchVerifyResult(
                email=email,
                status='invalid',
                reason=f"Error: {str(e)}"
            ))
    
    # Step 3: Full validation (optional, slow)
    if request.full_validation:
        for email in domain_valid_emails:
            try:
                result = await verify_email(email)
                results.append(BatchVerifyResult(
                    email=result['email'],
                    status=result['status'],
                    reason=result['reason']
                ))
            except Exception as e:
                results.append(BatchVerifyResult(
                    email=email,
                    status='invalid',
                    reason=f"Verification error: {str(e)}"
                ))
    else:
        # Just mark as valid if domain passed
        for email in domain_valid_emails:
            results.append(BatchVerifyResult(
                email=email,
                status='valid',
                reason='Passed format and domain checks'
            ))
    
    # Calculate statistics
    valid = sum(1 for r in results if r.status == 'valid')
    risky = sum(1 for r in results if r.status == 'risky')
    invalid = sum(1 for r in results if r.status == 'invalid')
    
    elapsed_ms = (time.time() - start_time) * 1000
    
    return BatchVerifyResponse(
        total=len(emails),
        valid=valid,
        risky=risky,
        invalid=invalid,
        results=results,
        processing_time_ms=round(elapsed_ms, 2)
    )
```

### Step 3: Test It

```bash
# Start backend (if not already running)
python3 -m uvicorn backend.main:app --reload --port 8000

# In another terminal, test it
curl -X POST http://localhost:8000/api/verify-batch \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["john@gmail.com", "admin@example.com", "invalid"],
    "full_validation": false
  }'
```

### Step 4: Add to Frontend (Optional)

If you want a UI for batch verification, add this HTML section to `frontend/index.html`:

```html
<!-- Add this after the single verification form -->

<div style="margin-top: 40px; padding-top: 40px; border-top: 2px solid #e0e0e0;">
  <h2 style="color: #333; margin-bottom: 20px;">📦 Batch Verification</h2>
  
  <form id="batchVerifyForm">
    <div class="form-group">
      <label for="batchEmails">Email List (one per line)</label>
      <textarea 
        id="batchEmails" 
        placeholder="john@example.com&#10;admin@example.com&#10;test@tempmail.com" 
        style="width: 100%; height: 150px; padding: 12px; border: 2px solid #e0e0e0; border-radius: 6px; font-family: monospace; font-size: 14px;"
        required
      ></textarea>
    </div>
    
    <label style="display: flex; align-items: center; margin-bottom: 20px;">
      <input type="checkbox" id="fullValidation" style="margin-right: 8px;">
      <span>Full validation (slower but more accurate)</span>
    </label>
    
    <button type="submit">Verify Batch</button>
  </form>
  
  <div id="batchResults" style="margin-top: 20px;"></div>
</div>

<script>
document.getElementById('batchVerifyForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const emails = document.getElementById('batchEmails').value
    .split('\n')
    .map(e => e.trim())
    .filter(e => e);
  
  const fullValidation = document.getElementById('fullValidation').checked;
  
  try {
    const response = await fetch(`${API_URL}/api/verify-batch`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({emails, full_validation: fullValidation})
    });
    
    const data = await response.json();
    
    let html = `
      <h3>Results: ${data.valid} Valid, ${data.risky} Risky, ${data.invalid} Invalid</h3>
      <p style="color: #666;">Processed ${data.total} emails in ${data.processing_time_ms}ms</p>
    `;
    
    data.results.forEach(r => {
      const statusEmoji = {'valid': '✅', 'risky': '⚠️', 'invalid': '❌'}[r.status];
      html += `
        <div style="padding: 10px; margin: 5px 0; background: #f5f5f5; border-radius: 4px;">
          ${statusEmoji} <strong>${r.email}</strong> - ${r.reason}
        </div>
      `;
    });
    
    document.getElementById('batchResults').innerHTML = html;
  } catch (err) {
    document.getElementById('batchResults').innerHTML = `<div style="color: red;">Error: ${err.message}</div>`;
  }
});
</script>
```

---

# 2. Confidence Scoring Model

## What It Does

Instead of just saying "valid" or "invalid", return a confidence score (0.0 to 1.0).

- 0.95 = Very confident it's a real email
- 0.70 = Probably valid but some red flags
- 0.40 = Risky, might bounce
- 0.10 = Likely invalid

### Example Response
```json
{
  "email": "john@gmail.com",
  "status": "valid",
  "confidence": 0.75,
  "confidence_reasons": "disposable_domain",
  "recommendation": "probably_valid"
}
```

## Step-by-Step Implementation

### Step 1: Add Function to `backend/validators.py`

Add this function after the `determine_status()` function:

```python
def calculate_confidence(checks: dict) -> tuple[float, str]:
    """
    Calculate confidence score (0.0 to 1.0) based on all checks.
    
    Higher score = more likely to be valid email.
    
    Returns: (confidence_score, reason_codes)
    """
    score = 100
    reasons = []
    
    # Invalid format = 0% confidence (certain it's bad)
    if not checks['is_valid_format']:
        return 0.0, "invalid_format"
    
    # Domain problems = major reduction
    if not checks['domain_exists']:
        score -= 50
        reasons.append("domain_not_found")
    
    if not checks['mx_found']:
        score -= 40
        reasons.append("no_mx_records")
    
    # Red flags = moderate reduction
    if checks['is_disposable']:
        score -= 20
        reasons.append("disposable_domain")
    
    if checks['is_role_based']:
        score -= 10
        reasons.append("role_based_email")
    
    # Clamp between 0-100
    score = max(0, min(100, score))
    confidence = score / 100.0
    
    return confidence, ",".join(reasons) if reasons else "no_issues"


def get_recommendation(confidence: float) -> str:
    """
    Get human-readable recommendation based on confidence.
    """
    if confidence >= 0.9:
        return "safe"
    elif confidence >= 0.7:
        return "probably_valid"
    elif confidence >= 0.4:
        return "risky"
    else:
        return "invalid"
```

### Step 2: Update `backend/schemas.py`

Update the `VerificationResponse` class:

```python
class VerificationResponse(BaseModel):
    email: str
    domain: str
    is_valid_format: bool
    domain_exists: bool
    mx_found: bool
    is_disposable: bool
    is_role_based: bool
    status: str
    reason: str
    
    # ADD THESE NEW FIELDS
    confidence: Optional[float] = None
    confidence_reasons: Optional[str] = None
    recommendation: Optional[str] = None
```

### Step 3: Update `backend/main.py`

Modify the `verify_email_endpoint` function to include confidence:

```python
@app.post("/api/verify", response_model=VerificationResponse)
async def verify_email_endpoint(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """Verify email with confidence scoring"""
    email = request.email.strip().lower()
    
    # Check cache
    existing = db.query(EmailVerification).filter(
        EmailVerification.email == email
    ).first()
    
    if existing:
        result = existing.to_dict()
        # Add confidence to cached result
        from backend.validators import calculate_confidence, get_recommendation
        confidence, reasons = calculate_confidence(result)
        result['confidence'] = confidence
        result['confidence_reasons'] = reasons
        result['recommendation'] = get_recommendation(confidence)
        return result
    
    try:
        # Run verification
        result = await verify_email(email)
        
        # Calculate confidence
        from backend.validators import calculate_confidence, get_recommendation
        confidence, reasons = calculate_confidence(result)
        result['confidence'] = confidence
        result['confidence_reasons'] = reasons
        result['recommendation'] = get_recommendation(confidence)
        
        # Save to database
        verification = EmailVerification(
            email=result["email"],
            domain=result["domain"],
            is_valid_format=result["is_valid_format"],
            domain_exists=result["domain_exists"],
            mx_found=result["mx_found"],
            is_disposable=result["is_disposable"],
            is_role_based=result["is_role_based"],
            status=result["status"],
            reason=result["reason"],
        )
        
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        result_dict = verification.to_dict()
        result_dict['confidence'] = confidence
        result_dict['confidence_reasons'] = reasons
        result_dict['recommendation'] = get_recommendation(confidence)
        
        return result_dict
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
```

### Step 4: Update Frontend to Show Confidence

Update `frontend/index.html` in the `displayResult` function:

```javascript
function displayResult(data) {
    const result = document.getElementById('result');
    const statusClass = data.status.toLowerCase();
    const statusEmoji = {
        'valid': '✅',
        'risky': '⚠️',
        'invalid': '❌'
    }[data.status] || '❓';

    let html = `
        <div class="result-title">${statusEmoji} ${data.status.toUpperCase()}</div>
    `;
    
    // ADD CONFIDENCE BAR
    if (data.confidence !== undefined) {
        const confPercent = (data.confidence * 100).toFixed(0);
        const barColor = 
            data.confidence >= 0.9 ? '#4caf50' :
            data.confidence >= 0.7 ? '#ff9800' :
            data.confidence >= 0.4 ? '#ff9800' :
            '#f44336';
        
        html += `
            <div style="margin: 15px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-weight: 600;">Confidence Score</span>
                    <span style="font-weight: 600;">${confPercent}%</span>
                </div>
                <div style="
                    width: 100%;
                    height: 10px;
                    background: #e0e0e0;
                    border-radius: 5px;
                    overflow: hidden;
                ">
                    <div style="
                        width: ${confPercent}%;
                        height: 100%;
                        background: ${barColor};
                        transition: width 0.3s;
                    "></div>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #666;">
                    Recommendation: <strong>${data.recommendation || 'unknown'}</strong>
                </div>
            </div>
        `;
    }
    
    // REST OF EXISTING CODE
    html += `
        <div class="result-details">
            <div class="result-item">
                <span class="result-icon">${data.is_valid_format ? '✓' : '✗'}</span>
                <span>Valid Format: ${data.is_valid_format ? 'Yes' : 'No'}</span>
            </div>
            <!-- ... rest of results ... -->
        </div>
        <div class="result-reason">📝 ${data.reason}</div>
    `;
    
    result.className = `result ${statusClass}`;
    result.innerHTML = html;
    result.style.display = 'block';
}
```

### Step 5: Test It

```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "john@gmail.com"}'

# Should return confidence: 0.75 (because Gmail is disposable)
```

---

# 3. Docker Setup

## What It Does

Run your entire app (backend + database + frontend) in Docker containers with one command.

```bash
docker-compose up
```

## Step-by-Step Implementation

### Step 1: Create `Dockerfile`

Create a new file named `Dockerfile` in the root of your project:

```dockerfile
# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Run app
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Create `docker-compose.yml`

Create a new file named `docker-compose.yml` in the root of your project:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: email_verifier_db
    environment:
      POSTGRES_USER: emailuser
      POSTGRES_PASSWORD: emailpass
      POSTGRES_DB: email_verifier
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U emailuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    build: .
    container_name: email_verifier_backend
    environment:
      DATABASE_URL: postgresql://emailuser:emailpass@postgres:5432/email_verifier
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    command: sh -c "python -c 'from backend.database import init_db; init_db()' && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

  # Frontend
  frontend:
    image: nginx:alpine
    container_name: email_verifier_frontend
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Step 3: Create `nginx.conf`

Create a new file named `nginx.conf` in the root of your project:

```nginx
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Step 4: Update `.env.example`

Add Docker configuration:

```
# Docker
DATABASE_URL=postgresql://emailuser:emailpass@postgres:5432/email_verifier

# Or for local development
# DATABASE_URL=postgresql://emailuser:emailpass@localhost:5432/email_verifier
```

### Step 5: Test It

```bash
# Build and run
docker-compose up

# You'll see output like:
# postgres_1  | database system is ready to accept connections
# backend_1   | Application startup complete
# frontend_1  | 2024/06/11 ...

# Visit http://localhost:3000 in browser
```

To stop:
```bash
docker-compose down
```

### Step 6: Add to `.gitignore`

Add Docker files:

```
# Docker
__pycache__/
*.pyc
.docker/
```

---

# 4. Unit Tests

## What It Does

Automated tests that verify your validation logic works correctly.

### Example Test
```python
def test_validate_email_format():
    assert validate_email_format("john@example.com") == (True, "Valid format")
    assert validate_email_format("invalid-email") == (False, "Invalid email format")
```

## Step-by-Step Implementation

### Step 1: Create `tests` Folder

```bash
mkdir tests
touch tests/__init__.py
```

### Step 2: Create `tests/test_validators.py`

```python
"""
Unit tests for email validation functions.

Run with: pytest tests/test_validators.py -v
"""

import pytest
from backend.validators import (
    validate_email_format,
    extract_domain,
    is_disposable_domain,
    is_role_based_email,
    determine_status,
)


class TestEmailFormatValidation:
    """Test email format validation"""
    
    def test_valid_emails(self):
        """Test valid email formats"""
        valid_emails = [
            "john@example.com",
            "john.smith@example.co.uk",
            "john+tag@example.com",
            "john_smith@example.com",
        ]
        for email in valid_emails:
            is_valid, reason = validate_email_format(email)
            assert is_valid == True, f"Email {email} should be valid"
    
    def test_invalid_emails(self):
        """Test invalid email formats"""
        invalid_emails = [
            "invalid-email",
            "john@",
            "@example.com",
            "john @example.com",
            "john@example",
            "",
        ]
        for email in invalid_emails:
            is_valid, reason = validate_email_format(email)
            assert is_valid == False, f"Email {email} should be invalid"
    
    def test_email_too_long(self):
        """Test email length limit"""
        long_email = "a" * 100 + "@example.com"
        is_valid, reason = validate_email_format(long_email)
        assert is_valid == False
        assert "too long" in reason.lower()
    
    def test_local_part_too_long(self):
        """Test local part (before @) length limit"""
        email = "a" * 100 + "@example.com"
        is_valid, reason = validate_email_format(email)
        assert is_valid == False
        assert "local part" in reason.lower()


class TestDomainExtraction:
    """Test domain extraction"""
    
    def test_extract_domain(self):
        """Test domain extraction from email"""
        test_cases = [
            ("john@example.com", "example.com"),
            ("john@sub.example.com", "sub.example.com"),
            ("john.smith@example.co.uk", "example.co.uk"),
        ]
        for email, expected_domain in test_cases:
            domain = extract_domain(email)
            assert domain == expected_domain
    
    def test_domain_normalization(self):
        """Test domain is normalized to lowercase"""
        domain = extract_domain("john@EXAMPLE.COM")
        assert domain == "example.com"


class TestDisposableDomainDetection:
    """Test disposable domain detection"""
    
    def test_known_disposable_domains(self):
        """Test detection of known disposable domains"""
        disposable_domains = [
            "gmail.com",
            "yahoo.com",
            "tempmail.com",
            "mailinator.com",
        ]
        for domain in disposable_domains:
            is_disposable, reason = is_disposable_domain(domain)
            assert is_disposable == True, f"Domain {domain} should be flagged as disposable"
    
    def test_legitimate_domains(self):
        """Test legitimate domains are not flagged"""
        legitimate_domains = [
            "example.com",
            "company.com",
            "university.edu",
        ]
        for domain in legitimate_domains:
            is_disposable, reason = is_disposable_domain(domain)
            assert is_disposable == False, f"Domain {domain} should not be flagged as disposable"


class TestRoleBasedDetection:
    """Test role-based email detection"""
    
    def test_role_based_emails(self):
        """Test detection of role-based emails"""
        role_based_emails = [
            "admin@example.com",
            "support@example.com",
            "info@example.com",
            "hello@example.com",
            "contact@example.com",
        ]
        for email in role_based_emails:
            is_role_based, reason = is_role_based_email(email)
            assert is_role_based == True, f"Email {email} should be flagged as role-based"
    
    def test_personal_emails(self):
        """Test personal emails are not flagged"""
        personal_emails = [
            "john@example.com",
            "jane.smith@example.com",
            "bob123@example.com",
        ]
        for email in personal_emails:
            is_role_based, reason = is_role_based_email(email)
            assert is_role_based == False, f"Email {email} should not be flagged as role-based"
    
    def test_role_based_with_underscore(self):
        """Test role-based with underscore pattern"""
        is_role_based, reason = is_role_based_email("admin_user@example.com")
        assert is_role_based == True
    
    def test_role_based_with_dash(self):
        """Test role-based with dash pattern"""
        is_role_based, reason = is_role_based_email("support-team@example.com")
        assert is_role_based == True


class TestStatusDetermination:
    """Test final status determination"""
    
    def test_valid_email_status(self):
        """Test valid email status determination"""
        checks = {
            'is_valid_format': True,
            'domain_exists': True,
            'mx_found': True,
            'is_disposable': False,
            'is_role_based': False,
        }
        status, reason = determine_status(**checks)
        assert status == 'valid'
    
    def test_invalid_format_status(self):
        """Test invalid format results in invalid status"""
        checks = {
            'is_valid_format': False,
            'domain_exists': True,
            'mx_found': True,
            'is_disposable': False,
            'is_role_based': False,
        }
        status, reason = determine_status(**checks)
        assert status == 'invalid'
    
    def test_no_domain_status(self):
        """Test no domain results in invalid status"""
        checks = {
            'is_valid_format': True,
            'domain_exists': False,
            'mx_found': False,
            'is_disposable': False,
            'is_role_based': False,
        }
        status, reason = determine_status(**checks)
        assert status == 'invalid'
    
    def test_no_mx_status(self):
        """Test no MX records results in invalid status"""
        checks = {
            'is_valid_format': True,
            'domain_exists': True,
            'mx_found': False,
            'is_disposable': False,
            'is_role_based': False,
        }
        status, reason = determine_status(**checks)
        assert status == 'invalid'
    
    def test_disposable_status(self):
        """Test disposable domain results in risky status"""
        checks = {
            'is_valid_format': True,
            'domain_exists': True,
            'mx_found': True,
            'is_disposable': True,
            'is_role_based': False,
        }
        status, reason = determine_status(**checks)
        assert status == 'risky'
    
    def test_role_based_status(self):
        """Test role-based email results in risky status"""
        checks = {
            'is_valid_format': True,
            'domain_exists': True,
            'mx_found': True,
            'is_disposable': False,
            'is_role_based': True,
        }
        status, reason = determine_status(**checks)
        assert status == 'risky'
    
    def test_multiple_red_flags_status(self):
        """Test multiple red flags results in risky status"""
        checks = {
            'is_valid_format': True,
            'domain_exists': True,
            'mx_found': True,
            'is_disposable': True,
            'is_role_based': True,
        }
        status, reason = determine_status(**checks)
        assert status == 'risky'
        assert 'disposable_domain' in reason.lower() or 'risky' in reason.lower()
```

### Step 3: Create `tests/test_api.py`

```python
"""
Integration tests for API endpoints.

Run with: pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "email-verifier"


class TestVerifyEndpoint:
    """Test email verification endpoint"""
    
    def test_verify_valid_format(self):
        """Test verifying valid email format"""
        response = client.post(
            "/api/verify",
            json={"email": "john@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "john@example.com"
        assert data["is_valid_format"] == True
    
    def test_verify_invalid_format(self):
        """Test verifying invalid email format"""
        response = client.post(
            "/api/verify",
            json={"email": "invalid-email"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid_format"] == False
        assert data["status"] == "invalid"
    
    def test_verify_missing_email(self):
        """Test error when email is missing"""
        response = client.post(
            "/api/verify",
            json={}
        )
        assert response.status_code == 422  # Validation error
    
    def test_verify_response_format(self):
        """Test response has required fields"""
        response = client.post(
            "/api/verify",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "email", "domain", "is_valid_format", "domain_exists",
            "mx_found", "is_disposable", "is_role_based", "status", "reason"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestHistoryEndpoint:
    """Test history endpoint"""
    
    def test_get_history(self):
        """Test /api/history endpoint"""
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "records" in data
        assert isinstance(data["records"], list)
    
    def test_history_limit(self):
        """Test history limit parameter"""
        response = client.get("/api/history?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) <= 5


class TestStatsEndpoint:
    """Test statistics endpoint"""
    
    def test_get_stats(self):
        """Test /api/stats endpoint"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["total_verified", "valid", "risky", "invalid"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            assert isinstance(data[field], int)
```

### Step 4: Update `requirements.txt`

Add pytest:

```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
dnspython==2.4.2
aiosmtplib==3.0.1
python-dotenv==1.0.0
asyncpg==0.29.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2  # NEW: For testing async endpoints
```

Install:
```bash
pip install -r requirements.txt
```

### Step 5: Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_validators.py -v

# Run specific test class
pytest tests/test_validators.py::TestEmailFormatValidation -v

# Run specific test
pytest tests/test_validators.py::TestEmailFormatValidation::test_valid_emails -v

# Run with coverage
pytest --cov=backend tests/
```

### Step 6: Example Output

```
tests/test_validators.py::TestEmailFormatValidation::test_valid_emails PASSED
tests/test_validators.py::TestEmailFormatValidation::test_invalid_emails PASSED
tests/test_validators.py::TestEmailFormatValidation::test_email_too_long PASSED
tests/test_validators.py::TestDomainExtraction::test_extract_domain PASSED
tests/test_api.py::TestHealthEndpoint::test_health_check PASSED
...

======================== 25 passed in 0.45s ========================
```
