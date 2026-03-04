# TalentRank AI

TalentRank AI is a local, privacy-first dual-mode resume screening application. It uses advanced RAG (Retrieval-Augmented Generation) and Large Language Models (LLMs) to automatically assess candidates against job descriptions.

## Overview

This project provides two distinct modes for interacting with the screening process, all hosted locally on your machine without relying on external APIs:
1. **Candidate Mode**: An interface for a single individual to upload their resume and a Job Description to receive instantaneous feedback on their fit, strengths, skill gaps, and potential interview questions.
2. **HR Batch Mode**: A power-user mode for recruiters to drag and drop up to 50 resumes (PDFs or ZIPs) simultaneously, run them against a single Job Description, and view the results in a sortable matrix ranking table, which can then be exported as a CSV.

## Project Architecture & Files

The project is structured entirely around local resources to ensure maximum privacy and offline capability.

*   `main.py`: This is the core FastAPI application server.
    *   It defines our two main endpoints (`/candidate` and `/hr-batch`).
    *   It handles saving uploaded PDF files to temporary locations.
    *   It serves the main web interface UI to the browser.
    *   For the HR batch processor, it manages Server-Sent Events (SSE) to stream live progress bar updates back to the browser while the AI works sequentially.
*   `graph.py`: This is the "Brain" of the application, utilizing LangChain and LangGraph for processing. It defines a workflow pipeline with the following steps:
    1.  **Extract**: Uses `unstructured` to parse plain text out of uploaded PDF resumes.
    2.  **Embed**: Chunks the extracted text and generates embeddings using the local `sentence-transformers/all-MiniLM-L6-v2` model.
    3.  **RAG (Retrieve)**: Creates a FAISS vector database to retrieve the top 3 most relevant chunks of the candidate's resume based on the provided Job Description context.
    4.  **Grade**: Sends the Job Description and the relevant resume context to a local `llama3.2` model (via Ollama) and prompts it to generate a highly structured JSON assessment.
    5.  **Report**: Cleans and validates the JSON output before passing it back to `main.py` for delivery to the front end.
*   `index.html`: The complete front-end user interface, built purely with vanilla HTML, CSS, and JavaScript. 
    *   Contains the styling for both Light and Dark mode themes.
    *   Houses the logic for tab switching, drag-and-drop file inputs, and submitting form data to the backend endpoints.
    *   Handles reading the SSE stream from the FastAPI server to dynamically update the HR batch progress bar.
    *   Contains the client-side JavaScript for the sortable interactive ranking table and CSV data export.
*   `requirements.txt`: Contains all the necessary Python pip dependencies needed to run the ecosystem.

## Setup & Running

1. **Install requirements**: 
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the local LLM**: 
   Ensure you have [Ollama](https://ollama.com/) installed on your machine and run:
   ```bash
   ollama pull llama3.2
   ```
3. **Run backend server**: 
   ```bash
   uvicorn main:app --reload
   ```
    - *Note: Uvicorn is a lightning-fast ASGI web server implementation for Python. It is used here to run our FastAPI application and handle the incoming HTTP web requests from your browser.*

4. **Access the Application**:
   Open your browser and navigate to `http://localhost:8000`.
