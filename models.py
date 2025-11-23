from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
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
    
    step_order = Column(Integer) # 1, 2, 3...
    title = Column(String) # e.g. "Define the Node"
    required_concept = Column(Text) # "Needs title, artist, next"
    unlock_code = Column(Text) # "class Node: ..."

    project = relationship("Project", back_populates="steps")

# --- NEW TABLE: MEMORY ---
class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # Ideally linked to real user
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    # The step they are currently trying to solve
    current_step_order = Column(Integer, default=1)