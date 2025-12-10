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
    """Run simulation for all lectures sequentially."""
    
    # Initialize
    model_name = initialize_api()
    prompts = load_agent_prompts(config.AGENT_PROMPTS_FILE)
    
    # Determine which lectures to run
    if config.RUN_ALL_LECTURES:
        lecture_ids = range(config.START_LECTURE_ID, config.END_LECTURE_ID + 1)
        print(f"\n{'='*80}")
        print(f"SIMCLASS MULTI-LECTURE SIMULATION")
        print(f"Running Lectures {config.START_LECTURE_ID} to {config.END_LECTURE_ID}")
        print(f"{'='*80}")
    else:
        lecture_ids = [config.CURRENT_LECTURE_ID]
        print(f"\n{'='*80}")
        print(f"SIMCLASS SINGLE LECTURE SIMULATION")
        print(f"Running Lecture {config.CURRENT_LECTURE_ID}")
        print(f"{'='*80}")
    
    print(f"Model: {model_name}")
    print(f"Sessions per lecture: {config.N_SESSIONS}")
    print(f"Auto-save: Every {config.AUTO_SAVE_INTERVAL} seconds")
    print(f"Shared log file: {config.SHARED_LOG_FILE}")
    print(f"Flow: Teacher checks understanding → Peer patterns → Simulated User encouraged to participate")
    print("Agents: Prof. X, Clarity Guide, Deep Thinker, Summary Seeker, Mr. Clown, Curious Baby, Student")
    print("Interaction Language: Vietnamese (with English ML/AI term translations)")
    print(f"{'='*80}\n")

    # Create agents once (will be reused across lectures with context reset)
    agent_instances = create_agents(prompts, model_name)
    
    total_utterances = 0
    
    # Run simulations for each lecture
    for lecture_id in lecture_ids:
        lecture_file = config.COURSE_SCRIPTS.get(lecture_id)
        if not lecture_file:
            print(f"[WARNING] Lecture {lecture_id} not found. Skipping.")
            continue
            
        script_data = load_course_script(lecture_file)
        
        print(f"\n{'='*80}")
        print(f"LECTURE {lecture_id}/{config.END_LECTURE_ID}: {lecture_file}")
        print(f"Slides: {len(script_data)}")
        print(f"{'='*80}\n")
        
        # Run session for this lecture
        for session_num in range(1, config.N_SESSIONS + 1):
            # Session ID format: lecture_id * 100 + session_num (e.g., 201 for lecture 2, session 1)
            session_id = lecture_id * 100 + session_num
            
            print(f"\n--- LECTURE {lecture_id} - SESSION {session_num}/{config.N_SESSIONS} (ID: {session_id}) ---")
            session_logs = run_single_session(session_id, agent_instances, script_data, config.SHARED_LOG_FILE)
            total_utterances += len(session_logs)
            
            print(f"\n--- LECTURE {lecture_id} - SESSION {session_num} SUMMARY ---")
            print(f"Session {session_id} completed. Utterances: {len(session_logs)}.")
            print(f"Cumulative total: {total_utterances} utterances")
            print(f"Logs appended to: {config.SHARED_LOG_FILE}")
            print(f"---------------------------\n")
        
        print(f"\n[LECTURE {lecture_id} COMPLETED] Moving to next lecture...\n")
            
    print(f"\n{'='*80}")
    print(f"ALL SIMULATIONS COMPLETED")
    print(f"Total lectures run: {len(lecture_ids)}")
    print(f"Total utterances: {total_utterances}")
    print(f"Final log file: {config.SHARED_LOG_FILE}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    run_multi_sessions()
