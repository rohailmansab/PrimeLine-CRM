from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

from enum import Enum

class CustomerType(str, Enum):
    CONTRACTOR = "contractor"
    ARCHITECT = "architect"
    INSTALLER = "installer"
    DIY = "diy"

class InteractionStatus(str, Enum):
    CALLED = "called"
    EMAILED = "emailed"
    SPOKE = "spoke"

class CustomerInteractionBase(BaseModel):
    status: InteractionStatus
    notes: Optional[str] = None

class CustomerInteractionCreate(CustomerInteractionBase):
    customer_id: str

class CustomerInteractionRead(CustomerInteractionBase):
    id: int
    user_id: Optional[int]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CustomerBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    business_name: Optional[str] = None
    email: EmailStr
    phone: str = Field(..., min_length=1) # Mandatory
    zip_code: str = Field(..., min_length=1) # Mandatory
    location: Optional[str] = None # Deprecated
    customer_type: CustomerType = CustomerType.CONTRACTOR
    notes: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    business_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    zip_code: Optional[str] = None
    location: Optional[str] = None
    customer_type: Optional[CustomerType] = None
    notes: Optional[str] = None

class CustomerRead(CustomerBase):
    id: UUID
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
