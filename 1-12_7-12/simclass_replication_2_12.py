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
load_dotenv() 

# --- CONSTANTS AND CONFIGURATION ---
N_SESSIONS = 5 	# Number of simulation runs (Increase to 15 for final result)

# --- DYNAMIC FLOW CONFIGURATION (V4) ---
# Total interaction probability: 1.0 - NO_INTERACTION_PROBABILITY
NO_INTERACTION_PROBABILITY = 0.15 # 15% chance of a silent turn (skips student response)
# The remaining 85% of turns are active interactions, split below:
# 80% of active interactions: Student Initiation (Code 9 -> Code 3) -> Maximize SIR
INITIATION_PROBABILITY_OF_ACTIVE = 0.80 

MODEL_NAME = "gemini-2.0-flash"

# --- TIMESTAMP AND LOGGING ---
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"simulation_log_structured_{TIMESTAMP}.jsonl"

# --- API KEY HANDLING (Load from environment variables) ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_API_KEY_NOT_SET")

if GOOGLE_API_KEY == "YOUR_API_KEY_NOT_SET":
    print("WARNING: GOOGLE_API_KEY not found in .env or environment variables. Please check your setup.")
    raise Exception("GOOGLE_API_KEY not set.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)


# --- NEW CONFIGURATION AND HELPER FUNCTION FOR FILE LOADING ---
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
# 2. AGENT PROMPTS
# ==========================================

TEACHER_SYSTEM_PROMPT = """[role description] You are Prof. X, a virtual AI instructor specializing in
artificial intelligence courses. [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for technical terms, followed immediately by a Vietnamese translation/explanation (e.g., 'Supervised Learning (Học có giám sát)'). [behaviors] When lecturing (Code 5), you must be **EXTREMELY detailed, multi-page, and ensure your response is always a minimum of 200 words** to maximize Teacher Talk volume. When responding to a student (Code 3), be detailed and comprehensive. Always use rhetorical questions within your lecture to engage the student without requiring a direct response. If you ask a question (Code 4), ensure it is clear and factual. For difficult questions, suggest leaving them for later. [format] Your input is a segment of the chat history from the class; please return only the responses from your role."""

DEEP_THINKER_SYSTEM_PROMPT = """[role description] You are a classroom assistant named "Deep Thinker", responsible for critical reflection and active participation. [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for technical terms, followed immediately by a Vietnamese translation/explanation (e.g., 'Supervised Learning (Học có giám sát)'). [behaviors] Your primary goal is to simulate realistic student behavior. You are strongly encouraged to use **Active Initiation (Code 9)**.
1. **Passive Response (Code 8):** If Prof. X asks a specific, closed, or factual question, you must respond directly and concisely in Vietnamese.
2. **Active Initiation (Code 9):** If Prof. X is lecturing, or after a detailed response, you must raise a relevant and constructive counterexample or complex, open-ended question in Vietnamese. 
Your default behavior when not directly questioned is Code 9.
[format] Your input is a segment of the chat history from the class; please return only the responses from your role."""

# --- UPDATED COURSE SCRIPT (The actual content is now in course_script.json) ---
course_script = [] # Placeholder for the data to be loaded

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
# 4. SIMULATION LOOP (V4 DYNAMIC FLOW IMPLEMENTATION)
# ==========================================

def _log_and_print(session_id, current_turn, speaker_name, response_text, log_list, type_of_turn):
    """Helper function to log the entry and print status immediately."""
    log_entry = {
        "session_id": session_id,
        "turn": current_turn,
        "speaker": speaker_name,
        "text": response_text,
        "timestamp": datetime.now().isoformat()
    }
    log_list.append(log_entry)
    
    # Print a concise log entry to the console
    snippet = response_text.replace('\n', ' ').split('.')[0][:100] + '...' if len(response_text) > 100 else response_text
    print(f"[{datetime.now().strftime('%H:%M:%S')}] S{session_id}|T{current_turn} ({type_of_turn}): {speaker_name}: \"{snippet}\"")
    
    # We remove the sleep here as it's handled by the caller or the API backoff.
    # time.sleep(1) 
    return log_entry

def run_single_session(session_id, teacher, student, script):
    """Execute a single simulation session using the dynamic flow."""
    
    teacher.reset_context()
    student.reset_context()
    
    classroom_history_log = []
    current_turn = 0
    
    # Initial setup for context - Ensuring language rules are top of mind
    teacher.generate_response("Bạn sắp bắt đầu một bài giảng chi tiết về các khái niệm AI/ML. Hãy nhớ quy tắc ngôn ngữ bắt buộc: chỉ dùng tiếng Việt, và chú giải thuật ngữ tiếng Anh.")
    student.generate_response("Tôi đã sẵn sàng tham gia và phản biện. Quy tắc ngôn ngữ bắt buộc đã được ghi nhớ: chỉ dùng tiếng Việt, và chú giải thuật ngữ tiếng Anh.")
    
    for slide in script:
        
        # Log slide transition for clarity
        print(f"\n--- SLIDE {slide['concept_id']}: {slide['slide_content'].split(':')[0]} ---")

        # --- PHASE 1: TEACHER LECTURES (Expected Code 5 - FORCED EXTREME VOLUME) ---
        current_turn += 1
        teacher_lecture = slide['teacher_script']
        
        # Explicitly prompt for 200 words and multi-paragraph
        prompt_for_lecture = (
            f"Deliver the lecture titled \"{slide['slide_content'].split(':')[0]}\". Expand the core script: \"{teacher_lecture}\" into a comprehensive, multi-paragraph response (minimum 200 words). The slide content is: \"{slide['slide_content']}\""
        )
        
        teacher_lecture_expanded = teacher.generate_response(prompt_for_lecture)
        
        # Log Entry 1 - Teacher Lecture (Code 5)
        _log_and_print(session_id, current_turn, teacher.name, teacher_lecture_expanded, classroom_history_log, "Lecture_5")
        
        # --- PHASE 2: DYNAMIC INTERACTION CHECK (Control flow for TT/ST balance) ---
        
        interaction_roll = random.random()
        
        if interaction_roll < NO_INTERACTION_PROBABILITY:
            # --- SCENARIO C (15%): SILENT TURN (Skipped interaction) ---
            print(f"[{datetime.now().strftime('%H:%M:%S')}] S{session_id}, Slide {slide['concept_id']}: Skipping student interaction (Silent Turn).")
            continue # Move to the next slide immediately

        # If interaction is triggered (85% chance)
        active_interaction_roll = random.random()
        
        if active_interaction_roll < INITIATION_PROBABILITY_OF_ACTIVE:
            # --- SCENARIO A (80% of active, 68% total): STUDENT INITIATION (Code 9 -> Code 3) ---
            
            # 2a. Student Initiates (Code 9)
            current_turn += 1
            # Prompt the student to perform their default action (Code 9)
            prompt_for_student_initiation = (
                f"Prof. X just finished lecturing. Based on the concept \"{slide['slide_content'].split(':')[0]}\", perform your default action: raise a new, relevant, open-ended question or a constructive counterexample in Vietnamese."
            )
            student_initiation_9 = student.generate_response(prompt_for_student_initiation)
            
            # Log Entry 2 - Deep Thinker Initiation (Code 9)
            _log_and_print(session_id, current_turn, student.name, student_initiation_9, classroom_history_log, "Initiation_9")
            
            # 2b. Teacher Responds to Initiation (Expected Code 3/5 - Detailed response)
            current_turn += 1
            prompt_for_teacher_response = f"A student 'Deep Thinker' just initiated a discussion with: \"{student_initiation_9}\". Provide a detailed and comprehensive response in Vietnamese to address their critical point."
            teacher_final_response = teacher.generate_response(prompt_for_teacher_response)
            
            # Log Entry 3 - Teacher Response (Code 3/5)
            _log_and_print(session_id, current_turn, teacher.name, teacher_final_response, classroom_history_log, "Response_3")
            
        else:
            # --- SCENARIO B (20% of active, 17% total): TEACHER CHECK (Code 4 -> Code 8 -> Code 3) ---
            
            # 2a. Teacher Asks Closed Question (Expected Code 4)
            current_turn += 1
            closed_question = f"Giờ chúng ta hãy làm rõ một điểm cốt lõi. Dựa trên nội dung về {slide['slide_content'].split(':')[0]}, hãy nói tóm tắt sự khác biệt về bản chất giữa $X$ (Features) và $y$ (Labels) mà chúng ta vừa học là gì?"
            teacher_response_q = teacher.generate_response(closed_question) # Teacher asks a question (Code 4)
            
            # Log Entry 2 - Teacher Asks a closed question (Code 4)
            _log_and_print(session_id, current_turn, teacher.name, teacher_response_q, classroom_history_log, "Question_4")
            
            # 2b. Deep Thinker Responds (Expected Code 8 - Forced response)
            current_turn += 1
            prompt_for_student_response = f"Prof. X just asked a factual question: \"{teacher_response_q}\". Please respond directly and concisely in Vietnamese to this specific question, without adding any new points."
            student_response_8 = student.generate_response(prompt_for_student_response) # Student responds (Code 8)
            
            # Log Entry 3 - Deep Thinker Responds (Code 8)
            _log_and_print(session_id, current_turn, student.name, student_response_8, classroom_history_log, "Response_8")

            # 2c. Teacher Acknowledges (Expected Code 3 - Detailed acknowledgement)
            current_turn += 1
            prompt_for_teacher_ack = f"The student 'Deep Thinker' responded: \"{student_response_8}\". Please acknowledge the correct response, elaborate significantly on the importance of X and Y, and encourage further focus on the material. Ensure your response is detailed."
            teacher_ack = teacher.generate_response(prompt_for_teacher_ack) # Teacher acknowledges (Code 3)
            
            # Log Entry 4 - Teacher Acknowledgement (Code 3)
            _log_and_print(session_id, current_turn, teacher.name, teacher_ack, classroom_history_log, "Acknowledge_3")


    return classroom_history_log

def run_multi_sessions():
    """Run multiple simulations and save logs."""
    # Retrieve the global LOG_FILE variable (which includes the timestamp)
    global LOG_FILE 
    
    # --- CHANGE START ---
    # Load script data once before running sessions
    script_data = load_course_script(COURSE_SCRIPT_FILE)
    # --- CHANGE END ---
    
    print(f"--- STARTING SIMCLASS REPLICATION (V4: EXTREME TT & HIGH SIR) ---")
    print(f"Model: {MODEL_NAME} | Sessions: {N_SESSIONS} | Slides: {len(script_data)}") # Use loaded data length
    print(f"Flow: 15% Silent, 68% Code 9, 17% Code 4->8. Teacher Lecture forced to >200 words.")
    print("--- Ngôn ngữ tương tác: Tiếng Việt (có chú giải thuật ngữ tiếng Anh) ---")
    print("-------------------------------------------------------\n")

    # Initialize Agents
    teacher = SimAgent("Prof. X", TEACHER_SYSTEM_PROMPT, MODEL_NAME)
    student = SimAgent("Deep Thinker", DEEP_THINKER_SYSTEM_PROMPT, MODEL_NAME)
    
    all_logs = []
    
    for i in range(1, N_SESSIONS + 1):
        print(f"--- STARTING SESSION {i}/{N_SESSIONS} ---")
        # Run simulation for a single session, passing the loaded script data
        session_logs = run_single_session(i, teacher, student, script_data)
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
    run_multi_sessions()