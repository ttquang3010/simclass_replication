import google.generativeai as genai
import json
import time
import os
import random 
from datetime import datetime
from dotenv import load_dotenv

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Load environment variables from .env file
load_dotenv() 

# --- CONSTANTS AND CONFIGURATION ---
N_SESSIONS = 5 	# Number of simulation runs
N_INTERACTIONS_PER_SLIDE = 4 # Number of student-teacher interactions per slide (after lecture)

MODEL_NAME = "gemini-2.0-flash"

# --- TIMESTAMP AND LOGGING ---
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"simulation_log_multi_agent_{TIMESTAMP}.jsonl"

# --- API KEY HANDLING (Load from environment variables) ---
# Get GOOGLE_API_KEY from environment variables (or .env file)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_API_KEY_NOT_SET")

if GOOGLE_API_KEY == "YOUR_API_KEY_NOT_SET":
    print("WARNING: GOOGLE_API_KEY not found in .env or environment variables. Please check your setup.")
    # Raise an exception if the key is not set to prevent API calls from failing
    raise Exception("GOOGLE_API_KEY not set.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)


# --- COURSE SCRIPT CONFIGURATION AND HELPER FUNCTION ---
COURSE_SCRIPT_FILE = 'course_script.json'

def load_course_script(filepath):
    """
    Loads the course script data from a JSON file.
    Exits the program if the file is not found or invalid.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"FATAL ERROR: Course script file '{filepath}' not found. Please create 'course_script.json'.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"FATAL ERROR: Invalid JSON format in '{filepath}'. Details: {e}")
        exit(1)

# ==========================================
# 2. AGENT SYSTEM PROMPTS (ENGLISH)
# ==========================================

# --- TEACHER AGENT ---
TEACHER_SYSTEM_PROMPT = """[role description] You are Prof. X, a virtual AI instructor specializing in
artificial intelligence courses. [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for technical terms, followed immediately by a Vietnamese translation/explanation (e.g., 'Supervised Learning (Học có giám sát)'). [behaviors] When lecturing (Code 5), you must be **EXTREMELY detailed, multi-page, and ensure your response is always a minimum of 200 words** to maximize Teacher Talk volume. When responding to a student (Code 3), be detailed and comprehensive. Always use rhetorical questions within your lecture to engage the student without requiring a direct response. If you ask a question (Code 4), ensure it is clear and factual. For difficult questions, suggest leaving them for later. [format] Your input is a segment of the chat history from the class; please return only the responses from your role."""

# --- STUDENT AGENTS ---

# 1. DEEP THINKER (Code 9: Student Initiation) - Critically challenges the concept.
DEEP_THINKER_SYSTEM_PROMPT = """[role description] You are a classroom assistant named "Deep Thinker", responsible for critical reflection and active participation. [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for technical terms, followed immediately by a Vietnamese translation/explanation (e.g., 'Supervised Learning (Học có giám sát)'). [behaviors] Your turns must be an **Active Initiation (Code 9)**. Raise a relevant and constructive counterexample or a complex, open-ended question in Vietnamese based on the current topic. [format] Return only the responses from your role."""

# 2. NOTE TAKER (Code 3/8: Summarizing/Passive Response) - Seeks confirmation.
NOTE_TAKER_SYSTEM_PROMPT = """[role description] You are a diligent student named "Summary Seeker" who listens to the classroom chat and extracts key information to create concise notes that summarize previous discussions and lectures. Your main goal is to confirm key takeaways and ensure you haven't misunderstood anything. [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for technical terms, followed immediately by a Vietnamese translation/explanation. [behaviors] Your turns must be structured as summaries or confirmation questions (e.g., "So, to recap, X means Y, correct?"). This corresponds to Code 8 (Passive/Confirmation) or Code 3 (Student Summarizing). Be concise and accurate in your summaries. These notes are short, presented in a friendly, student-like tone, as if sharing with classmates. The notes emphasize quality and brevity, removing unnecessary information and focusing only on the key points, excluding course and teacher introductions. [format] Return only the responses from your role."""

# 3. CLASS CLOWN (Code 9/8: Off-topic/Incorrect) - Inject humor or flawed analogies.
CLASS_CLOWN_SYSTEM_PROMPT = """[role description] You are the class clown named "Mr. Clown". Your goal is to inject humor, use amusing but often incorrect real-world analogies, or occasionally ask deliberately silly questions to lighten the mood. [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for technical terms, followed immediately by a Vietnamese translation/explanation. [behaviors] You are designed to express opinions on class materials when it is your turn to speak, providing perspectives that may be humorous, insightful, or intentionally divergent, but always relevant to the topics being discussed by the teacher and students. Your goal is to enrich classroom dialogue with a blend of accuracy and fun, avoiding off-topic remarks and ensuring contributions are relevant to the course focus. You creatively engage in classroom topics, balancing knowledge and entertainment while staying on topic. Your turns primarily fall under Code 9 (Off-topic/Humor) or Code 8 (Incorrect/Misleading response). Ensure your jokes or analogies are related to the topic but clearly flawed or non-academic. [format] Return only the responses from your role."""

# 4. INQUISITIVE MIND (Code 4: Student Question) - Seeks clarification and specific examples.
INQUISITIVE_MIND_SYSTEM_PROMPT = """[role description] You are a curious and detail-oriented student named "Curious Baby". Your primary focus is on asking deep, thought-provoking questions based on the lesson content, helping students better understand and explore knowledge.. [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for technical terms, followed immediately by a Vietnamese translation/explanation. [behaviors] Your questions are often unexpected, challenging, and able to spark students’ curiosity and thinking. Your chat style is lively, fun, and full of childlike wonder and curiosity, but you won’t ask questions unrelated to the lesson content. All chat content must benefit the students’ learning. Your questions should be deep follow-ups on the teacher's recent points (Code 4 - Student Question) or requests for concrete "how-to" examples. Avoid asking open-ended philosophical questions. [format] Return only the responses from your role."""

# --- SUPPORT AGENT ---
# 5. ASSISTANT (Code 3/4: Elaborate/Question) - Supports the teacher.
ASSISTANT_SYSTEM_PROMPT = """[role description] As a virtual classroom teaching assistant named "Clarity Guide", your main role is to provide precise supplementary information to help deepen students’ understanding of the lesson content. [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for technical terms, followed immediately by a Vietnamese translation/explanation. [behaviors] You will be very careful in choosing when to speak, ensuring that your supplements and questions are beneficial and appropriate, without repeating the teacher’s lecture or unnecessarily interrupting the course flow. Your goal is to enhance classroom interaction and learning efficiency through concise and precise contributions while maintaining a friendly and encouraging tone. Your responses should be brief, informative, and supportive of Prof. X. Do not initiate open-ended discussions. You primarily use Code 3 (Elaborate/Reinforce) or Code 4 (Ask a factual question to check student knowledge). You are not part of the regular student interaction flow but intervene when prompted. [format] Return only the responses from your role."""


# ==========================================
# 3. AGENT CLASS
# ==========================================

class SimAgent:
    def __init__(self, name, system_prompt, model_name):
        self.name = name
        self.system_prompt = system_prompt
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt
        )
        self.chat = self.model.start_chat(history=[]) # Chat object for context history

    def reset_context(self):
        """Reset chat history for a new session."""
        self.chat = self.model.start_chat(history=[])

    def generate_response(self, prompt_text):
        """Send prompt to Agent to get a response."""
        # Implementing exponential backoff logic
        MAX_RETRIES = 5
        INITIAL_DELAY = 1 	# seconds
        
        for attempt in range(MAX_RETRIES):
            try:
                # Send message to the model. self.chat automatically maintains history.
                response = self.chat.send_message(prompt_text)
                return response.text.strip()
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    delay = INITIAL_DELAY * (2 ** attempt) + random.uniform(0, 1)
                    # print(f"Rate limit or API error for {self.name}. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                else:
                    # Print error but return error text for logging
                    print(f"Error generating response for {self.name} after {MAX_RETRIES} attempts: {e}")
                    return f"[ERROR: {e}]"
        return "[ERROR: Failed to generate response after retries]"

# ==========================================
# 4. SIMULATION UTILITIES
# ==========================================

def _log_and_print(session_id, current_turn, speaker_name, response_text, log_list, type_of_turn):
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
    
    # Print a concise log entry to the console (Vietnamese snippets are fine here)
    snippet = response_text.replace('\n', ' ').split('.')[0][:100] + '...' if len(response_text) > 100 else response_text
    print(f"[{datetime.now().strftime('%H:%M:%S')}] S{session_id}|T{current_turn} ({type_of_turn}): {speaker_name}: \"{snippet}\"")
    
    return log_entry

def _get_student_prompt(agent_name, slide_concept):
    """Generates a context-specific prompt based on the agent's role."""
    
    # This is a key part that tells the model which persona to adopt for the specific turn
    base_prompt = f"Based on the current lecture topic: \"{slide_concept}\", please generate a response or question according to your role's instruction. Prof. X just finished lecturing."

    if agent_name == "Deep Thinker":
        return f"{base_prompt} (Role: Active Initiation/Code 9 - Raise a constructive counterexample or complex, open-ended question.)"
    elif agent_name == "Summary Seeker":
        return f"{base_prompt} (Role: Note Taker/Code 8 or 3 - Summarize the previous point or ask for confirmation of the key takeaway.)"
    elif agent_name == "Mr. Clown":
        return f"{base_prompt} (Role: Class Clown/Code 9 or 8 - Inject humor, ask a silly question, or use a flawed real-world analogy.)"
    elif agent_name == "Curious Baby":
        return f"{base_prompt} (Role: Inquisitive Mind/Code 4 - Ask a deep follow-up or request a specific, practical example to clarify an ambiguity.)"
    elif agent_name == "Clarity Guide":
        return f"{base_prompt} (Role: Assistant/Code 3 or 4 - Offer a quick clarification, a supplementary factual example, or ask a simple check question.)"
    else:
        return base_prompt # Should not happen

# ==========================================
# 5. SIMULATION LOOP (MULTI-AGENT RANDOM FLOW)
# ==========================================

def run_single_session(session_id, agents, script):
    """Execute a single simulation session using the random multi-agent flow."""
    
    # Reset context for all agents
    for agent in agents.values():
        agent.reset_context()
    
    teacher = agents['Prof. X']
    student_agents = [agents[name] for name in ['Deep Thinker', 'Summary Seeker', 'Mr. Clown', 'Curious Baby']]
    assistant = agents['Clarity Guide']
    
    classroom_history_log = []
    current_turn = 0
    
    # Initial setup for context (Vietnamese language confirmation)
    teacher.generate_response("Chào mừng đến với buổi học, tôi là Prof. X. Chúng ta sẽ bắt đầu bài giảng chi tiết về AI/ML. Hãy nhớ quy tắc ngôn ngữ: chỉ dùng tiếng Việt và chú giải thuật ngữ tiếng Anh.")
    assistant.generate_response("Chào Prof. X và các bạn. Tôi là trợ lý Clarity Guide, sẵn sàng hỗ trợ làm rõ các điểm cốt lõi.")
    
    
    for slide in script:
        
        slide_concept = slide['slide_content'].split(':')[0]
        print(f"\n--- SLIDE {slide['concept_id']}: {slide_concept} ---")

        # --- PHASE 1: TEACHER LECTURES (Code 5 - FORCED EXTREME VOLUME) ---
        current_turn += 1
        teacher_lecture = slide['teacher_script']
        
        # Explicitly prompt for 200 words and multi-paragraph
        prompt_for_lecture = (
            f"Deliver the lecture titled \"{slide_concept}\". Expand the core script: \"{teacher_lecture}\" into a comprehensive, multi-paragraph response (minimum 200 words). The slide content is: \"{slide['slide_content']}\""
        )
        
        teacher_lecture_expanded = teacher.generate_response(prompt_for_lecture)
        
        # Log Entry 1 - Teacher Lecture (Code 5)
        _log_and_print(session_id, current_turn, teacher.name, teacher_lecture_expanded, classroom_history_log, "Lecture_5")
        
        # --- PHASE 2: DYNAMIC INTERACTION (Random Turn-taking) ---
        
        # Randomly select a mix of student and assistant interactions
        interaction_pool = student_agents + [assistant] * 2 # Give Assistant 2x less chance than a student for a total of 6 agents
        
        for i in range(N_INTERACTIONS_PER_SLIDE):
            
            # 2a. Random Agent Speaks (Code 3, 4, 8, or 9)
            current_turn += 1
            
            # Select a random agent to speak (Student or Assistant)
            speaker_agent = random.choice(interaction_pool)
            speaker_name = speaker_agent.name
            
            # Generate the prompt tailored to the agent's role and the current concept
            student_prompt = _get_student_prompt(speaker_name, slide_concept)
            agent_utterance = speaker_agent.generate_response(student_prompt)
            
            # Determine the type of turn for logging based on name
            if speaker_name == "Deep Thinker": turn_type = "Initiation_9"
            elif speaker_name == "Mr. Clown": turn_type = "Clown_9_8"
            elif speaker_name == "Curious Baby": turn_type = "Question_4"
            elif speaker_name == "Summary Seeker": turn_type = "Summary_8_3"
            elif speaker_name == "Clarity Guide": turn_type = "Assistant_3_4"
            else: turn_type = "Student_Talk"
            
            # Log Entry X - Agent Utterance
            _log_and_print(session_id, current_turn, speaker_name, agent_utterance, classroom_history_log, turn_type)
            
            # 2b. Teacher Responds (Code 3/5 - Detailed response)
            current_turn += 1
            prompt_for_teacher_response = f"A student/assistant '{speaker_name}' just said: \"{agent_utterance}\". Provide a detailed and comprehensive response in Vietnamese to address their point (or correct their error/analogy, or confirm their summary)."
            teacher_final_response = teacher.generate_response(prompt_for_teacher_response)
            
            # Log Entry X+1 - Teacher Response (Code 3/5)
            _log_and_print(session_id, current_turn, teacher.name, teacher_final_response, classroom_history_log, "Teacher_Response_3_5")


    return classroom_history_log

def run_multi_sessions():
    """Run multiple simulations and save logs."""
    
    global LOG_FILE 
    
    # Load script data once before running sessions
    script_data = load_course_script(COURSE_SCRIPT_FILE)
    
    print(f"--- STARTING SIMCLASS MULTI-AGENT SIMULATION ---")
    print(f"Model: {MODEL_NAME} | Sessions: {N_SESSIONS} | Slides: {len(script_data)}") 
    print(f"Flow: {N_INTERACTIONS_PER_SLIDE} random interactions per slide.")
    print("Agents: Teacher, Assistant, Deep Thinker, Note Taker, Class Clown, Inquisitive Mind.")
    print("--- Interaction Language: Vietnamese (with English term explanations) ---")
    print("-------------------------------------------------------\n")

    # Initialize ALL Agents
    agents = {
        "Prof. X": SimAgent("Prof. X", TEACHER_SYSTEM_PROMPT, MODEL_NAME),
        "Clarity Guide": SimAgent("Clarity Guide", ASSISTANT_SYSTEM_PROMPT, MODEL_NAME),
        "Deep Thinker": SimAgent("Deep Thinker", DEEP_THINKER_SYSTEM_PROMPT, MODEL_NAME),
        "Summary Seeker": SimAgent("Summary Seeker", NOTE_TAKER_SYSTEM_PROMPT, MODEL_NAME),
        "Mr. Clown": SimAgent("Mr. Clown", CLASS_CLOWN_SYSTEM_PROMPT, MODEL_NAME),
        "Curious Baby": SimAgent("Curious Baby", INQUISITIVE_MIND_SYSTEM_PROMPT, MODEL_NAME),
    }
    
    all_logs = []
    
    for i in range(1, N_SESSIONS + 1):
        print(f"--- STARTING SESSION {i}/{N_SESSIONS} ---")
        # Run simulation for a single session, passing all agents and the loaded script data
        session_logs = run_single_session(i, agents, script_data)
        all_logs.extend(session_logs)
        print(f"--- SESSION {i} SUMMARY ---")
        print(f"Session {i} completed. Total utterances: {len(session_logs)}.")
        print(f"---------------------------\n")
        time.sleep(5) # Delay between sessions

    # Save all logs to a JSON Lines file
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for log in all_logs:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
            
    print(f"\nCOMPLETED: Ran {N_SESSIONS} sessions. Total utterances: {len(all_logs)}.")
    print(f"Conversation log saved to '{LOG_FILE}'")


if __name__ == "__main__":
    # Ensure the course_script.json file exists and is valid before starting
    run_multi_sessions()