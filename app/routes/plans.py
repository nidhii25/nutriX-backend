from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime
import uuid

from app.database.connection import get_db
from app.models.plans import NutritionPlan
from app.schemas.plans import GeneratePlanRequest,SwapMealRequest
from app.services.ai_service import generate_plan_ai, generate_swap_ai


router = APIRouter( tags=["Nutrition Plans"])


# ----------------------------------------------------------
# 1) Generate Plan (AI)
# ----------------------------------------------------------
@router.post("/generate")
async def generate_plan(body: GeneratePlanRequest, db: AsyncSession = Depends(get_db)):

    # Ask Gemini to generate the plan
    plan_data = await generate_plan_ai(body.user_profile, body.formData)

    # Save to DB
    plan = NutritionPlan(
        id=uuid.uuid4(),
        user_id=body.user_profile["id"],
        name=plan_data["name"],
        goal=plan_data["goal"],
        duration=plan_data["duration"],
        status="active",
        days=plan_data["days"],
        startDate=datetime.utcnow().isoformat(),
        created_at=datetime.utcnow().isoformat(),
    )

    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return {
        "id": str(plan.id),
        "name": plan.name,
        "goal": plan.goal,
        "duration": plan.duration,
        "status": plan.status,
        "days": plan.days,
        "startDate": plan.startDate,
        "created_at": plan.created_at,
    }


# ----------------------------------------------------------
# 2) Get active plan for a user
# ----------------------------------------------------------
@router.get("/{user_id}")
async def get_user_plan(user_id: str, db: AsyncSession = Depends(get_db)):

    q = await db.execute(
        select(NutritionPlan).where(
            NutritionPlan.user_id == user_id,
            NutritionPlan.status == "active"
        )
    )

    plans = list(q.scalars().all())   # convert to list so .sort() works

    if not plans:
        return {"message": "No active plan", "plan": None}

    # Sort by created_at (latest first)
    plans.sort(key=lambda x: x.created_at, reverse=True)

    plan = plans[0]


    return {
        "id": str(plan.id),
        "name": plan.name,
        "goal": plan.goal,
        "duration": plan.duration,
        "status": plan.status,
        "days": plan.days,
        "startDate": plan.startDate,
        "created_at": plan.created_at,
    }


# ----------------------------------------------------------
# 3) Delete plan
# ----------------------------------------------------------
@router.delete("/{plan_id}")
async def delete_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(NutritionPlan).where(NutritionPlan.id == plan_id))
    await db.commit()
    return {"message": "Plan deleted"}


# ----------------------------------------------------------
# 4) Update Meal Status  (eaten / pending / skipped)
# ----------------------------------------------------------
@router.put("/{plan_id}/meal/{meal_id}")
async def update_meal_status(plan_id: str, meal_id: str, status: str, db: AsyncSession = Depends(get_db)):

    allowed = ["eaten", "pending", "skipped"]
    if status not in allowed:
        raise HTTPException(400, f"Invalid status. Allowed: {allowed}")

    q = await db.execute(select(NutritionPlan).where(NutritionPlan.id == plan_id))
    plan = q.scalar_one_or_none()

    if not plan:
        raise HTTPException(404, "Plan not found")

    found = False

    for day in plan.days:
        for meal in day["meals"]:
            if meal["id"] == meal_id: #type: ignore
                meal["status"] = status #type: ignore
                found = True

    if not found:
        raise HTTPException(404, "Meal not found")

    await db.execute(
        update(NutritionPlan).where(NutritionPlan.id == plan_id).values(days=plan.days)
    )
    await db.commit()

    return {"message": "Meal status updated"}


# ----------------------------------------------------------
# 5) Swap Meal (AI)
# ----------------------------------------------------------
@router.post("/{plan_id}/swap")
async def swap_meal(plan_id: str, body: SwapMealRequest, db: AsyncSession = Depends(get_db)):
    meal = body.model_dump()

    # validate
    if "id" not in meal:
        raise HTTPException(400, "Meal must include 'id' field")

    # AI replacement
    new_meal = await generate_swap_ai(meal)
    new_meal["id"] = str(uuid.uuid4())
    new_meal["isSwapped"] = True
    new_meal["status"] = "pending"
    
    q = await db.execute(select(NutritionPlan).where(NutritionPlan.id == plan_id))
    plan = q.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")

    replaced = False
    for day in plan.days:
        for idx, m in enumerate(day["meals"]): #type: ignore
            if m["id"] == meal["id"]:
                day["meals"][idx] = new_meal#type: ignore
                replaced = True

    if not replaced:
        raise HTTPException(404, "Meal to swap not found")

    await db.execute(
        update(NutritionPlan).where(NutritionPlan.id == plan_id).values(days=plan.days)
    )
    await db.commit()

    return {"new_meal": new_meal}
