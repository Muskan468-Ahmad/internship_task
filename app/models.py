import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.db import Base

# --------- NEW ----------
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(String, unique=True, nullable=False)  # e.g., username/email
    created_at = Column(DateTime, default=datetime.utcnow)

class AdminSettings(Base):
    __tablename__ = "admin_settings"
    id = Column(Integer, primary_key=True, default=1)
    gpt_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
# ------------------------

class QAPair(Base):
    __tablename__ = "qa_pairs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    final_answer = Column(Text, nullable=True)  # can be null if pending for admin
    matched = Column(Boolean, nullable=False, default=False)
    similarity = Column(Float, nullable=True)
    # --------- NEW ----------
    status = Column(String, nullable=False, default="answered")  # "answered" | "pending"
    is_image = Column(Boolean, nullable=False, default=False)
    # ------------------------
    created_at = Column(DateTime, default=datetime.utcnow)
