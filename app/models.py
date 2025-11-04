import secrets

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
from app.db.database import Base
from sqlalchemy import JSON

user_role = Table(
    'user_role', Base.metadata,
    Column('user_id', ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True)
)

role_permission = Table(
    'role_permission', Base.metadata,
    Column('role_id', ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True),
    Column('permission_id', ForeignKey('permissions.id', ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    middle_name = Column(String)
    password_hash = Column(String)
    is_active = Column(Boolean, default=True)

    roles = relationship("Role", secondary=user_role, backref="users")
    refresh_tokens = relationship("RefreshToken", backref="user")

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)


    permissions = relationship("Permission", secondary=role_permission, backref="roles")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)




