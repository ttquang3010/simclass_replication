"""
Configuration file for SimClass Multi-Agent Simulation
Contains all constants and configuration parameters
"""

from datetime import datetime

# ==========================================
# SIMULATION PARAMETERS
# ==========================================
N_SESSIONS = 2  # Number of simulation runs
N_INTERACTIONS_PER_SLIDE = 2  # Reduced to increase Teacher Talk ratio

# ==========================================
# CONTEXT WINDOW MANAGEMENT (Role-based)
# ==========================================
# DeepSeek limit: 131K tokens
# Strategy: Different window sizes per agent role
MAX_CONTEXT_TEACHER = 60        # Prof. X: Keep last 60 messages (lectures are long)
MAX_CONTEXT_SUMMARY_SEEKER = None  # Summary Seeker: Keep ALL messages (needs full lecture)
MAX_CONTEXT_PEERS = 40          # Other students: Keep last 40 messages
MAX_CONTEXT_ASSISTANT = 40      # Clarity Guide: Keep last 40 messages

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
COURSE_SCRIPT_FILE = 'data/course_script.json'
AGENT_PROMPTS_FILE = 'data/agent_prompts.json'
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"logs/simulation_log_multi_agent_{TIMESTAMP}.jsonl"
