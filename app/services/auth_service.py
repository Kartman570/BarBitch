import json
from datetime import datetime, timedelta, timezone

import re
import secrets
import jwt
import bcrypt as _bcrypt
from jwt.exceptions import PyJWTError as JWTError  # noqa: F401 (re-exported)

# All valid permission identifiers
ALL_PERMISSIONS = {"tables", "items", "stock", "stats", "users", "roles", "discounts"}

# Default roles seeded on first run
DEFAULT_ROLES = [
    {
        "name": "barman",
        "description": "Bartender / cashier — manages tables and orders",
        "permissions": ["tables"],
    },
    {
        "name": "cook",
        "description": "Kitchen staff — manages stock and views items",
        "permissions": ["items", "stock"],
    },
    {
        "name": "manager",
        "description": "Manager — full operational access plus staff management",
        "permissions": ["tables", "items", "stock", "stats", "users", "discounts"],
    },
    {
        "name": "admin",
        "description": "Administrator — unrestricted access",
        "permissions": ["tables", "items", "stock", "stats", "users", "roles", "discounts"],
    },
]


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def encode_permissions(permissions: list[str]) -> str:
    return json.dumps(sorted(permissions))


def decode_permissions(raw: str) -> list[str]:
    try:
        return json.loads(raw)
    except Exception:
        return []


_ALGORITHM = "HS256"
_TOKEN_EXPIRE_HOURS = 12
REFRESH_TOKEN_EXPIRE_DAYS = 30

_PASSWORD_MIN_LEN = 8
_PASSWORD_SPECIAL = re.compile(r'[0-9!@#$%^&*_\-+=]')


def create_access_token(user_id: int, secret_key: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> int:
    """Returns user_id. Raises JWTError on invalid/expired token."""
    payload = jwt.decode(token, secret_key, algorithms=[_ALGORITHM])
    return int(payload["sub"])


def create_refresh_token_string() -> str:
    return secrets.token_urlsafe(32)


def validate_password_complexity(password: str) -> str:
    """Raises ValueError if password doesn't meet complexity requirements."""
    if len(password) < _PASSWORD_MIN_LEN:
        raise ValueError(f"Password must be at least {_PASSWORD_MIN_LEN} characters")
    if not _PASSWORD_SPECIAL.search(password):
        raise ValueError("Password must contain at least one digit or special character (!@#$%^&*_-+=)")
    return password
