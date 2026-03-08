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
TURNS_PER_SESSION: int = 15  # Number of 2-minute segments (30 min total)
TEMPERATURE: float = 0.7
MAX_TOKENS: int = 500
MAX_RETRIES: int = 3
BRIEF_PAUSE: float = 0.5  # seconds

# Slide Distribution Mapping
# Maps segment numbers to slide indices for 30-min class
# Some complex slides span multiple segments for realistic pacing
SLIDE_SEGMENT_MAPPING: Dict[int, int] = {
    1: 0,   2: 0,   # Slide 1 (Intro): 4 min
    3: 1,   4: 1,   # Slide 2 (Problem): 4 min
    5: 2,   6: 2,   # Slide 3 (Concept): 4 min
    7: 3,           # Slide 4 (Equation): 2 min
    8: 4,   9: 4,   # Slide 5 (Finding w,b): 4 min
    10: 5, 11: 5,   # Slide 6 (Gradient Descent): 4 min
    12: 6,          # Slide 7 (Code Demo): 2 min
    13: 7,          # Slide 8 (Applications): 2 min
    14: 8,          # Slide 9 (Limitations): 2 min
    15: 9           # Slide 10 (Summary): 2 min
}

# File Paths
AGENT_PROMPTS_MODULE: str = "data.agent_prompts_vi"  # Python module for agent prompts
SLIDES_DATA_PATH: str = "data/linear_regression_slides.json"
RESULTS_DIR: str = "results"
LOGS_DIR: str = "logs"

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
