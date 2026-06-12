# How to Add Bonus Features (Step-by-Step)

## Feature #1: Email Typo Suggestion (Like Mailcheck)

### Step 1: Update validators.py

Add this function to `backend/validators.py`:

```python
from difflib import SequenceMatcher

# Add to DISPOSABLE_DOMAINS section
COMMON_DOMAINS = {
    # Gmail typos
    'gmial.com': 'gmail.com',
    'gmai.com': 'gmail.com',
    'gmial.com': 'gmail.com',
    'gmil.com': 'gmail.com',
    'gmal.com': 'gmail.com',
    
    # Yahoo typos
    'yahooo.com': 'yahoo.com',
    'yaho.com': 'yahoo.com',
    'yahou.com': 'yahoo.com',
    
    # Hotmail typos
    'hotmial.com': 'hotmail.com',
    'hotmal.com': 'hotmail.com',
    'hotmil.com': 'hotmail.com',
    
    # Outlook typos
    'outlok.com': 'outlook.com',
    'outloo.com': 'outlook.com',
    
    # Common typos
    'aol.con': 'aol.com',
    'protonmail.co': 'protonmail.com',
}

def suggest_correction(email: str) -> dict:
    """
    Suggest corrections for common email typos.
    
    Returns confidence score 0-1.
    At 0.9+, you can suggest to user.
    """
    email = email.strip().lower()
    local_part, domain = email.split('@')
    
    # Check exact typos first
    if domain in COMMON_DOMAINS:
        return {
            'email': email,
            'suggestion': f"{local_part}@{COMMON_DOMAINS[domain]}",
            'type': 'common_typo',
            'confidence': 0.99,
            'message': f"Did you mean {local_part}@{COMMON_DOMAINS[domain]}?"
        }
    
    # Check similar domains (Levenshtein distance)
    for common_domain in COMMON_DOMAINS.keys():
        similarity = SequenceMatcher(None, domain, common_domain).ratio()
        if similarity > 0.85:  # 85% similar
            return {
                'email': email,
                'suggestion': f"{local_part}@{COMMON_DOMAINS[common_domain]}",
                'type': 'similar_domain',
                'confidence': similarity,
                'message': f"Did you mean {local_part}@{COMMON_DOMAINS[common_domain]}?"
            }
    
    return None


async def verify_email_with_suggestions(email: str) -> dict:
    """
    Enhanced verify_email that includes typo suggestions.
    
    Returns both verification results AND suggestions.
    """
    email = email.strip().lower()
    
    # First check if it's a typo
    suggestion = suggest_correction(email)
    
    # Run regular verification
    result = await verify_email(email)
    
    # If original is invalid but we have a suggestion, suggest it
    if result['status'] == 'invalid' and suggestion:
        result['suggestion'] = suggestion
        result['reason'] = f"Looks like a typo. {suggestion['message']}"
    
    return result
```

### Step 2: Update API Endpoint

Update `backend/main.py`:

```python
@app.post("/api/verify", response_model=VerificationResponse)
async def verify_email_endpoint(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email with typo suggestions.
    """
    email = request.email.strip().lower()
    
    # Check for cached result first
    existing = db.query(EmailVerification).filter(
        EmailVerification.email == email
    ).first()
    
    if existing:
        # Add suggestion to cached result
        result = existing.to_dict()
        suggestion = suggest_correction(email)
        if suggestion:
            result['suggestion'] = suggestion
        return result
    
    try:
        # Run verification WITH suggestions
        from backend.validators import suggest_correction
        result = await verify_email(email)
        
        # Add suggestion if typo found
        suggestion = suggest_correction(email)
        if suggestion:
            result['suggestion'] = suggestion
        
        # Save to database
        verification = EmailVerification(...)
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        return result
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
```

### Step 3: Update Frontend

Update `frontend/index.html` to show suggestions:

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
        <div class="result-details">
            <!-- ... existing result items ... -->
        </div>
        <div class="result-reason"> ${data.reason}</div>
    `;
    
    // ADD THIS: Show suggestion if available
    if (data.suggestion) {
        html += `
            <div class="result-suggestion" style="
                margin-top: 15px;
                padding: 12px;
                background: rgba(102, 126, 234, 0.1);
                border-radius: 6px;
                border-left: 3px solid #667eea;
            ">
                <strong> Did you mean?</strong><br>
                <code style="background: rgba(0,0,0,0.05); padding: 4px 8px; border-radius: 4px;">
                    ${data.suggestion.suggestion}
                </code>
                <button onclick="verifyEmail('${data.suggestion.suggestion}')" 
                    style="
                    margin-left: 10px;
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                ">
                    Try This
                </button>
            </div>
        `;
    }
    
    result.className = `result ${statusClass}`;
    result.innerHTML = html;
    result.style.display = 'block';
}
```

### Step 4: Test It

```bash
# Test with typo
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "john@gmial.com"}'

# Should return suggestion: john@gmail.com
```

---

## Feature #2: Confidence Scoring (Like Hunter.io)

### Step 1: Add Confidence Calculation

Add to `backend/validators.py`:

