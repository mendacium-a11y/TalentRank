from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="TalentRank AI")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return "<h1>TalentRank AI - Hello World</h1>"
