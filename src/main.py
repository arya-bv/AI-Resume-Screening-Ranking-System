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
