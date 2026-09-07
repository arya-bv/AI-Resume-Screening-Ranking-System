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