```python
def calculate_confidence(checks: dict) -> tuple[float, str]:
    """
    Calculate confidence score (0.0 to 1.0) based on checks.
    
    Higher score = more likely to be valid email.
    """
    score = 100
    reasons = []
    
    # Invalid format = 0% confidence
    if not checks['is_valid_format']:
        return 0.0, "Invalid email format"
    
    # Domain problems = reduce significantly
    if not checks['domain_exists']:
        score -= 60
        reasons.append("domain_not_found")
    
    if not checks['mx_found']:
        score -= 40
        reasons.append("no_mx_records")
    
    # Red flags = reduce moderately
    if checks['is_disposable']:
        score -= 25
        reasons.append("disposable_domain")
    
    if checks['is_role_based']:
        score -= 15
        reasons.append("role_based_email")
    
    # Clamp between 0-100
    score = max(0, min(100, score))
    confidence = score / 100.0
    
    return confidence, ",".join(reasons) if reasons else "no_issues"


async def verify_email_with_confidence(email: str) -> dict:
    """
    Verify email and return confidence score.
    
    Confidence interpretation:
    - 0.9-1.0: Safe to use
    - 0.7-0.9: Probably valid
    - 0.4-0.7: Risky (might bounce)
    - 0.0-0.4: Invalid
    """
    email = email.strip().lower()
    
    # Run verification
    result = await verify_email(email)
    
    # Calculate confidence
    confidence, reason_code = calculate_confidence(result)
    
    return {
        **result,
        'confidence': confidence,
        'confidence_reasons': reason_code,
        'recommendation': (
            'safe' if confidence >= 0.9
            else 'probably_valid' if confidence >= 0.7
            else 'risky' if confidence >= 0.4
            else 'invalid'
        )
    }
```

### Step 2: Update API Response

Update `backend/schemas.py`:

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
    
    # NEW FIELDS
    confidence: Optional[float] = None  # 0.0 to 1.0
    recommendation: Optional[str] = None  # safe/probably_valid/risky/invalid
```

### Step 3: Update Frontend Display

```javascript
function displayResult(data) {
    // ... existing code ...
    
    // ADD confidence bar
    if (data.confidence !== undefined) {
        const confidencePercent = (data.confidence * 100).toFixed(0);
        const barColor = 
            data.confidence >= 0.9 ? '#4caf50' :
            data.confidence >= 0.7 ? '#ff9800' :
            data.confidence >= 0.4 ? '#ff9800' :
            '#f44336';
        
        html += `
            <div style="margin-top: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>Confidence Score</span>
                    <span>${confidencePercent}%</span>
                </div>
                <div style="
                    width: 100%;
                    height: 8px;
                    background: #e0e0e0;
                    border-radius: 4px;
                    overflow: hidden;
                ">
                    <div style="
                        width: ${confidencePercent}%;
                        height: 100%;
                        background: ${barColor};
                        transition: width 0.3s;
                    "></div>
                </div>
                <div style="font-size: 12px; color: #666; margin-top: 8px;">
                    Recommendation: <strong>${data.recommendation}</strong>
                </div>
            </div>
        `;
    }
}
```

### Step 4: Test It

```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@gmail.com"}'

# Should return confidence: 0.75, recommendation: "probably_valid"
```

---

## Feature #3: Batch Verification (Like Brevo)

### Step 1: Add Batch Schema

Update `backend/schemas.py`:

```python
class BatchVerifyRequest(BaseModel):
    emails: list[str]
    full_validation: bool = False  # Skip expensive SMTP check

class BatchVerifyResult(BaseModel):
    email: str
    status: str
    reason: str
    confidence: Optional[float] = None

class BatchVerifyResponse(BaseModel):
    total: int
    valid: int
    risky: int
    invalid: int
    results: list[BatchVerifyResult]
    processing_time_ms: float
```

### Step 2: Add Batch Endpoint

Add to `backend/main.py`:

```python
@app.post("/api/verify-batch", response_model=BatchVerifyResponse)
async def verify_batch(
    request: BatchVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify multiple emails efficiently.
    
    Progressive approach:
    1. Format check (instant)
    2. Domain check (5s)
    3. SMTP validation (optional, 30s)
    """
    import time
    start_time = time.time()
    
    emails = [e.strip().lower() for e in request.emails]
    results = []
    
    # STEP 1: Format validation (fast)
    formatted = []
    for email in emails:
        is_valid, reason = validate_email_format(email)
        if is_valid:
            formatted.append(email)
        else:
            results.append(BatchVerifyResult(
                email=email,
                status='invalid',
                reason=reason
            ))
    
    # STEP 2: Domain validation (medium)
    domain_valid = []
    for email in formatted:
        domain = extract_domain(email)
        domain_exists, mx_found, reason = await check_mx_records(domain)
        
        if domain_exists and mx_found:
            domain_valid.append(email)
        else:
            results.append(BatchVerifyResult(
                email=email,
                status='invalid',
                reason=f"Domain check failed: {reason}"
            ))
    
    # STEP 3: Full validation (optional, slow)
    if request.full_validation:
        for email in domain_valid:
            result = await verify_email(email)
            results.append(BatchVerifyResult(**result))
    else:
        # Just mark as valid if domain passed
        for email in domain_valid:
            results.append(BatchVerifyResult(
                email=email,
                status='valid',
                reason='Passed format and domain checks'
            ))
    
    # Statistics
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
        processing_time_ms=elapsed_ms
    )
```

### Step 3: Test It

```bash
curl -X POST http://localhost:8000/api/verify-batch \
  -H "Content-Type: application/json" \
  -d '{
    "emails": [
      "john@gmail.com",
      "invalid-email",
      "admin@example.com",
      "test@tempmail.com"
    ],
    "full_validation": false
  }'

# Should process all 4 in ~2 seconds
```

---
