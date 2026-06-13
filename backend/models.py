from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    
    is_valid_format = Column(Boolean, nullable=False)
    domain_exists = Column(Boolean, nullable=False)
    mx_found = Column(Boolean, nullable=False)
    is_disposable = Column(Boolean, nullable=False)
    is_role_based = Column(Boolean, nullable=False)
    
    status = Column(String(20), nullable=False)
    reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "email": self.email,
            "domain": self.domain,
            "is_valid_format": self.is_valid_format,
            "domain_exists": self.domain_exists,
            "mx_found": self.mx_found,
            "is_disposable": self.is_disposable,
            "is_role_based": self.is_role_based,
            "status": self.status,
            "reason": self.reason,
        }


class VerificationHistory(Base):
    __tablename__ = "verification_history"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), nullable=False)
    
    is_valid_format = Column(Boolean, nullable=False)
    domain_exists = Column(Boolean, nullable=False)
    mx_found = Column(Boolean, nullable=False)
    is_disposable = Column(Boolean, nullable=False)
    is_role_based = Column(Boolean, nullable=False)
    
    status = Column(String(20), nullable=False)
    reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            "email": self.email,
            "domain": self.domain,
            "is_valid_format": self.is_valid_format,
            "domain_exists": self.domain_exists,
            "mx_found": self.mx_found,
            "is_disposable": self.is_disposable,
            "is_role_based": self.is_role_based,
            "status": self.status,
            "reason": self.reason,
        }
