import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Index, Text
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.types import TypeDecorator, CHAR
import uuid
from datetime import datetime, timezone

from .base import Base

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses SQLite BLOB for storage to be efficient, but handles conversion to/from uuid.UUID.
    """
    impl = BLOB
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value

class Customer(Base):
    __tablename__ = "customers"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Indexes
    __table_args__ = (
        Index('idx_customer_email_lower', email), # SQLite is case-insensitive by default for ASCII, but good to be explicit or handle logic
    )

    def __repr__(self):
        return f"<Customer(id={self.id}, full_name='{self.full_name}', email='{self.email}')>"
