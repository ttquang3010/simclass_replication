"""
Configuration file for SimClass Multi-Agent Simulation
Contains all constants and configuration parameters
"""

from datetime import datetime

# ==========================================
# SIMULATION PARAMETERS
# ==========================================
N_SESSIONS = 1  # Number of simulation runs per lecture
N_INTERACTIONS_PER_SLIDE = 2  # Reduced to increase Teacher Talk ratio
AUTO_SAVE_INTERVAL = 300  # Auto-save logs every 5 minutes (300 seconds)

# Multi-lecture configuration
START_LECTURE_ID = 1  # Start from lecture 2 (1 already completed)
END_LECTURE_ID = 5    # End at lecture 5
RUN_ALL_LECTURES = True  # Set to False to run only CURRENT_LECTURE_ID

# ==========================================
# CONTEXT WINDOW MANAGEMENT (Role-based)
# ==========================================
# DeepSeek limit: 131K tokens (~100K words or ~40K Chinese characters)
# Strategy: Different window sizes per agent role + periodic reset
MAX_CONTEXT_TEACHER = 50        # Prof. X: Keep last 50 messages (lectures are long)
MAX_CONTEXT_SUMMARY_SEEKER = 100  # Summary Seeker: Keep last 100 messages (was unlimited, now capped)
MAX_CONTEXT_PEERS = 35          # Other students: Keep last 35 messages
MAX_CONTEXT_ASSISTANT = 35      # Clarity Guide: Keep last 35 messages

# Periodic context cleanup
CONTEXT_RESET_INTERVAL = 10     # Reset all agent contexts every N slides to prevent overflow

# ==========================================
# API CONFIGURATION
# ==========================================
# API keys should be loaded from .env file
# Priority: DeepSeek first, then Google Gemini as fallback
DEEPSEEK_MODEL = "deepseek-chat"
GOOGLE_MODEL = "gemini-2.0-flash"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ==========================================
# API REQUEST PARAMETERS
# ==========================================
API_TEMPERATURE = 0.7
API_MAX_TOKENS = 2000
API_MAX_RETRIES = 5
API_INITIAL_RETRY_DELAY = 1

# ==========================================
# FILE PATHS
# ==========================================
# Available lectures
COURSE_SCRIPTS = {
    1: 'data/course_script_lecture_1.json',
    2: 'data/course_script_lecture_2.json',
    3: 'data/course_script_lecture_3.json',
    4: 'data/course_script_lecture_4.json',
    5: 'data/course_script_lecture_5.json'
}

# Select which lecture to run (Change this ID to switch lectures)
CURRENT_LECTURE_ID = 1

COURSE_SCRIPT_FILE = COURSE_SCRIPTS.get(CURRENT_LECTURE_ID, 'data/course_script_lecture_1.json')
AGENT_PROMPTS_FILE = 'data/agent_prompts.json'

# Shared log file for all lectures (use existing file from lecture 1)
SHARED_LOG_FILE = 'logs/simulation_log_multi_agent_20251210_110948.jsonl'
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = SHARED_LOG_FILE  # Use shared file for continuation
