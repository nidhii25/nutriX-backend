from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.models.users import User
from app.utils.hashing import hash_password, verify_password
from app.utils.jwt_handler import create_token, decode_token
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


# -------------------------
# HELPERS
# -------------------------

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return payload


# -------------------------
# /me (MUST BE ABOVE /{user_id})
# -------------------------

@router.get("/me")
async def get_me(user = Depends(get_current_user)):
    return user


# -------------------------
# REGISTER
# -------------------------
@router.post("/register")
async def register_user(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> dict:
    email = payload.email
    password = payload.password

    if len(password) > 72:
        raise HTTPException(status_code=400, detail="Password too long")

    full_name = payload.full_name

    check = await db.execute(select(User).where(User.email == email))
    existing = check.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(password)
    new_user = User(email=email, full_name=full_name, hashed_password=hashed)

    db.add(new_user)
    await db.commit()

    return {"message": "User registered"}


# -------------------------
# LOGIN
# -------------------------
@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    email = payload.email
    password = payload.password

    query = await db.execute(select(User).where(User.email == email))
    user = query.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Wrong password")

    token = create_token({"user_id": str(user.id)})

    return {"access_token": token, "user_id": str(user.id)}


# -------------------------
# GET USER (dynamic route)
# -------------------------
@router.get("/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(User).where(User.id == user_id))
    user = query.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "created_at": user.created_at
    }
