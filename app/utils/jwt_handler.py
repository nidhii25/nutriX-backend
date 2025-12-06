from datetime import datetime, timedelta

from jose import jwt, JWTError
from fastapi import HTTPException

SECRET_KEY: str = "secretkey123"
ALGO: str = "HS256"


def create_token(data: dict) -> str:
    """Create a short-lived JWT access token from the given payload."""
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(days=3)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGO)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        if payload.get("exp") and datetime.utcnow().timestamp() > payload["exp"]:
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")