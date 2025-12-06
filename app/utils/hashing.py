from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    bcrypt__rounds=8,  # faster than 12
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt, truncating to 72 chars for safety."""
    if len(password.encode("utf-8")) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def verify_password(raw: str, hashed: str) -> bool:
    """Verify a raw password against a stored bcrypt hash."""
    raw = raw[:72]
    return pwd_context.verify(raw, hashed)
