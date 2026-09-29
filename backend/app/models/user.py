import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Uuid
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class UserRole(str, enum.Enum):
    MAKER = "MAKER"
    CHECKER = "CHECKER"
    ADMIN = "ADMIN"

class Organisation(Base):
    __tablename__ = "organisations"
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class User(Base):
    __tablename__ = "users"
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(Uuid(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # US-08 2FA Fields
    totp_secret_encrypted = Column(String, nullable=True)
    totp_enabled = Column(Boolean, default=False, nullable=False)
    totp_verified_at = Column(DateTime(timezone=True), nullable=True)

    organisation = relationship("Organisation")