import uuid
from sqlalchemy import Column, String, Boolean, Float,ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class AthleteMeta(Base):
    __tablename__ = "athlete_meta"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    is_athlete = Column(Boolean, default=False)
    sport = Column(String)
    position_role = Column(String)
    current_phase = Column(String)

    user = relationship("User", backref="athlete_meta")
