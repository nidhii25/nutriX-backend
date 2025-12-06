import uuid
from sqlalchemy import Column, String, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class DietaryPreferences(Base):
    __tablename__ = "dietary_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    diet_type = Column(String)
    allergies = Column(ARRAY(String))
    dislikes = Column(ARRAY(String))
    medical_conditions = Column(ARRAY(String))
    supplements_stack = Column(ARRAY(String))

    user = relationship("User", backref="diet_preferences")
