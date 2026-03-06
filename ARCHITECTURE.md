# TalentRank AI - Headless API Architecture

This document provides a detailed breakdown of the **TalentRank AI Headless API**. It explains exactly what happens under the hood when API requests are made, how the AI models are utilized, and how data moves through the system.

---

## 🏗️ 1. The High-Level Stack

TalentRank AI is built on a modern, local-first API stack:
- **Backend Framework**: **FastAPI** (`main.py`) running on the **Uvicorn** ASGI server.
- **Database**: **SQLite** (via **SQLAlchemy**) for state persistence.
- **AI Orchestration**: **LangGraph** (`graph.py`) to structure the AI workflow into discrete "nodes."
- **Embeddings**: HuggingFace's `all-MiniLM-L6-v2` run locally to convert text into mathematical vectors.
- **Vector Database**: **FAISS** (Facebook AI Similarity Search) to store and retrieve those vectors efficiently.
- **Large Language Model (LLM)**: **Llama 3.2 3B** (hosted locally via **vLLM** for production-grade throughput) acting as the judge.

---

## 🌊 2. The Complete Data Flow: Step-by-Step

Here is exactly what happens during an asynchronous batch processing job:

### Step 1: Job Creation (`POST /jobs`)
1. The client sends a `POST` request containing the textual Job Description.
2. `main.py` uses SQLAlchemy to create a new `Job` record in the SQLite database.
3. The API immediately returns a unique `job_id`.

### Step 2: Uploading Resumes (`POST /jobs/{job_id}/resumes`)
1. The client uploads multiple PDF resumes via `multipart/form-data`.
2. `main.py` verifies the `job_id` exists in the database.
3. For every uploaded PDF, it creates a `Candidate` record linked to the `Job` with a status of `"processing"`.
4. The PDF files are saved to temporary files on disk.
5. FastAPI delegates the heavy AI inference to a `BackgroundTask` (`process_resume_task`) so the API can return immediately without keeping the HTTP connection open.
6. The client receives a success response instantly.

### Step 3: The LangGraph AI Brain (`graph.py`)
In the background, LangGraph passes the resume through a sequence of functions called "nodes" for each candidate.

#### Node 1: Extract (`extract_node`)
- **What it does**: Reads the physical PDF file.
- **How**: Uses Langchain's `PyPDFLoader` to open the PDF, extract all the raw text from every page, and join it into one giant string.

#### Node 2: Embed (`embed_node`)
- **What it does**: Breaks the giant string into smaller, digestible chunks (1000 characters each).

#### Node 3: RAG - Retrieve (`rag_node`)
- **What it does**: Finds the most relevant parts of the resume for the specific Job Description.
- **How**: It converts chunks into vectors, stores them in FAISS, embeds the Job Description, and retrieves the top 3 semantic matches.

#### Node 4: Grade (`grade_node`)
- **What it does**: The actual "AI" thinking phase.
- **How**: It connects to the local **vLLM** container using an OpenAI-compatible interface. It prompts `Llama-3.2-3B-Instruct` with the context and demands a strictly formatted JSON output grading the candidate.

#### Node 5: Report (`report_node`)
- **What it does**: Cleans up the AI's response to ensure it can be parsed as valid JSON.

### Step 4: Finalizing & Polling (`GET /jobs/{job_id}`)
1. Once LangGraph completes, the background task updates the `Candidate` SQLite record with the final `score`, `strengths`, `gaps`, and changes the status to `"completed"`.
2. Because this is a headless API, the client fetches the results by polling `GET /jobs/{job_id}` to see the current rankings of all completed candidates.

---

## 🛠️ 3. Modularity and Scale

The reason this project relies on **LangGraph** and **vLLM** is for enterprise scalability:
- **Asynchronous Processing**: Using `BackgroundTasks` ensures the API never times out, even if 100 resumes are uploaded at once.
- **vLLM**: Serving the model through vLLM bypasses the inefficiencies of single-stream runners by enabling Continuous Batching and PagedAttention, significantly maximizing GPU utilization for concurrent inferences.
- **Graph Routing**: Because the architecture uses distinct nodes, complex conditional logic can be easily added to the pipeline in the future.
