import os
from typing import List
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="AI Resume Screening API")

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the single-file React/Tailwind frontend."""
    # Ensure the templates directory exists relative to this file
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    try:
        with open(template_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Dashboard UI not found. Please create src/templates/index.html</h1>", 
            status_code=404
        )

@app.post("/screen")
async def screen_resumes(files: List[UploadFile] = File(...)):
    """Receives PDFs, saves them temporarily, and triggers the pipeline."""
    
    # --- Phase 2 Placeholder ---
    # 1. Save files to a temporary directory
    # 2. Extract text using PyPDF2
    # 3. Run Hard Eligibility Filter
    # 4. Run Gemini LLM Scoring + GitHub Enrichment
    # 5. Clean up temporary files
    
    file_names = [file.filename for file in files]
    
    # Returning a mock response for now to verify the endpoint works
    return {
        "message": f"Successfully received {len(files)} files.",
        "files_received": file_names,
        "status": "Pipeline not yet implemented."
    }

if __name__ == "__main__":
    # Runs the server locally. Render will use the command: uvicorn src.main:app --host 0.0.0.0 --port $PORT
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

import os
from typing import List
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import uvicorn

from src.parser import extract_text_from_pdf
from src.eligibility import check_eligibility
from src.scoring import score_candidate, extract_github_username, enrich_github_profile

app = FastAPI(title="AI Resume Screening API")

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the single-file React/Tailwind frontend."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    try:
        with open(template_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Dashboard UI not found. Please create src/templates/index.html</h1>", 
            status_code=404
        )

@app.post("/screen")
async def screen_resumes(files: List[UploadFile] = File(...)):
    """Receives PDFs, processes them in memory, and returns the ranked batch."""
    
    results = {
        "batch_summary": {
            "total_resumes": len(files),
            "successfully_parsed": 0,
            "eligible": 0,
            "rejected": 0,
            "failed_unreadable": 0
        },
        "eligible_candidates": [],
        "rejected_candidates": []
    }

    for file in files:
        candidate_filename = file.filename
        
        # 1. Ingestion & Extraction (In-memory to save disk I/O)
        file_bytes = await file.read()
        text = extract_text_from_pdf(file_bytes)
        
        if not text:
            results["batch_summary"]["failed_unreadable"] += 1
            continue
            
        results["batch_summary"]["successfully_parsed"] += 1

        # 2. Hard Eligibility Filter
        is_eligible, rejection_reasons = check_eligibility(text)
        
        if not is_eligible:
            results["batch_summary"]["rejected"] += 1
            results["rejected_candidates"].append({
                "candidate": candidate_filename,
                "eligible": False,
                "rejection_reasons": rejection_reasons
            })
            continue

        results["batch_summary"]["eligible"] += 1

        # 3. LLM Scoring
        evaluation = score_candidate(text)
        if not evaluation:
            # If LLM fails, skip this candidate safely without crashing the batch[cite: 1]
            results["batch_summary"]["failed_unreadable"] += 1
            results["batch_summary"]["eligible"] -= 1 
            continue

        # 4. GitHub Enrichment
        github_username = extract_github_username(text)
        github_data = await enrich_github_profile(github_username)

        # 5. Calculate Final Score
        breakdown = evaluation.get("score_breakdown", {})
        base_score = (
            breakdown.get("ai_project_depth", 0) +
            breakdown.get("python_backend", 0) +
            breakdown.get("cloud_fullstack", 0) +
            breakdown.get("engineering_depth", 0)
        )
        total_score = base_score + github_data["score"]

        # Store the GitHub score explicitly in the breakdown
        breakdown["github"] = github_data["score"]

        candidate_data = {
            "candidate_name": evaluation.get("candidate_name", candidate_filename),
            "eligible": True,
            "total_score": total_score,
            "score_breakdown": breakdown,
            "matched_skills": evaluation.get("matched_skills", []),
            "project_summary": evaluation.get("project_summary", ""),
            "github_summary": github_data["summary"],
            "strengths": evaluation.get("strengths", []),
            "concerns": evaluation.get("concerns", [])
        }
        results["eligible_candidates"].append(candidate_data)

    # 6. Rank Eligible Candidates (Highest score first)[cite: 1]
    results["eligible_candidates"].sort(key=lambda x: x["total_score"], reverse=True)
    for rank, candidate in enumerate(results["eligible_candidates"], start=1):
        candidate["rank"] = rank

    return results

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
