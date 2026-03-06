import os
import shutil
import tempfile
import json
from typing import List
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import engine, Base, SessionLocal
from models import Job, Candidate
from graph import app_graph

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TalentRank API", description="Headless AI Resume Screening API")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class JobCreate(BaseModel):
    jd_text: str

def process_resume_task(candidate_id: str, resume_path: str, jd_text: str):
    db: Session = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return

        initial_state = {
            "resume_path": resume_path,
            "jd_text": jd_text
        }
        res = app_graph.invoke(initial_state)
        report = res.get("final_report", {})

        candidate.score = report.get("score", 0)
        candidate.strengths = json.dumps(report.get("strengths", []))
        candidate.gaps = json.dumps(report.get("gaps", []))
        candidate.questions = json.dumps(report.get("questions", []))
        candidate.status = "completed"

        db.commit()
    except Exception as e:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if candidate:
            candidate.status = "failed"
            candidate.strengths = json.dumps([f"Error: {str(e)}"])
            db.commit()
    finally:
        if os.path.exists(resume_path):
            os.remove(resume_path)
        db.close()

@app.post("/jobs")
def create_job(job_data: JobCreate, db: Session = Depends(get_db)):
    db_job = Job(jd_text=job_data.jd_text)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return {"job_id": db_job.id, "message": "Job created successfully."}

@app.post("/jobs/{job_id}/resumes")
def upload_resumes(job_id: str, background_tasks: BackgroundTasks, resumes: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    processing_ids = []
    
    for resume in resumes:
        db_candidate = Candidate(
            job_id=job.id,
            filename=resume.filename,
            status="processing"
        )
        db.add(db_candidate)
        db.commit()
        db.refresh(db_candidate)
        processing_ids.append(db_candidate.id)

        # Save file to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(resume.file, tmp)
            tmp_path = tmp.name

        background_tasks.add_task(process_resume_task, db_candidate.id, tmp_path, job.jd_text)

    return {"message": f"{len(resumes)} resumes uploaded and processing started.", "candidate_ids": processing_ids}

@app.get("/jobs/{job_id}")
def get_job_results(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = db.query(Candidate).filter(Candidate.job_id == job_id).order_by(Candidate.score.desc()).all()
    
    results = []
    for c in candidates:
        results.append({
            "id": c.id,
            "filename": c.filename,
            "status": c.status,
            "score": c.score,
            "strengths": json.loads(c.strengths) if c.strengths else [],
            "gaps": json.loads(c.gaps) if c.gaps else [],
            "questions": json.loads(c.questions) if c.questions else []
        })

    return {
        "job_id": job.id,
        "jd_text": job.jd_text,
        "candidates": results
    }
