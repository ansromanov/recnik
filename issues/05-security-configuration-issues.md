# Issue 5: Security and Configuration Issues

## Problem Description

The application has several critical security vulnerabilities and configuration issues including hardcoded secrets, missing security headers, improper authentication handling, and insecure default configurations.

## Impact

- **Security Vulnerabilities**: Risk of data breaches and unauthorized access
- **Compliance Issues**: May not meet security standards
- **User Privacy**: Potential exposure of sensitive user data
- **Production Risks**: Unsafe for production deployment

## Root Causes

### 1. Hardcoded Secrets and Default Values

```python
# In config.py - insecure defaults
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vocab_user:vocab_pass@localhost:5432/serbian_vocabulary")
```

### 2. Missing Security Headers

```python
# No security headers configured
# Missing: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
# No CORS proper configuration
```

### 3. Insecure Authentication

```python
# In app.py - JWT token handling issues
@app.route("/api/auth/me")
@jwt_required()
def get_current_user():
    # No token validation
    # No refresh token mechanism
    # No token expiration handling
```

### 4. Database Security Issues

```sql
-- In init.sql - no user authentication
-- No row-level security
-- No data encryption
-- Weak password requirements
```

### 5. Environment Configuration Problems

```bash
# Missing environment validation
# No configuration validation
# No secrets management
# No production vs development separation
```

## Evidence from Codebase

### Insecure Configuration

```python
# config.py - multiple security issues
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "https://localhost:443,https://localhost:3000,http://localhost:3000,http://localhost:3001",
).split(",")

# No validation of CORS origins
# Allows all localhost connections
# No HTTPS enforcement
```

### Missing Security Headers

```python
# No security middleware
# No CSRF protection
# No rate limiting
# No input validation
```

### Database Security

```sql
-- No user authentication in database
-- No audit logging
-- No backup encryption
-- No connection encryption
```

### Frontend Security Issues

```javascript
// In frontend/src/services/api.js
// No CSRF token handling
// No secure cookie settings
// No input sanitization
// No XSS protection
```

## Solutions

### 1. Implement Proper Security Configuration

```python
# security.py - Security configuration
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def configure_security(app):
    # Security headers
    Talisman(app,
        content_security_policy={
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline'",
            'style-src': "'self' 'unsafe-inline'",
            'img-src': "'self' data: https:",
            'font-src': "'self'",
        },
        force_https=True,
        strict_transport_security=True,
        session_cookie_secure=True
    )

    # Rate limiting
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )

    # CORS configuration
    CORS(app,
        origins=app.config['ALLOWED_ORIGINS'],
        supports_credentials=True,
        methods=['GET', 'POST', 'PUT', 'DELETE'],
        allow_headers=['Content-Type', 'Authorization']
    )
```

### 2. Implement Secure Authentication

```python
# auth.py - Secure authentication
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import timedelta
import bcrypt

class SecureAuth:
    def __init__(self, app):
        self.app = app
        self.setup_jwt()

    def setup_jwt(self):
        self.app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
        self.app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
        self.app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
        self.app.config['JWT_COOKIE_SECURE'] = True
        self.app.config['JWT_COOKIE_HTTPONLY'] = True
        self.app.config['JWT_COOKIE_SAMESITE'] = 'Strict'

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def verify_password(self, password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed)

    def create_tokens(self, user_id):
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        return access_token, refresh_token
```

### 3. Add Input Validation and Sanitization

```python
# validation.py - Input validation
from marshmallow import Schema, fields, validate
from werkzeug.security import safe_str_cmp

class UserRegistrationSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    password = fields.Str(required=True, validate=validate.Length(min=8))
    email = fields.Email(required=True)

class WordSchema(Schema):
    serbian_word = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    english_translation = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    category_id = fields.Int(required=True, validate=validate.Range(min=1))

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    import html
    return html.escape(text.strip())
```

### 4. Implement Database Security

```sql
-- database_security.sql
-- Enable row-level security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_vocabulary ENABLE ROW LEVEL SECURITY;
ALTER TABLE practice_sessions ENABLE ROW LEVEL SECURITY;

-- Create security policies
CREATE POLICY user_isolation ON users
    FOR ALL USING (id = current_user_id());

CREATE POLICY vocabulary_isolation ON user_vocabulary
    FOR ALL USING (user_id = current_user_id());

-- Add audit logging
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100),
    table_name VARCHAR(100),
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create audit trigger
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (user_id, action, table_name, record_id, new_values)
        VALUES (current_user_id(), 'INSERT', TG_TABLE_NAME, NEW.id, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (user_id, action, table_name, record_id, old_values, new_values)
        VALUES (current_user_id(), 'UPDATE', TG_TABLE_NAME, NEW.id, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (user_id, action, table_name, record_id, old_values)
        VALUES (current_user_id(), 'DELETE', TG_TABLE_NAME, OLD.id, to_jsonb(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```

