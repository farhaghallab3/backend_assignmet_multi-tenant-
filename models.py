import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Integer, ForeignKey, DateTime, JSON, 
    Index, func, Enum, Column, Table, Text, Computed
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Full-text search vector for name/email
    search_vector: Mapped[TSVECTOR] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', coalesce(full_name, '') || ' ' || coalesce(email, ''))",
            persisted=True
        )
    )

    memberships: Mapped[List["Membership"]] = relationship(back_populates="user")
    items: Mapped[List["Item"]] = relationship(back_populates="creator")

    __table_args__ = (
        Index("ix_user_search_vector", "search_vector", postgresql_using="gin"),
    )

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    memberships: Mapped[List["Membership"]] = relationship(back_populates="organization")
    items: Mapped[List["Item"]] = relationship(back_populates="organization")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="organization")

class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.MEMBER)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship(back_populates="memberships")
    organization: Mapped["Organization"] = relationship(back_populates="memberships")

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_details: Mapped[dict] = mapped_column(JSONB)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="items")
    creator: Mapped["User"] = relationship(back_populates="items")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(255))
    details: Mapped[str] = mapped_column(Text)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="audit_logs")
