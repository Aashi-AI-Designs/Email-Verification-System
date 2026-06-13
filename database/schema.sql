-- Email Verification Schema
-- Design Goals:
-- 1. Store email verification history
-- 2. Avoid duplicate checks (cache results)
-- 3. Track all validation flags for analysis
-- 4. Enable efficient querying by email, domain, date

-- Table 1: Verification Results
-- Why this structure?
-- - Atomic record of a single verification check
-- - Email is unique per session (compound key would be email + timestamp if we allow duplicates)
-- - Store all check results so we can understand the logic
-- - TTL concept: results older than 30 days could be refreshed
CREATE TABLE email_verifications (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    domain VARCHAR(255) NOT NULL,
    
    -- Validation flags (boolean results from each check)
    is_valid_format BOOLEAN NOT NULL,
    domain_exists BOOLEAN NOT NULL,
    mx_found BOOLEAN NOT NULL,
    is_disposable BOOLEAN NOT NULL,
    is_role_based BOOLEAN NOT NULL,
    
    -- Final verdict
    status VARCHAR(20) NOT NULL CHECK (status IN ('valid', 'risky', 'invalid')),
    reason TEXT,
    
    -- Metadata for analysis
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Index decisions:
    -- Email lookups are most common → add index
    -- Domain analysis is useful → add index
    -- Time-series queries for "recent checks" → add index
    INDEX idx_email (email),
    INDEX idx_domain (domain),
    INDEX idx_created_at (created_at)
);

-- Table 2: Verification History (if you want to track multiple checks per email)
-- Optional: only add this if you want full audit trail
CREATE TABLE verification_history (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    
    is_valid_format BOOLEAN NOT NULL,
    domain_exists BOOLEAN NOT NULL,
    mx_found BOOLEAN NOT NULL,
    is_disposable BOOLEAN NOT NULL,
    is_role_based BOOLEAN NOT NULL,
    
    status VARCHAR(20) NOT NULL,
    reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_email_history (email),
    INDEX idx_created_at_history (created_at)
);

-- Why two tables?
-- 1. email_verifications = latest check (cache-like behavior)
-- 2. verification_history = audit trail of all checks
-- This is a common pattern: "current state" + "historical records"
-- Interview takeaway: Think about query patterns, not just storing data
