from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, text, func
from typing import List, Annotated
from datetime import timedelta, datetime

from database import get_db, engine, Base
from models import User, Organization, Membership, Item, AuditLog, UserRole
from schemas import (
    UserRegister, UserLogin, Token, UserResponse,
    OrgCreate, OrgResponse, OrgMemberInvite,
    ItemCreate, ItemResponse, ItemDetail,
    AuditLogResponse, ChatbotRequest
)
from auth import (
    get_password_hash, verify_password, create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
)
from rbac import require_admin, require_member_or_admin
from utils import create_audit_log

app = FastAPI(title="Multi-Tenant Organization Manager")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@app.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

from fastapi.security import OAuth2PasswordRequestForm
@app.post("/auth/token", include_in_schema=False)
async def token_swagger(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """Hidden endpoint for Swagger UI's Authorize button"""
    return await login(UserLogin(email=form_data.username, password=form_data.password), db)

@app.post("/organization", response_model=OrgResponse)
async def create_organization(
    org_data: OrgCreate, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org = Organization(name=org_data.org_name)
    db.add(org)
    await db.flush() # Get org id
    
    membership = Membership(
        user_id=current_user.id,
        org_id=org.id,
        role=UserRole.ADMIN
    )
    db.add(membership)
    
    await create_audit_log(
        db, org.id, current_user.id, "CREATE_ORGANIZATION", 
        f"Organization {org_data.org_name} created by {current_user.email}"
    )
    
    await db.commit()
    return {"org_id": org.id}

@app.post("/organization/{id}/user")
async def add_user_to_org(
    id: int,
    invite_data: OrgMemberInvite,
    membership: Membership = Depends(require_admin), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == invite_data.email))
    user_to_add = result.scalar_one_or_none()
    
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Membership).where(
        Membership.user_id == user_to_add.id,
        Membership.org_id == id
    ))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member")
    
    new_membership = Membership(
        user_id=user_to_add.id,
        org_id=id,
        role=invite_data.role
    )
    db.add(new_membership)
    
    await create_audit_log(
        db, id, membership.user_id, "ADD_USER",
        f"User {invite_data.email} added to organization by admin"
    )
    
    await db.commit()
    return {"status": "success"}

@app.get("/organizations/{id}/users", response_model=List[UserResponse])
async def list_org_users(
    id: int,
    limit: int = 20,
    offset: int = 0,
    membership: Membership = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).join(Membership).where(
        Membership.org_id == id
    ).offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/organizations/{id}/users/search", response_model=List[UserResponse])
async def search_org_users(
    id: int,
    q: str,
    membership: Membership = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).join(Membership).where(
        Membership.org_id == id,
        User.search_vector.op("@@")(func.plainto_tsquery("english", q))
    )
    
    result = await db.execute(query)
    return result.scalars().all()

@app.post("/organizations/{id}/item", response_model=ItemResponse)
async def create_item(
    id: int,
    item_data: ItemCreate,
    membership: Membership = Depends(require_member_or_admin),
    db: AsyncSession = Depends(get_db)
):
    if item_data.org_id != id:
         raise HTTPException(status_code=400, detail="Mismatched organization ID")

    item = Item(
        item_details=item_data.item_details,
        org_id=id,
        user_id=membership.user_id
    )
    db.add(item)
    
    await create_audit_log(
        db, id, membership.user_id, "CREATE_ITEM",
        f"Item created by user {membership.user_id}"
    )
    
    await db.commit()
    return {"item_id": item.id}

@app.get("/organizations/{id}/item", response_model=List[ItemDetail])
async def list_items(
    id: int,
    limit: int = 20,
    offset: int = 0,
    membership: Membership = Depends(require_member_or_admin),
    db: AsyncSession = Depends(get_db)
):
    query = select(Item).where(Item.org_id == id)
    
    if membership.role == UserRole.MEMBER:
        query = query.where(Item.user_id == membership.user_id)
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    
    await create_audit_log(
        db, id, membership.user_id, "LIST_ITEMS",
        f"User viewed items (RBAC: {membership.role})"
    )
    
    return result.scalars().all()

@app.get("/organizations/{id}/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    id: int,
    membership: Membership = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditLog).where(AuditLog.org_id == id).order_by(AuditLog.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@app.post("/organizations/{id}/audit-logs/ask")
async def ask_chatbot(
    id: int,
    request: ChatbotRequest,
    membership: Membership = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    from chatbot import get_ai_response
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    query = select(AuditLog).where(
        AuditLog.org_id == id,
        AuditLog.created_at >= today
    )
    result = await db.execute(query)
    logs = result.scalars().all()
    
    log_text = "\n".join([f"{l.created_at}: {l.action} - {l.details}" for l in logs])
    
    return await get_ai_response(request.question, log_text, request.stream)
