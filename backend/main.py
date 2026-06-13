from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db, init_db
from backend.models import EmailVerification, VerificationHistory
from backend.schemas import VerifyEmailRequest, VerificationResponse, HistoryListResponse
from backend.validators import verify_email

import os
from dotenv import load_dotenv

load_dotenv()

# Initialize database on startup
init_db()

app = FastAPI(
    title="Email Verification API",
    description="Verify email addresses with DNS/MX checks and disposable domain detection",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "email-verifier"}


@app.post("/api/verify", response_model=VerificationResponse)
async def verify_email_endpoint(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a single email address.
    
    Returns verification results including format, domain existence, MX records,
    and whether it's a disposable or role-based email.
    """
    email = request.email.strip().lower()
    
    # Check if we already verified this email recently
    existing = db.query(EmailVerification).filter(
        EmailVerification.email == email
    ).first()
    
    if existing:
        # Return cached result
        return existing.to_dict()
    
    try:
        # Run verification
        result = await verify_email(email)
        
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
        
        # Also save to history
        history = VerificationHistory(
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
        
        db.add(history)
        db.commit()
        
        return verification.to_dict()
    
    except IntegrityError:
        # Email was already verified (race condition)
        db.rollback()
        existing = db.query(EmailVerification).filter(
            EmailVerification.email == email
        ).first()
        if existing:
            return existing.to_dict()
        raise HTTPException(status_code=400, detail="Error verifying email")
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/history", response_model=HistoryListResponse)
async def get_history(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get recent verification history.
    
    Returns the most recent email verifications.
    """
    try:
        records = db.query(VerificationHistory).order_by(
            VerificationHistory.created_at.desc()
        ).limit(limit).all()
        
        return {
            "total": len(records),
            "records": [r.to_dict() for r in records]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/verify/{email}")
async def verify_email_by_email(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Verify email via URL parameter (alternative endpoint).
    """
    request = VerifyEmailRequest(email=email)
    return await verify_email_endpoint(request, db)


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get verification statistics.
    """
    total = db.query(EmailVerification).count()
    valid = db.query(EmailVerification).filter(
        EmailVerification.status == "valid"
    ).count()
    risky = db.query(EmailVerification).filter(
        EmailVerification.status == "risky"
    ).count()
    invalid = db.query(EmailVerification).filter(
        EmailVerification.status == "invalid"
    ).count()
    
    return {
        "total_verified": total,
        "valid": valid,
        "risky": risky,
        "invalid": invalid,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
