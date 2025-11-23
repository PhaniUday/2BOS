import os
import sys
import io
import traceback
from contextlib import redirect_stdout
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI 

import models
from database import engine, SessionLocal

# --- SETUP ---
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# USE LOCAL OLLAMA (Free Forever)
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama" 
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
class ChatRequest(BaseModel):
    message: str
    project_id: int
    user_id: int = 1

class CodeExecutionRequest(BaseModel):
    code: str

class LoginRequest(BaseModel):
    email: str

class ProficiencyRequest(BaseModel):
    user_id: int
    proficiency: str

# --- AUTH & UTILITY ROUTES ---
@app.post("/login/")
def login(user: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user:
        db_user = models.User(email=user.email, proficiency_level=None)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    return db_user

@app.post("/update-proficiency/")
def update_proficiency(data: ProficiencyRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.proficiency_level = data.proficiency
    db.commit()
    return {"status": "success"}

@app.get("/projects/")
def get_projects(level: Optional[str] = None, db: Session = Depends(get_db)):
    if level: return db.query(models.Project).filter(models.Project.difficulty == level).all()
    return db.query(models.Project).all()

@app.get("/projects/{project_id}")
def get_project_details(project_id: int, db: Session = Depends(get_db)):
    return db.query(models.Project).filter(models.Project.id == project_id).first()

@app.post("/run/")
def run_code(request: CodeExecutionRequest):
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            # Safe-ish execution environment
            exec(request.code, {"__builtins__": __builtins__}, {})
        return {"output": buffer.getvalue() or "Code Executed. (No Output)"}
    except Exception:
        return {"output": traceback.format_exc()}

# --- THE SAFETY NET CHAT ENGINE ---
@app.post("/chat/")
def chat_with_ai(request: ChatRequest, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == request.project_id).first()
    if not project: return {"reply": "Error: Project not found."}

    # 1. Get User Progress
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == request.user_id,
        models.UserProgress.project_id == request.project_id
    ).first()

    if not progress:
        progress = models.UserProgress(user_id=request.user_id, project_id=request.project_id, current_step_order=1)
        db.add(progress)
        db.commit()

    # 2. Get Target Step
    current_step = db.query(models.ProjectStep).filter(
        models.ProjectStep.project_id == request.project_id,
        models.ProjectStep.step_order == progress.current_step_order
    ).first()

    if not current_step:
        return {"reply": "CONGRATULATIONS! You have completed all steps for this project. Feel free to experiment with the code now."}

    print(f"Checking Logic for Step {current_step.step_order}: {current_step.title}")

    # 3. THE JUDGE (Logic Check)
    judge_prompt = f"""
    Role: Strict Code Logic Examiner.
    Current Goal: "{current_step.required_concept}"
    User Message: "{request.message}"
    
    INSTRUCTIONS:
    - Did the user correctly identify the logic/variables/data structure required?
    - If they asked for code, help, or are vague -> FAIL
    - If they explained it correctly -> PASS
    
    OUTPUT ONLY: PASS or FAIL
    """

    try:
        judge_res = client.chat.completions.create(
            model="qwen2.5-coder:3b", 
            messages=[{"role": "system", "content": judge_prompt}],
            temperature=0.0, max_tokens=5
        )
        verdict = judge_res.choices[0].message.content.strip().upper()
        print(f"Verdict: {verdict}")
    except: verdict = "FAIL"

    # 4. RESPONSE LOGIC
    if "PASS" in verdict:
        # --- SUCCESS: UNLOCK CODE FROM DB ---
        code_reward = current_step.unlock_code
        progress.current_step_order += 1
        db.commit()
        
        next_step = db.query(models.ProjectStep).filter(
            models.ProjectStep.project_id == request.project_id,
            models.ProjectStep.step_order == progress.current_step_order
        ).first()
        
        next_prompt = f"Next Step: {next_step.title}. {next_step.required_concept}" if next_step else "Project Complete!"

        return {"reply": f"**Correct!**\n\nHere is the implementation:\n```python\n{code_reward}\n```\n\n{next_prompt}"}

    else:
        # --- FAILURE: TUTOR MODE + PYTHON SAFETY NET ---
        tutor_prompt = f"""
        You are a Socratic Tutor for project: "{project.title}".
        The user is stuck on Step {current_step.step_order}: "{current_step.title}".
        Goal Logic: "{current_step.required_concept}"
        
        INSTRUCTIONS:
        1. Explain the CONCEPT only.
        2. Ask a guiding question about the variables or structure needed.
        3. DO NOT WRITE CODE.
        """
        
        completion = client.chat.completions.create(
            model="qwen2.5-coder:3b", 
            messages=[{"role": "system", "content": tutor_prompt}],
            temperature=0.2, max_tokens=250
        )
        
        ai_reply = completion.choices[0].message.content

        # --- THE SAFETY NET ---
        # If the AI ignores instructions and writes code, we delete it.
        forbidden = ["class ", "def ", "import ", "```"]
        
        if any(bad_word in ai_reply for bad_word in forbidden):
            print("Safety Net Triggered: Code leak prevented.")
            ai_reply = f"I cannot write the code for you yet. Let's think about the logic first.\n\nHint: {current_step.required_concept}"

        return {"reply": ai_reply}