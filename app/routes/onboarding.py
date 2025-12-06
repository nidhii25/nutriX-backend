from datetime import date, datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.users import User
from app.models.profiles import UserProfile
from app.models.athlete_meta import AthleteMeta
from app.models.dietary_preferences import DietaryPreferences


router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


# ------------------------------------------------------
#  POST /complete/{user_id}
#  → Saves onboarding questionnaire answers
#  → Computes BMI / BMR / TDEE
# ------------------------------------------------------
@router.post("/complete/{user_id}")
async def complete_onboarding(
    user_id: str,
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):

    # Validate user existence
    q_user = await db.execute(select(User).where(User.id == user_id))
    user = q_user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # --------------------------------------------------
    # Parse DOB
    # --------------------------------------------------
    dob_value = None
    if body.get("dob"):
        try:
            dob_value = datetime.fromisoformat(body["dob"]).date()
        except:
            raise HTTPException(400, "Invalid DOB format. Use YYYY-MM-DD")

    # --------------------------------------------------
    # 1️⃣ Save PHYSICAL PROFILE
    # --------------------------------------------------
    q_profile = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = q_profile.scalar_one_or_none()

    if profile:
        profile.gender = body.get("gender") # type: ignore
        profile.dob = dob_value # type: ignore
        profile.height_cm = body.get("height_cm") # type: ignore
        profile.current_weight_kg = body.get("current_weight_kg") # type: ignore
        profile.activity_level = body.get("activity_level") # type: ignore
        profile.kitchen_type = body.get("kitchen_type") # type: ignore
        profile.water_target_liters = body.get("water_target_liters") # type: ignore
    else:
        profile = UserProfile(
            user_id=user_id,
            gender=body.get("gender"),
            dob=dob_value,
            height_cm=body.get("height_cm"),
            current_weight_kg=body.get("current_weight_kg"),
            activity_level=body.get("activity_level"),
            kitchen_type=body.get("kitchen_type"),
            water_target_liters=body.get("water_target_liters"),
        )
        db.add(profile)

    # --------------------------------------------------
    # Compute BMI / BMR / TDEE
    # --------------------------------------------------
    height = body.get("height_cm")
    weight = body.get("current_weight_kg")
    gender = body.get("gender")
    activity = body.get("activity_level")

    # BMI
    bmi = None
    if height and weight:
        h_m = height / 100
        if h_m > 0:
            bmi = round(weight / (h_m * h_m), 2)

    # AGE
    age = None
    if dob_value:
        today = date.today()
        age = today.year - dob_value.year - ((today.month, today.day) < (dob_value.month, dob_value.day))

    # BMR
    bmr = None
    if gender and height and weight and age is not None:
        if gender.lower() == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Activity multipliers
    activity_map = {
        "sedentary": 1.2,
        "light": 1.375,
        "active": 1.55,
        "very_active": 1.725,
    }

    multiplier = activity_map.get(str(activity).lower(), 1.2)

    # TDEE
    tdee = round(bmr * multiplier) if bmr else None

    # --------------------------------------------------
    # 2️⃣ Save ATHLETE OR LIFESTYLE DATA
    # --------------------------------------------------
    user_type = body.get("what_drives_you")  # Athlete / Lifestyle

    q_meta = await db.execute(select(AthleteMeta).where(AthleteMeta.user_id == user_id))
    meta = q_meta.scalar_one_or_none()

    # Select correct field: athlete uses phase, lifestyle uses primary_goal
    phase_or_goal = (
        body.get("phase") if user_type == "Athlete"
        else body.get("primary_goal")
    )

    if meta:
        meta.is_athlete = (user_type == "Athlete") # type: ignore
        meta.sport = body.get("sport") # type: ignore
        meta.position_role = body.get("role") # type: ignore
        meta.current_phase = phase_or_goal # type: ignore
    else:
        meta = AthleteMeta(
            user_id=user_id,
            is_athlete=(user_type == "Athlete"),
            sport=body.get("sport"),
            position_role=body.get("role"),
            current_phase=phase_or_goal,
        )
        db.add(meta)

    # --------------------------------------------------
    # 3️⃣ Save DIETARY PREFERENCES
    # --------------------------------------------------
    q_prefs = await db.execute(select(DietaryPreferences).where(DietaryPreferences.user_id == user_id))
    prefs = q_prefs.scalar_one_or_none()

    if prefs:
        prefs.diet_type = body.get("diet_type") # type: ignore
        prefs.allergies = body.get("allergies") # type: ignore
        prefs.dislikes = body.get("dislikes") # type: ignore
        prefs.medical_conditions = body.get("medical_conditions") # type: ignore
        prefs.supplements_stack = body.get("supplements_stack") # type: ignore
    else: 
        prefs = DietaryPreferences(
            user_id=user_id,
            diet_type=body.get("diet_type"),
            allergies=body.get("allergies"),
            dislikes=body.get("dislikes"),
            medical_conditions=body.get("medical_conditions"),
            supplements_stack=body.get("supplements_stack"),
        )
        db.add(prefs)

    await db.commit()

    return {
        "message": "Onboarding completed successfully",
        "bmi": bmi,
        "bmr": round(bmr) if bmr else None,
        "tdee": tdee,
    }


