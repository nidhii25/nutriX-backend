from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_meals() -> dict:
    return {"msg": "meals ok"}
