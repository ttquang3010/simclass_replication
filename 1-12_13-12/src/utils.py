"""
Utility functions for SimClass Multi-Agent Simulation
Includes question classification, difficulty estimation, logging, and prompts
"""

import json
from datetime import datetime


def is_asking_question(text):
    """Check if the text contains a question."""
    question_indicators = ['?', 'tại sao', 'như thế nào', 'có thể', 'liệu', 'có phải', 'là gì', 'nghĩa là']
    return any(indicator in text.lower() for indicator in question_indicators)


def classify_question_difficulty(text, speaker_name):
    """Classify question as basic, medium, or advanced."""
    if speaker_name == "Deep Thinker":
        return "advanced"
    elif speaker_name == "Curious Baby":
        return "basic"
    elif speaker_name == "Mr. Clown":
        return "medium"
    else:
        return "basic"


def calculate_lecture_complexity(lecture_text):
    """Estimate lecture complexity based on length."""
    return len(lecture_text)


def estimate_slide_difficulty(slide_concept):
    """Estimate difficulty of slide topic (0.0-1.0)."""
    difficult_keywords = ['gradient', 'optimization', 'neural', 'deep', 'backpropagation']
    basic_keywords = ['introduction', 'overview', 'definition', 'example']
    
    difficulty = 0.5  # Default medium
    
    concept_lower = slide_concept.lower()
    if any(keyword in concept_lower for keyword in difficult_keywords):
        difficulty = 0.8
    elif any(keyword in concept_lower for keyword in basic_keywords):
        difficulty = 0.3
    
    return difficulty


def log_and_print(session_id, current_turn, speaker_name, response_text, log_list, type_of_turn):
    """Helper function to log the entry and print status immediately."""
    log_entry = {
        "session_id": session_id,
        "turn": current_turn,
        "speaker": speaker_name,
        "text": response_text,
        "type": type_of_turn,
        "timestamp": datetime.now().isoformat()
    }
    log_list.append(log_entry)
    
    # Print a concise log entry to the console
    snippet = response_text.replace('\n', ' ').split('.')[0][:100] + '...' if len(response_text) > 100 else response_text
    print(f"[{datetime.now().strftime('%H:%M:%S')}] S{session_id}|T{current_turn} ({type_of_turn}): {speaker_name}: \"{snippet}\"")
    
    return log_entry


def get_student_prompt(agent_name, slide_concept, context="general"):
    """Generates a context-specific prompt based on the agent's role and context."""
    
    if context == "after_peer_question":
        base_prompt = f"A classmate just asked a question about \"{slide_concept}\". You feel encouraged to ask your own question or add to the discussion."
    else:
        base_prompt = f"The teacher just taught about \"{slide_concept}\"."
    
    if agent_name == "Deep Thinker":
        return f"{base_prompt} Ask a deep, challenging question that explores edge cases or theoretical implications. Be thought-provoking."
    elif agent_name == "Summary Seeker":
        return f"{base_prompt} Briefly summarize what you understood to confirm your comprehension."
    elif agent_name == "Mr. Clown":
        return f"{base_prompt} Make a humorous real-world analogy to lighten the mood while staying relevant."
    elif agent_name == "Curious Baby":
        return f"{base_prompt} Ask a basic, practical question about implementation or a specific detail. Keep it simple and relatable."
    elif agent_name == "Clarity Guide":
        return f"{base_prompt} Provide a brief supplementary fact or clarification."
    else:
        return base_prompt


def write_logs_to_file(logs, log_file, mode='a'):
    """Write logs to file incrementally. Mode 'w' for new file, 'a' for append."""
    with open(log_file, mode, encoding="utf-8") as f:
        for log in logs:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")


def load_course_script(filepath):
    """Load course script data from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"FATAL ERROR: Course script file '{filepath}' not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"FATAL ERROR: Invalid JSON format in '{filepath}'. Details: {e}")
        exit(1)


def load_agent_prompts(filepath):
    """Load agent system prompts from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
            return prompts
    except FileNotFoundError:
        print(f"FATAL ERROR: Agent prompts file '{filepath}' not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"FATAL ERROR: Invalid JSON format in '{filepath}'. Details: {e}")
        exit(1)
