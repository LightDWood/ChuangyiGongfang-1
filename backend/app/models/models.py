from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="session", cascade="all, delete-orphan")
    conversation_messages = relationship("ConversationMessage", back_populates="session", cascade="all, delete-orphan")
    decision_records = relationship("DecisionRecord", back_populates="session", cascade="all, delete-orphan")
    checkpoints = relationship("Checkpoint", back_populates="session", cascade="all, delete-orphan")
    requirement_spec_versions = relationship("RequirementSpecVersion", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    artifact_type = Column(String, nullable=False)
    current_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("Session", back_populates="artifacts")
    versions = relationship("ArtifactVersion", back_populates="artifact", cascade="all, delete-orphan")


class ArtifactVersion(Base):
    __tablename__ = "artifact_versions"

    id = Column(String, primary_key=True)
    artifact_id = Column(String, ForeignKey("artifacts.id"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    artifact = relationship("Artifact", back_populates="versions")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="conversation_messages")


class DecisionRecord(Base):
    __tablename__ = "decision_records"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    agent = Column(String, nullable=False)
    decision = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="decision_records")


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    state = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="checkpoints")


class RequirementSpecVersion(Base):
    __tablename__ = "requirement_spec_versions"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="requirement_spec_versions")
