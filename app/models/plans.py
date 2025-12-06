import uuid
from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base


class NutritionPlan(Base):
    __tablename__ = "nutrition_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)
    goal = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    status = Column(String, default="active")

    days = Column(JSON, nullable=False)

    created_at = Column(String)
    startDate = Column(String)

    user = relationship("User", backref="nutrition_plans")
