from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INTAKE = "intake"
    ANALYST = "analyst"
    REPORTER = "reporter"
    VIEWER = "viewer"

class CaseStatus(str, enum.Enum):
    NEW = "new"
    UNDER_ANALYSIS = "under_analysis"
    EVIDENCE_COLLECTED = "evidence_collected"
    REPORT_SUBMITTED = "report_submitted"
    CLOSED = "closed"
    ESCALATED = "escalated"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    hashed_password = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(CaseStatus), default=CaseStatus.NEW, nullable=False)
    priority = Column(String(10), default="medium")  # low, medium, high, critical
    category = Column(String(50))
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(JSON, default=[])
    
    reporter = relationship("User", foreign_keys=[reporter_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])

class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String(20), unique=True, index=True, nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    type = Column(String(20), nullable=False)  # screenshot, video, link, etc.
    file_hash = Column(String(64), nullable=False)  # SHA256
    file_path = Column(Text, nullable=False)
    source_url = Column(Text)
    metadata = Column(JSON, default={})
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    integrity_verified = Column(Boolean, default=False)
    
    case = relationship("Case", backref="evidences")
