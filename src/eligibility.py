import re
from typing import Tuple, List

# Keywords for fast rule-based filtering
PYTHON_KEYWORDS = [r'\bpython\b', r'\bfastapi\b', r'\bflask\b', r'\bdjango\b', r'\bpandas\b', r'\bnumpy\b']
AI_KEYWORDS = [
    r'\bai\b', r'\bllm\b', r'\brag\b', r'\bagent\b', r'\bagentic\b',
    r'\blangchain\b', r'\blanggraph\b', r'\bllamaindex\b', 
    r'\bopenai\b', r'\bembeddings\b', r'\bvector\b'
]

def check_eligibility(resume_text: str) -> Tuple[bool, List[str]]:
    """
    Scans text for Python and AI keywords.
    Returns (is_eligible, list_of_rejection_reasons).
    """
    text_lower = resume_text.lower()
    
    has_python = any(re.search(kw, text_lower) for kw in PYTHON_KEYWORDS)
    has_ai = any(re.search(kw, text_lower) for kw in AI_KEYWORDS)
    
    reasons = []
    if not has_python:
        reasons.append("No evidence of Python stack")
    if not has_ai:
        reasons.append("No AI/agentic project evidence")
        
    is_eligible = has_python and has_ai
    
    return is_eligible, reasons
