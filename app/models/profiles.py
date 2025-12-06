import uuid
from sqlalchemy import Column, String, Date, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    gender = Column(String)
    dob = Column(Date)
    height_cm = Column(Integer)
    current_weight_kg = Column(Float)
    activity_level = Column(String)
    kitchen_type = Column(String)
    water_target_liters = Column(Float)

    user = relationship("User", backref="profile")
