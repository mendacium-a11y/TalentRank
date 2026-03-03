import os
import shutil
import tempfile
import asyncio
from typing import List
from fastapi import FastAPI, UploadFile, Form, File, Request
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
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
async def process_hr_batch(request: Request, resumes: List[UploadFile] = File(...), jd: str = Form(...)):
    async def event_stream():
        total = len(resumes)
        results = []
        for index, resume in enumerate(resumes):
            if await request.is_disconnected():
                break

            # Send progress update
            progress_data = json.dumps({"type": "progress", "current": index + 1, "total": total, "filename": resume.filename})
            yield f"data: {progress_data}\n\n"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                shutil.copyfileobj(resume.file, tmp)
                tmp_path = tmp.name

            try:
                initial_state = {
                    "resume_path": tmp_path,
                    "jd_text": jd
                }
                # To prevent blocking the async event loop, run invoke in a thread
                res = await asyncio.to_thread(app_graph.invoke, initial_state)
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
            
            # Send the result for the current file
            result_data = json.dumps({"type": "result", "data": results[-1]})
            yield f"data: {result_data}\n\n"
            
        # Send complete event
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("index.html")
