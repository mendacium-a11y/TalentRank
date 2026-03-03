import os
import shutil
import tempfile
from typing import List
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import HTMLResponse, FileResponse
from graph import app_graph

app = FastAPI(title="TalentRank AI")

@app.post("/candidate")
async def process_candidate(resume: UploadFile = File(...), jd: str = Form(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(resume.file, tmp)
        tmp_path = tmp.name

    try:
        initial_state = {
            "resume_path": tmp_path,
            "jd_text": jd
        }
        result = app_graph.invoke(initial_state)
        return result["final_report"]
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/hr-batch")
async def process_hr_batch(resumes: List[UploadFile] = File(...), jd: str = Form(...)):
    results = []
    for resume in resumes:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(resume.file, tmp)
            tmp_path = tmp.name

        try:
            initial_state = {
                "resume_path": tmp_path,
                "jd_text": jd
            }
            res = app_graph.invoke(initial_state)
            report = res["final_report"]
            report["filename"] = resume.filename
            results.append(report)
        except Exception as e:
            results.append({
                "filename": resume.filename,
                "score": 0,
                "strengths": [f"Error: {str(e)}"],
                "gaps": [],
                "questions": []
            })
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    return results

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("index.html")
