import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    jd_text = Column(String, nullable=False)
    
    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"))
    filename = Column(String, index=True)
    status = Column(String, default="processing") # processing, completed, failed
    score = Column(Integer, nullable=True)
    strengths = Column(String, nullable=True) # Stored as JSON string
    gaps = Column(String, nullable=True) # Stored as JSON string
    questions = Column(String, nullable=True) # Stored as JSON string
    
    job = relationship("Job", back_populates="candidates")
