# TalentRank API

TalentRank API is a production-ready, headless backend service for automated resume screening. It uses advanced RAG (Retrieval-Augmented Generation) and LangGraph to sequentially score and analyze Candidate PDFs against a given Job Description.

## 🏗️ Architecture

This is a **Headless API**. There is no web UI. It is designed to be integrated into larger HR systems or triggered via CI/CD pipelines and command-line interfaces.

- **Framework**: `FastAPI` + `Uvicorn`
- **Database**: `SQLAlchemy` + `SQLite` (Persists Jobs and Candidates)
- **AI Orchestration**: `LangGraph` + `LangChain`
- **Vector Search**: `FAISS` + `HuggingFaceEmbeddings` (Local CPU embeddings)
- **Inference Server**: `vLLM` running locally (OpenAI-compatible endpoints over Llama-3.2-3B-Instruct)
- **Concurrency**: Fast asynchronous file handling via `BackgroundTasks`

## 🚀 Getting Started (Docker)

The fastest and most robust way to run TalentRank in production is using Docker Compose. This spins up the FastAPI application alongside the blazing-fast vLLM inference engine mapping to your GPU.

1. Create a `.env` file in the project root containing your Hugging Face token (required by `vLLM` to pull the Llama 3.2 weights):
   ```bash
   echo "HF_TOKEN=hf_your_token_here" > .env
   ```
2. Start the services:
   ```bash
   docker-compose up --build -d
   ```
   *Note: The vLLM service requires an NVIDIA GPU and Docker configured with the NVIDIA Container Toolkit.*

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
*For manual development without Docker, ensure you run `pip install -r requirements.txt` and have a local vLLM or OpenAI-compatible server running on port `8001`, then run `uvicorn main:app`.*
