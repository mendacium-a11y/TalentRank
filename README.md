# TalentRank API

TalentRank API is a production-ready, headless backend service for automated resume screening. It uses advanced RAG (Retrieval-Augmented Generation) and LangGraph to sequentially score and analyze Candidate PDFs against a given Job Description.

## 🏗️ Architecture

This is a **Headless API**. There is no web UI. It is designed to be integrated into larger HR systems or triggered via CI/CD pipelines and command-line interfaces.

- **Framework**: `FastAPI` + `Uvicorn`
- **Database**: `SQLAlchemy` + `SQLite` (Persists Jobs and Candidates)
- **AI Orchestration**: `LangGraph` + `LangChain`
- **Vector Search**: `FAISS` + `HuggingFaceEmbeddings` (Local CPU embeddings)
- **Inference Server**: `Ollama` running locally (`llama3.2` model)
- **Concurrency**: Fast asynchronous file handling via `BackgroundTasks`

## 🚀 Getting Started

You can run TalentRank either using Docker Compose (recommended for production-like environments) or locally directly from your system.

### Option A: Using Docker Compose
The fastest and most robust way to run TalentRank is using Docker Compose. This spins up the FastAPI application alongside an Ollama inference container.

1. Start the services:
   ```bash
   docker compose up --build -d
   ```
   *Note: The Ollama container is configured to automatically pull the `llama3.2` model on native startup and will attempt to utilize your NVIDIA GPU if the container toolkit is installed.*

### Option B: Local Setup (Without Docker)
If you prefer to run the API and AI inference locally on your own machine:

1. **Install Dependencies:**
   Ensure you have Python 3.10+ installed.
   ```bash
   pip install -r requirements.txt
   ```
2. **Start Local Ollama:**
   Ensure [Ollama](https://ollama.com/) is installed on your system.
   ```bash
   ollama serve &
   ```
   Pull the Llama 3.2 model if you haven't already:
   ```bash
   ollama pull llama3.2
   ```
3. **Run the FastAPI Server:**
   Start the application locally on your machine.
   ```bash
   uvicorn main:app --reload
   ```

## 💻 API Usage (CLI Examples)

You can interact with the API entirely through `curl`. 

### 1. Create a Job
Send the Job Description to create a new processing batch and receive a `job_id`.

```bash
curl -X POST "http://localhost:8000/jobs" \
     -H "Content-Type: application/json" \
     -d '{"jd_text": "We are looking for a Senior Software Engineer with strong Python, FastAPI, and Docker experience..."}'
```
**Response:**
```json
{
  "job_id": "c1a938...af2e",
  "message": "Job created successfully."
}
```

### 2. Upload Resumes (Asynchronous)
Upload multiple `pdf` files to the Job ID. The backend will immediately return a success message while the AI begins scoring them in the background.

```bash
curl -X POST "http://localhost:8000/jobs/c1a938...af2e/resumes" \
     -F "resumes=@/path/to/Alice_Resume.pdf" \
     -F "resumes=@/path/to/Bob_Resume.pdf"
```

### 3. Check Results/Status
Fetch the job by its ID to see the rankings. Candidates will show `"status": "processing"` until they finish, at which point they will display their `"score"`, `"strengths"`, and `"gaps"`.

```bash
curl -X GET "http://localhost:8000/jobs/c1a938...af2e"
```
**Response:**
```json
{
  "job_id": "c1a938...af2e",
  "jd_text": "We are looking for...",
  "candidates": [
    {
      "id": "7b2d...",
      "filename": "Alice_Resume.pdf",
      "status": "completed",
      "score": 95,
      "strengths": ["Strong Python", "FastAPI Expert"],
      "gaps": [],
      "questions": ["Can you describe a complex system you built with Docker?"]
    },
    {
      "id": "2e4f...",
      "filename": "Bob_Resume.pdf",
      "status": "processing",
      "score": 0,
      "strengths": [],
      "gaps": [],
      "questions": []
    }
  ]
}
```

---
*For manual development without Docker, follow Option B in the Getting Started section.*
