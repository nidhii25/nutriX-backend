from pydantic import BaseModel
from typing import Dict, Any


class GeneratePlanRequest(BaseModel):
    user_profile: Dict[str, Any]   # required
    formData: Dict[str, Any]       # required


class NutritionPlanResponse(BaseModel):
    id: str
    name: str
    goal: str
    duration: int
    status: str
    days: Any
    startDate: str
    created_at: str
