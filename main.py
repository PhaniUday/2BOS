import os
import sys
import io
import traceback
from datetime import datetime, timedelta
from contextlib import redirect_stdout
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI 
from passlib.context import CryptContext # Security
from jose import JWTError, jwt # Tokens
import re

import models
from database import engine, SessionLocal

# --- SETUP ---
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SECURITY CONFIG ---
SECRET_KEY = "YOUR_SUPER_SECRET_KEY_HERE" # In prod, use .env
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- DATA MODELS ---
class AuthRequest(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    message: str
    project_id: int
    user_id: int

class CodeExecutionRequest(BaseModel):
    code: str

class ProficiencyRequest(BaseModel):
    user_id: int
    proficiency: str

class InitProjectRequest(BaseModel):
    user_id: int
    project_id: int

# --- AUTH ROUTES ---

@app.post("/register/")
def register(user: AuthRequest, db: Session = Depends(get_db)):
    # 1. Check if email exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Hash Password & Save
    hashed_pw = get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pw, proficiency_level=None)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"id": new_user.id, "email": new_user.email, "proficiency_level": None}

@app.post("/login/")
def login(user: AuthRequest, db: Session = Depends(get_db)):
    # 1. Find User
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid Credentials")
    
    # 2. Verify Password
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid Password")
    
    return {"id": db_user.id, "email": db_user.email, "proficiency_level": db_user.proficiency_level}

@app.post("/update-proficiency/")
def update_proficiency(data: ProficiencyRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.proficiency_level = data.proficiency
    db.commit()
    return {"status": "success"}

# --- PROJECT ROUTES ---
@app.post("/projects/initialize")
def initialize_project(req: InitProjectRequest, db: Session = Depends(get_db)):
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == req.user_id,
        models.UserProgress.project_id == req.project_id
    ).first()
    
    if not progress:
        progress = models.UserProgress(user_id=req.user_id, project_id=req.project_id, current_step_order=1)
        db.add(progress)
        db.commit()
        return {"status": "Started"}
    return {"status": "Resumed"}

@app.get("/user/{user_id}/dashboard")
def get_user_dashboard(user_id: int, db: Session = Depends(get_db)):
    all_projects = db.query(models.Project).all()
    total_possible_steps = sum([len(p.steps) for p in all_projects]) if all_projects else 1
    
    ongoing = db.query(models.UserProgress).filter(models.UserProgress.user_id == user_id).all()
    
    total_completed_steps = sum([p.current_step_order - 1 for p in ongoing])
    global_percentage = int((total_completed_steps / total_possible_steps) * 100) if total_possible_steps > 0 else 0

    dashboard_data = []
    project_map = {p.id: p for p in all_projects}

    for entry in ongoing:
        proj = project_map.get(entry.project_id)
        if not proj: continue
        
        total_steps = len(proj.steps)
        current = entry.current_step_order
        percent = int(((current - 1) / total_steps) * 100)
        percent = min(100, max(0, percent))

        dashboard_data.append({
            "id": proj.id,
            "title": proj.title,
            "difficulty": proj.difficulty,
            "description": proj.description,
            "current_step": current,
            "total_steps": total_steps,
            "percent": percent
        })
        
    return {"global_progress": global_percentage, "projects": dashboard_data}

@app.get("/projects/")
def get_projects(level: Optional[str] = None, db: Session = Depends(get_db)):
    if level:
        return db.query(models.Project).filter(models.Project.difficulty == level).all()
    return db.query(models.Project).all()

@app.get("/projects/{project_id}")
def get_project_details(project_id: int, db: Session = Depends(get_db)):
    return db.query(models.Project).filter(models.Project.id == project_id).first()

# --- EXECUTION & CHAT (Unchanged Logic, just cleaner) ---
@app.post("/run/")
def run_code(request: CodeExecutionRequest):
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(request.code, {"__builtins__": __builtins__}, {})
        return {"output": buffer.getvalue() or "Code Executed."}
    except Exception:
        return {"output": traceback.format_exc()}

@app.post("/chat/")
def chat_with_ai(request: ChatRequest, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == request.project_id).first()
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    
    if not project or not user: return {"reply": "Error: Context missing."}

    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == request.user_id,
        models.UserProgress.project_id == request.project_id
    ).first()

    if not progress:
        progress = models.UserProgress(user_id=request.user_id, project_id=request.project_id, current_step_order=1)
        db.add(progress)
        db.commit()

    current_step = db.query(models.ProjectStep).filter(
        models.ProjectStep.project_id == request.project_id,
        models.ProjectStep.step_order == progress.current_step_order
    ).first()

    if not current_step:
        return {"reply": "CONGRATULATIONS! You have completed all steps. Feel free to experiment."}

    print(f"User Level: {user.proficiency_level} | Step: {current_step.title}")

    # --- JUDGE ---
    judge_prompt = f"""
    Role: Logic Examiner.
    Goal: "{current_step.required_concept}"
    User Input: "{request.message}"
    
    Did the user correctly explain the logic/variables?
    OUTPUT ONLY: PASS or FAIL
    """

    try:
        judge_res = client.chat.completions.create(
            model="qwen2.5-coder:3b", 
            messages=[{"role": "system", "content": judge_prompt}],
            temperature=0.0, max_tokens=5
        )
        verdict = judge_res.choices[0].message.content.strip().upper()
    except: verdict = "FAIL"

    if "PASS" in verdict:
        # SUCCESS
        code_reward = current_step.unlock_code
        progress.current_step_order += 1
        db.commit()
        
        next_step = db.query(models.ProjectStep).filter(
            models.ProjectStep.project_id == request.project_id,
            models.ProjectStep.step_order == progress.current_step_order
        ).first()
        
        next_text = f"Next Goal: {next_step.title}." if next_step else "Project Complete!"
        return {"reply": f"**Correct!**\n\nHere is the implementation:\n```python\n{code_reward}\n```\n\n{next_text}"}

    else:
        # --- TUTOR MODE (Simplified) ---
        level = user.proficiency_level or "Beginner"
        
        if level == "Beginner":
            persona = "You are a patient teacher. Use analogies."
        elif level == "Advanced":
            persona = "You are a Lead Architect. Be concise and technical."
        else:
            persona = "You are a Senior Developer. Be direct."

        # We give it an EXAMPLE of a good response to follow
        tutor_prompt = f"""
        {persona}
        Context: Project "{project.title}".
        Goal: Help user with "{current_step.required_concept}" without giving code.
        
        User: "{request.message}"
        
        Your Response Guidelines:
        1. Explain the concept briefly.
        2. Ask a specific question to guide them.
        3. NO headers. NO meta-talk.
        """
        
        completion = client.chat.completions.create(
            model="qwen2.5-coder:3b", 
            messages=[{"role": "system", "content": tutor_prompt}],
            temperature=0.3, max_tokens=350
        )
        
        ai_reply = completion.choices[0].message.content

        # --- THE SANITIZER (Python Cleaning) ---
        # 1. Block Code Leaks
        forbidden = ["class ", "def ", "import ", "```"]
        if any(bad_word in ai_reply for bad_word in forbidden):
            ai_reply = f"I cannot write the code yet. Let's focus on the logic.\n\nHint: {current_step.required_concept}"

        # 2. Strip Leaked Headers (Regex)
        # Removes lines like "Concept Explanation:", "User Input:", etc.
        ai_reply = re.sub(r'^(Concept Explanation|User Input|Current Step|INSTRUCTIONS|Question):?\s*', '', ai_reply, flags=re.MULTILINE | re.IGNORECASE)
        
        return {"reply": ai_reply.strip()}