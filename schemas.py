from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from models import UserRole

# Auth Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Organization Schemas
class OrgCreate(BaseModel):
    org_name: str

class OrgResponse(BaseModel):
    org_id: int

class OrgMemberInvite(BaseModel):
    email: EmailStr
    role: UserRole

# Item Schemas
class ItemCreate(BaseModel):
    item_details: Dict[str, Any]
    org_id: int

class ItemResponse(BaseModel):
    item_id: int

class ItemDetail(BaseModel):
    id: int
    item_details: Dict[str, Any]
    org_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# User & Membership Schemas
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    action: str
    details: str
    org_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChatbotRequest(BaseModel):
    question: str
    stream: bool = True
