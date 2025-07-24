import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from app.db import Base

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
    final_answer = Column(Text, nullable=False)
    matched = Column(Boolean, nullable=False, default=False)
    similarity = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
