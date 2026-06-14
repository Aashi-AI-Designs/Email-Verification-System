import re
import dns.resolver
import dns.exception
from typing import Dict, Tuple

# Disposable email domains list (expanded for demo)
DISPOSABLE_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",  # Free emails
    "tempmail.com", "guerrillamail.com", "mailinator.com",  # Temp emails
    "10minutemail.com", "throwaway.email", "trashmail.com",
    "yopmail.com", "maildrop.io", "temp-mail.org",
}

ROLE_BASED_PREFIXES = {
    "admin", "support", "help", "info", "noreply",
    "contact", "sales", "hello", "team", "abuse",
    "no-reply", "notification", "billing", "security",
}


def validate_email_format(email: str) -> Tuple[bool, str]:
    """
    Validate email format using regex.

    Returns: (is_valid, reason)
    """
    # Simple but effective regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    # Check length limits
    if len(email) > 254:
        return False, "Email too long (max 254 characters)"
    
    local_part, domain = email.split('@')
    if len(local_part) > 64:
        return False, "Local part too long (max 64 characters)"
    
    return True, "Valid format"


def extract_domain(email: str) -> str:
    """Extract and normalize domain from email"""
    email = email.strip().lower()
    return email.split('@')[1]


async def check_mx_records(domain: str) -> Tuple[bool, bool, str]:
    """
    Check if domain exists and has MX records.
    Returns: (domain_exists, mx_found, reason)
    """
    try:
        # Check if domain has MX records (actual mail servers)
        mx_records = dns.resolver.resolve(domain, 'MX')
        if mx_records:
            return True, True, "MX records found"
    except dns.resolver.NXDOMAIN:
        return False, False, "Domain does not exist"
    except dns.resolver.NoAnswer:
        return False, False, "No MX records found"
    except dns.exception.Timeout:
        return False, False, "DNS lookup timeout"
    except Exception as e:
        return False, False, f"DNS error: {str(e)}"
    
    return True, False, "Domain exists but no MX records"


def is_disposable_domain(domain: str) -> Tuple[bool, str]:
    """
    Check if domain is a disposable/temporary email provider.
    In production, you'd fetch this from an API or database
    """
    domain = domain.lower()
    
    if domain in DISPOSABLE_DOMAINS:
        return True, "Disposable email domain"
    
    return False, "Not a known disposable domain"


def is_role_based_email(email: str) -> Tuple[bool, str]:
    """
    Detect role-based emails (admin@, support@, etc).
    """
    local_part = email.split('@')[0].lower()
    
    if local_part in ROLE_BASED_PREFIXES:
        return True, f"Role-based email ({local_part})"
    
    # Check for common patterns like admin_*, support_*
    for prefix in ROLE_BASED_PREFIXES:
        if local_part.startswith(prefix + '_') or local_part.startswith(prefix + '-'):
            return True, f"Role-based email ({prefix}*)"
    
    return False, "Not a role-based email"


def determine_status(
    is_valid_format: bool,
    domain_exists: bool,
    mx_found: bool,
    is_disposable: bool,
    is_role_based: bool
) -> Tuple[str, str]:
    """
    Determine final verification status based on all checks.
    Returns: (status, reason)
    """
    
    # Invalid: format is wrong or domain doesn't exist
    if not is_valid_format:
        return "invalid", "Invalid email format"
    
    if not domain_exists or not mx_found:
        return "invalid", "Domain does not exist or has no MX records"
    
    # Risky: might be valid but has red flags
    reasons = []
    if is_disposable:
        reasons.append("disposable domain")
    if is_role_based:
        reasons.append("role-based email")
    
    if reasons:
        return "risky", f"Domain exists but flagged as risky: {', '.join(reasons)}"
    
    # Valid: passed all checks
    return "valid", "Domain and MX records found, no red flags"


async def verify_email(email: str) -> Dict:
    """
    Complete email verification workflow.
    """
    
    # Step 1: Format validation
    is_valid_format, format_reason = validate_email_format(email)
    
    # Step 2: Extract domain
    domain = extract_domain(email)
    
    # Step 3: Domain & MX check
    domain_exists, mx_found, mx_reason = await check_mx_records(domain)
    
    # Step 4: Disposable domain check
    is_disposable, disposable_reason = is_disposable_domain(domain)
    
    # Step 5: Role-based check
    is_role_based, role_reason = is_role_based_email(email)
    
    # Step 6: Determine final status
    status, final_reason = determine_status(
        is_valid_format,
        domain_exists,
        mx_found,
        is_disposable,
        is_role_based
    )
    
    return {
        "email": email,
        "domain": domain,
        "is_valid_format": is_valid_format,
        "domain_exists": domain_exists,
        "mx_found": mx_found,
        "is_disposable": is_disposable,
        "is_role_based": is_role_based,
        "status": status,
        "reason": final_reason,
    }
