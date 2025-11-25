from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String) # <--- NEW: Stores the secure hash
    proficiency_level = Column(String)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    difficulty = Column(String)
    description = Column(Text)
    full_solution_context = Column(Text, default="")
    
    steps = relationship("ProjectStep", back_populates="project")

class ProjectStep(Base):
    __tablename__ = "project_steps"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    step_order = Column(Integer)
    title = Column(String)
    required_concept = Column(Text)
    unlock_code = Column(Text)

    project = relationship("Project", back_populates="steps")

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    current_step_order = Column(Integer, default=1)