### 5. Add Environment Validation

```python
# config_validation.py - Environment validation
import os
from typing import List

class ConfigValidator:
    REQUIRED_ENV_VARS = [
        'JWT_SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'OPENAI_API_KEY'
    ]

    SECURE_ENV_VARS = [
        'JWT_SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL'
    ]

    @classmethod
    def validate_config(cls):
        missing_vars = []
        insecure_vars = []

        for var in cls.REQUIRED_ENV_VARS:
            if not os.getenv(var):
                missing_vars.append(var)

        for var in cls.SECURE_ENV_VARS:
            value = os.getenv(var)
            if value and cls._is_insecure_value(value):
                insecure_vars.append(var)

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

        if insecure_vars:
            raise ValueError(f"Insecure environment variables detected: {insecure_vars}")

    @staticmethod
    def _is_insecure_value(value: str) -> bool:
        insecure_patterns = [
            'default', 'password', 'secret', 'key',
            'localhost', '127.0.0.1', 'admin'
        ]
        return any(pattern in value.lower() for pattern in insecure_patterns)
```

### 6. Implement Frontend Security

```javascript
// security.js - Frontend security utilities
export class SecurityUtils {
    static sanitizeInput(input) {
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    }

    static validatePassword(password) {
        const minLength = 8;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        return password.length >= minLength &&
               hasUpperCase &&
               hasLowerCase &&
               hasNumbers &&
               hasSpecialChar;
    }

    static setSecureCookies(token, refreshToken) {
        document.cookie = `access_token=${token}; Secure; SameSite=Strict; HttpOnly`;
        document.cookie = `refresh_token=${refreshToken}; Secure; SameSite=Strict; HttpOnly`;
    }

    static getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }
}
```

## Implementation Steps

### Phase 1: Critical Security Fixes (1 week)

1. **Remove Hardcoded Secrets** (2 days)
   - Move all secrets to environment variables
   - Add configuration validation
   - Implement secrets management

2. **Add Security Headers** (2 days)
   - Implement CSP, HSTS, X-Frame-Options
   - Add CSRF protection
   - Configure secure cookies

3. **Implement Rate Limiting** (1 day)
   - Add request rate limiting
   - Implement IP-based blocking
   - Add brute force protection

4. **Database Security** (2 days)
   - Enable row-level security
   - Add audit logging
   - Implement connection encryption

### Phase 2: Authentication Security (1 week)

1. **Secure JWT Implementation** (3 days)
   - Add refresh tokens
   - Implement token rotation
   - Add token blacklisting

2. **Input Validation** (2 days)
   - Add comprehensive input validation
   - Implement XSS protection
   - Add SQL injection prevention

3. **Password Security** (2 days)
   - Implement strong password requirements
   - Add password hashing
   - Add password reset functionality

### Phase 3: Production Hardening (1 week)

1. **Environment Security** (3 days)
   - Production environment setup
   - Secrets management
   - SSL/TLS configuration

2. **Monitoring & Logging** (2 days)
   - Security event logging
   - Intrusion detection
   - Audit trail implementation

3. **Compliance & Testing** (2 days)
   - Security testing
   - Vulnerability scanning
   - Compliance checking

## Security Checklist

- [ ] Remove all hardcoded secrets
- [ ] Implement proper CORS configuration
- [ ] Add security headers
- [ ] Enable HTTPS enforcement
- [ ] Implement rate limiting
- [ ] Add input validation
- [ ] Enable database encryption
- [ ] Implement audit logging
- [ ] Add CSRF protection
- [ ] Configure secure cookies
- [ ] Implement password hashing
- [ ] Add XSS protection
- [ ] Enable row-level security
- [ ] Add security monitoring

## Success Metrics

- **Security Score**: Achieve 90+ security score
- **Vulnerability Count**: Zero critical vulnerabilities
- **Compliance**: Meet industry security standards
- **Incident Response**: <1 hour detection time

## Priority: CRITICAL

**Estimated Time**: 3 weeks for complete security implementation
**Business Impact**: Critical for data protection and compliance
