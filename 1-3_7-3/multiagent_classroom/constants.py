"""
Constants for COPUS Classroom Simulation
"""

from typing import Dict


# API Configuration
DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
DEEPSEEK_MODEL: str = "deepseek-chat"
GOOGLE_MODEL: str = "gemini-1.5-flash"

# Context Window Limits
MAX_CONTEXT_TEACHER: int = 15
MAX_CONTEXT_STUDENT: int = 10

# Simulation Settings
TURNS_PER_SESSION: int = 5  # Number of 2-minute segments
TEMPERATURE: float = 0.7
MAX_TOKENS: int = 500
MAX_RETRIES: int = 3
BRIEF_PAUSE: float = 0.5  # seconds

# File Paths
AGENT_PROMPTS_PATH: str = "data/agent_prompts_vi.json"
SLIDES_DATA_PATH: str = "data/linear_regression_slides.json"
RESULTS_DIR: str = "results"

# COPUS Codes for Instructors
INSTRUCTOR_CODES: Dict[str, str] = {
    "Lec": "Lecturing (presenting content)",
    "RtW": "Real-time writing",
    "FUp": "Follow-up/feedback",
    "PQ": "Posing non-clicker question",
    "CQ": "Asking clicker question",
    "AnQ": "Answering student questions",
    "MG": "Moving & guiding",
    "D/V": "Demo/video",
    "Adm": "Administration",
    "W": "Waiting",
    "O": "Other"
}

# COPUS Codes for Students
STUDENT_CODES: Dict[str, str] = {
    "L": "Listening/taking notes",
    "Ind": "Individual thinking",
    "CG": "Discussing clicker question",
    "WG": "Working in groups",
    "OG": "Other group activity",
    "AnQ": "Answering question",
    "SQ": "Asking question",
    "WC": "Whole class discussion",
    "Prd": "Making prediction",
    "SP": "Student presentation",
    "TQ": "Test/quiz",
    "W": "Waiting",
    "O": "Other"
}

# COPUS Classification Thresholds
DIDACTIC_THRESHOLD: float = 80.0  # Lec > 80% and L > 80%
INTERACTIVE_THRESHOLD: float = 50.0  # PQ > 50% and (AnQ + SQ) > 50%

# Logging Configuration
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
