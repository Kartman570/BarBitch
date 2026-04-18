import json
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from jose import JWTError, jwt

# All valid permission identifiers
ALL_PERMISSIONS = {"tables", "items", "stock", "stats", "users", "roles"}

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
        "permissions": ["tables", "items", "stock", "stats", "users"],
    },
    {
        "name": "admin",
        "description": "Administrator — unrestricted access",
        "permissions": ["tables", "items", "stock", "stats", "users", "roles"],
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


def create_access_token(user_id: int, secret_key: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> int:
    """Returns user_id. Raises JWTError on invalid/expired token."""
    payload = jwt.decode(token, secret_key, algorithms=[_ALGORITHM])
    return int(payload["sub"])
