import os
import hashlib
import hmac
import jwt
from datetime import datetime, timedelta
import config

SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-SHA256 with a unique random salt."""
    salt = os.urandom(16)
    iterations = 100000
    db_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    # Format: algorithm$iterations$salt_hex$hash_hex
    return f"pbkdf2_sha256${iterations}${salt.hex()}${db_hash.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password by comparing its pbkdf2 hash in constant time."""
    if not hashed:
        return False
    try:
        parts = hashed.split('$')
        if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        original_hash = bytes.fromhex(parts[3])
        
        test_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(original_hash, test_hash)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generate a signed JWT token containing user profile information."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    if isinstance(encoded_jwt, bytes):
        return encoded_jwt.decode('utf-8')
    return encoded_jwt
