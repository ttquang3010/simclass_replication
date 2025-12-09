"""
SimClass Multi-Agent Classroom Simulation
Main entry point for running the simulation with refactored modular structure
"""

import os
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv

from src import config
from src.agents import SimAgent, SimulatedUser
from src import agents  # For setting global variables
from src.utils import load_course_script, load_agent_prompts, write_logs_to_file
from src.simulation import run_single_session


def initialize_api():
    """Initialize API client based on available keys."""
    load_dotenv()
    
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", None)
    google_key = os.getenv("GOOGLE_API_KEY", None)
    
    if deepseek_key:
        agents.API_PROVIDER = "deepseek"
        agents.client = OpenAI(
            api_key=deepseek_key,
            base_url=config.DEEPSEEK_BASE_URL
        )
        model_name = config.DEEPSEEK_MODEL
        print(f"[API CONFIG] Using DeepSeek API with model: {model_name}")
    elif google_key:
        agents.API_PROVIDER = "google"
        genai.configure(api_key=google_key)
        model_name = config.GOOGLE_MODEL
        print(f"[API CONFIG] Using Google Gemini API with model: {model_name}")
    else:
        raise Exception("No API key found. Please set either DEEPSEEK_API_KEY or GOOGLE_API_KEY in .env file.")
    
    return model_name


def create_agents(prompts, model_name):
    """Create all agent instances with role-specific context windows."""
    agents_dict = {
        "Prof. X": SimAgent(
            prompts['teacher']['name'], 
            prompts['teacher']['system_prompt'], 
            model_name, 
            max_context_window=config.MAX_CONTEXT_TEACHER
        ),
        "Clarity Guide": SimAgent(
            prompts['assistant']['name'], 
            prompts['assistant']['system_prompt'], 
            model_name, 
            max_context_window=config.MAX_CONTEXT_ASSISTANT
        ),
        "Deep Thinker": SimAgent(
            prompts['deep_thinker']['name'], 
            prompts['deep_thinker']['system_prompt'], 
            model_name, 
            max_context_window=config.MAX_CONTEXT_PEERS
        ),
        "Summary Seeker": SimAgent(
            prompts['summary_seeker']['name'], 
            prompts['summary_seeker']['system_prompt'], 
            model_name, 
            max_context_window=config.MAX_CONTEXT_SUMMARY_SEEKER  # None = unlimited
        ),
        "Mr. Clown": SimAgent(
            prompts['mr_clown']['name'], 
            prompts['mr_clown']['system_prompt'], 
            model_name, 
            max_context_window=config.MAX_CONTEXT_PEERS
        ),
        "Curious Baby": SimAgent(
            prompts['curious_baby']['name'], 
            prompts['curious_baby']['system_prompt'], 
            model_name, 
            max_context_window=config.MAX_CONTEXT_PEERS
        ),
        "Student": SimulatedUser(
            prompts['simulated_user']['name'], 
            prompts['simulated_user']['system_prompt'], 
            model_name, 
            max_context_window=config.MAX_CONTEXT_PEERS
        ),
    }
    return agents_dict


def run_multi_sessions():
    """Run multiple simulation sessions and save logs."""
    
    # Initialize
    model_name = initialize_api()
    script_data = load_course_script(config.COURSE_SCRIPT_FILE)
    prompts = load_agent_prompts(config.AGENT_PROMPTS_FILE)
    
    print(f"\n--- STARTING SIMCLASS MULTI-AGENT SIMULATION (WITH SIMULATED USER) ---")
    print(f"Model: {model_name} | Sessions: {config.N_SESSIONS} | Slides: {len(script_data)}") 
    print(f"Flow: Teacher checks understanding → Peer patterns → Simulated User encouraged to participate")
    print("Agents: Prof. X, Clarity Guide, Deep Thinker, Summary Seeker, Mr. Clown, Curious Baby, Student")
    print("Interaction Language: Vietnamese (with English ML/AI term translations)")
    print("-------------------------------------------------------\n")

    # Create agents
    agent_instances = create_agents(prompts, model_name)
    
    all_logs = []
    
    # Run sessions
    for i in range(1, config.N_SESSIONS + 1):
        print(f"\n--- STARTING SESSION {i}/{config.N_SESSIONS} ---")
        session_logs = run_single_session(i, agent_instances, script_data, config.LOG_FILE)
        all_logs.extend(session_logs)
        
        # Write logs incrementally after each session
        write_mode = 'w' if i == 1 else 'a'
        write_logs_to_file(session_logs, config.LOG_FILE, mode=write_mode)
        print(f"  [LOG] Wrote {len(session_logs)} utterances to {config.LOG_FILE}")
        
        print(f"--- SESSION {i} SUMMARY ---")
        print(f"Session {i} completed. Total utterances: {len(session_logs)}.")
        print(f"---------------------------\n")
            
    print(f"\nCOMPLETED: Ran {config.N_SESSIONS} sessions. Total utterances: {len(all_logs)}.")
    print(f"Conversation log saved to '{config.LOG_FILE}'")


if __name__ == "__main__":
    run_multi_sessions()
