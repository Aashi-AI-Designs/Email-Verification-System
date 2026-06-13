from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class VerifyEmailRequest(BaseModel):
    """Request schema for email verification"""
    email: str = Field(..., example="user@example.com")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john@gmail.com"
            }
        }


class VerificationResponse(BaseModel):
    """Response schema for email verification"""
    email: str
    domain: str
    is_valid_format: bool
    domain_exists: bool
    mx_found: bool
    is_disposable: bool
    is_role_based: bool
    status: str  # 'valid', 'risky', 'invalid'
    reason: str
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john@example.com",
                "domain": "example.com",
                "is_valid_format": True,
                "domain_exists": True,
                "mx_found": True,
                "is_disposable": False,
                "is_role_based": False,
                "status": "valid",
                "reason": "Domain and MX records found, no red flags"
            }
        }


class HistoryResponse(BaseModel):
    """Single history record"""
    email: str
    domain: str
    status: str
    reason: str
    created_at: Optional[datetime] = None


class HistoryListResponse(BaseModel):
    """List of history records"""
    total: int
    records: list[HistoryResponse]
