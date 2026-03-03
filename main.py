import os
import json
from typing import TypedDict, List, Dict, Any
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import HTMLResponse
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

app = FastAPI(title="TalentRank AI")

# --- LangGraph Setup ---

class GraphState(TypedDict):
    resume_path: str
    jd_text: str
    extracted_text: str
    chunks: List[Document]
    retrieved_context: str
    assessment_json: str
    final_report: Dict[str, Any]

def extract_node(state: GraphState) -> Dict:
    path = state.get("resume_path", "")
    if path and os.path.exists(path):
        try:
            loader = PyPDFLoader(path)
            docs = loader.load()
            text = "\n".join([doc.page_content for doc in docs])
        except Exception as e:
            text = f"Error extracting PDF: {str(e)}"
    else:
        text = "Mock setup for extraction."
    return {"extracted_text": text}

def embed_node(state: GraphState) -> Dict:
    text = state.get("extracted_text", "")
    chunk_size = 1000
    chunks = [Document(page_content=text[i:i+chunk_size]) for i in range(0, len(text), chunk_size)]
    if not chunks:
        chunks = [Document(page_content="Empty resume")]
    return {"chunks": chunks}

def rag_node(state: GraphState) -> Dict:
    chunks = state.get("chunks", [])
    jd = state.get("jd_text", "")
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    # Fetch top 3 most relevant chunks
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    retrieved_docs = retriever.invoke(jd)
    context = "\n".join([doc.page_content for doc in retrieved_docs])
    return {"retrieved_context": context}

def grade_node(state: GraphState) -> Dict:
    context = state.get("retrieved_context", "")
    jd = state.get("jd_text", "")
    
    # Using llama3.2 (~3B) instead of phi3 as requested
    llm = ChatOllama(model="llama3.2", temperature=0)
    
    prompt = f"""
    You are an expert technical recruiter matching a candidate to a job description.
    
    Job Description:
    {jd}
    
    Candidate Resume Context:
    {context}
    
    Assess the candidate and return strictly a JSON object with this exact structure:
    {{
        "score": <0-100 integer>,
        "strengths": ["list", "of", "strengths"],
        "gaps": ["list", "of", "gaps"],
        "questions": ["list", "of", "suggested", "interview", "questions"]
    }}
    Do not include any text outside the JSON block.
    """
    
    response = llm.invoke(prompt)
    return {"assessment_json": response.content}

def report_node(state: GraphState) -> Dict:
    raw_json = state.get("assessment_json", "")
    try:
        start = raw_json.find('{')
        end = raw_json.rfind('}') + 1
        clean_json = raw_json[start:end]
        report = json.loads(clean_json)
    except Exception:
        report = {
            "score": 0,
            "strengths": ["Error parsing output"],
            "gaps": [],
            "questions": []
        }
    return {"final_report": report}

workflow = StateGraph(GraphState)
workflow.add_node("extract", extract_node)
workflow.add_node("embed", embed_node)
workflow.add_node("rag", rag_node)
workflow.add_node("grade", grade_node)
workflow.add_node("report", report_node)

workflow.add_edge(START, "extract")
workflow.add_edge("extract", "embed")
workflow.add_edge("embed", "rag")
workflow.add_edge("rag", "grade")
workflow.add_edge("grade", "report")
workflow.add_edge("report", END)

app_graph = workflow.compile()


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return "<h1>TalentRank AI - Processing Nodes Initialized</h1>"
