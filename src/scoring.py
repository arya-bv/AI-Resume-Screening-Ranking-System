import os
import json
import logging
from google import genai
from google.genai import types
from .models import ResumeEvaluation

logger = logging.getLogger(__name__)

# The client automatically picks up the GEMINI_API_KEY environment variable
client = genai.Client()

def score_candidate(resume_text: str) -> dict:
    """Scores an eligible candidate using Gemini with Structured Outputs."""
    
    prompt = f"""
    You are an expert engineering manager screening a resume. 
    Analyze the text and extract the candidate's details.
    
    Scoring Rules:
    1. AI / Agentic Depth (Max 40): Deduct 5-15 points if the AI project is just a thin wrapper around an LLM API call with no real backend logic, data processing, or orchestration.
    2. Python & Backend (Max 30): Reward evidence in projects over keyword-only skill lists.
    3. Cloud / Full Stack (Max 15): GCP, Docker, deployment, React.
    4. Engineering Depth (Max 5): Testing, architecture, caching, failure handling.
    
    Resume Text:
    {resume_text}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ResumeEvaluation,
                temperature=0.1, # Low temperature for consistent grading
            ),
        )
        # Parse the structured JSON response back into a dictionary
        evaluation_data = json.loads(response.text)
        return evaluation_data
        
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        # The system must not crash if one model call fails
        return None

import re
import httpx
import os

def extract_github_username(resume_text: str) -> str | None:
    """Extracts a GitHub username from the resume text."""
    match = re.search(r'github\.com/([a-zA-Z0-9-]+)', resume_text.lower())
    return match.group(1) if match else None

async def enrich_github_profile(username: str) -> dict:
    """
    Fetches basic GitHub stats to award up to 10 bonus points.
    If the API fails or rate limits, it returns 0 points safely.
    """
    if not username:
        return {"score": 0, "summary": "No GitHub profile found in resume."}

    # Use token if available to prevent aggressive rate limiting[cite: 1]
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/users/{username}", 
                headers=headers, 
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                public_repos = data.get("public_repos", 0)
                
                # Simple explainable scoring method: up to 5 points for having repos, 
                # and up to 5 points for the volume of public repos.
                repo_score = min(5, public_repos)
                activity_score = 5 if public_repos > 0 else 0
                total_github_score = repo_score + activity_score
                
                return {
                    "score": total_github_score, 
                    "summary": f"Profile active; {public_repos} public repos found."
                }
            else:
                return {"score": 0, "summary": "GitHub profile private or API rate limited."}
                
    except Exception as e:
        logger.warning(f"GitHub API call failed for {username}: {e}")
        # Return 0 safely without failing the batch[cite: 1]
        return {"score": 0, "summary": "GitHub enrichment connection failed."}
