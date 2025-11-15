from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserOut(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    class Config: from_attributes = True

class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None