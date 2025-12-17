from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from .base import Base

class InteractionStatus(str, enum.Enum):
    CALLED = "called"
    EMAILED = "emailed"
    SPOKE = "spoke"

class CustomerInteraction(Base):
    __tablename__ = "customer_interactions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    user_id = Column(Integer, nullable=True) # Removed ForeignKey("users.id") as User model is not in SQLAlchemy
    status = Column(String(50), nullable=False) # Storing enum as string for SQLite simplicity
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships can be added if needed, but for now we just need the foreign keys
    # customer = relationship("Customer", back_populates="interactions")