# ------------------------------------------------------
#  GET /{user_id}
#  → Returns ALL onboarding data merged
# ------------------------------------------------------
@router.get("/{user_id}")
async def get_onboarding(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):

    # User
    q_user = await db.execute(select(User).where(User.id == user_id))
    user = q_user.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    # Profile
    q_profile = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = q_profile.scalar_one_or_none()

    # Athlete/Lifestyle
    q_meta = await db.execute(select(AthleteMeta).where(AthleteMeta.user_id == user_id))
    meta = q_meta.scalar_one_or_none()

    # Dietary preferences
    q_prefs = await db.execute(select(DietaryPreferences).where(DietaryPreferences.user_id == user_id))
    prefs = q_prefs.scalar_one_or_none()

    # Recompute BMI/BMR/TDEE for display
    bmi = None
    bmr = None
    tdee = None

    if profile and profile.height_cm and profile.current_weight_kg: # type: ignore
        h_m = profile.height_cm / 100
        if h_m > 0: # type: ignore
            bmi = round(profile.current_weight_kg / (h_m * h_m), 1) # type: ignore

    # AGE
    age = None
    if profile and profile.dob: # type: ignore
        today = date.today()
        age = today.year - profile.dob.year - ((today.month, today.day) < (profile.dob.month, profile.dob.day))

    # BMR + TDEE
    if profile and age is not None:
        if profile.gender and profile.height_cm and profile.current_weight_kg: # type: ignore
            gender_norm = profile.gender.lower()
            if gender_norm == "male":
                bmr = 10 * profile.current_weight_kg + 6.25 * profile.height_cm - 5 * age + 5
            else:
                bmr = 10 * profile.current_weight_kg + 6.25 * profile.height_cm - 5 * age - 161

            activity_map = {
                "sedentary": 1.2,
                "light": 1.375,
                "active": 1.55,
                "very_active": 1.725,
            }
            factor = activity_map.get(str(profile.activity_level).lower(), 1.2)
            tdee = round(bmr * factor)
            bmr = round(bmr)

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
        },
        "profile": {
            "gender": profile.gender if profile else None,
            "dob": str(profile.dob) if profile else None,
            "height_cm": profile.height_cm if profile else None,
            "current_weight_kg": profile.current_weight_kg if profile else None,
            "activity_level": profile.activity_level if profile else None,
            "kitchen_type": profile.kitchen_type if profile else None,
            "water_target_liters": profile.water_target_liters if profile else None,
        },
        "athlete_or_lifestyle": {
            "is_athlete": meta.is_athlete if meta else None,
            "sport": meta.sport if meta else None,
            "role": meta.position_role if meta else None,
            "phase_or_goal": meta.current_phase if meta else None,
            "bmi": bmi,
            "bmr": bmr,
            "tdee": tdee,
        },
        "dietary_preferences": {
            "diet_type": prefs.diet_type if prefs else None,
            "allergies": prefs.allergies if prefs else None,
            "dislikes": prefs.dislikes if prefs else None,
            "medical_conditions": prefs.medical_conditions if prefs else None,
            "supplements_stack": prefs.supplements_stack if prefs else None,
        },
    }
