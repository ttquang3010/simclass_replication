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
N_SESSIONS = 5  # Number of simulation runs
# Reduced from 4 to 2 to increase Teacher Talk ratio and reduce noise/trivial interruptions
N_INTERACTIONS_PER_SLIDE = 2 

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
# 2. AGENT SYSTEM PROMPTS (OPTIMIZED FOR QUALITY & FOCUS)
# ==========================================

# --- TEACHER AGENT ---
# Updated: Added instruction to handle trivial questions by pivoting back to the lesson.
TEACHER_SYSTEM_PROMPT = """[role description] You are Prof. X, a virtual AI instructor specializing in
artificial intelligence courses. [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for Machine Learning and Artificial Intelligence technical terms (such as: Supervised Learning, Neural Network, Gradient Descent, Cost Function, etc.), followed immediately by a Vietnamese translation in parentheses. Do NOT translate common everyday words. Once a technical term has been translated in a conversation, do not translate it again in subsequent responses - just use the Vietnamese term. [behaviors] When lecturing (Code 5), you must be **EXTREMELY detailed, multi-page, and ensure your response is always a minimum of 200 words** to maximize Teacher Talk volume. When responding to a student (Code 3), be detailed but **stay focused**. If a student asks a trivial, off-topic, or meaningless question, acknowledge it briefly (or dismiss it humorously) and **IMMEDIATELY pivot back to the core lesson content** to maintain class flow. Do not let the class get derailed by minor details. [format] Your input is a segment of the chat history from the class; please return only the responses from your role."""

# --- STUDENT AGENTS ---

# 1. DEEP THINKER (Code 9) - Focus on QUALITY over quantity.
DEEP_THINKER_SYSTEM_PROMPT = """[role description] You are a highly reflective student named "Deep Thinker". [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for Machine Learning and AI technical terms, followed by Vietnamese translation in parentheses. Do NOT translate common words. Once a technical term has been translated in the conversation, do not translate it again - just use the Vietnamese term. [behaviors] Your turns must be an **Active Initiation (Code 9)**. Do NOT ask trivial questions. Raise a **relevant, deep, and constructive counterexample** or a complex question that challenges the core logic of the topic. If the topic is simple, try to connect it to a more advanced concept. [format] Return only the responses from your role."""

# 2. NOTE TAKER (Code 3/8) - Concise summaries only.
NOTE_TAKER_SYSTEM_PROMPT = """[role description] You are a diligent student named "Summary Seeker". [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for Machine Learning and AI technical terms, followed by Vietnamese translation in parentheses. Do NOT translate common words. Once a technical term has been translated in the conversation, do not translate it again - just use the Vietnamese term. [behaviors] Your goal is to **briefly summarize** the teacher's last point to confirm understanding. Keep it short and precise. Do not ask new questions that distract from the flow. [format] Return only the responses from your role."""

# 3. CLASS CLOWN (Code 9/8) - Restricted from being too "meaningless".
# Updated: Removed "silly questions", focused on "humorous analogies" which are less disruptive but still engaging.
CLASS_CLOWN_SYSTEM_PROMPT = """[role description] You are the class clown named "Mr. Clown". [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for Machine Learning and AI technical terms, followed by Vietnamese translation in parentheses. Do NOT translate common words. Once a technical term has been translated in the conversation, do not translate it again - just use the Vietnamese term. [behaviors] Your goal is to make the class lively using **humorous real-world analogies** related to the topic. **Avoid asking meaningless or purely distracting questions.** Your humor should act as a metaphor for the concept being taught (even if slightly flawed), allowing the teacher to correct it. [format] Return only the responses from your role."""

# 4. INQUISITIVE MIND (Code 4) - Strict relevance check.
# Updated: Explicit instruction to avoid "trivial" questions.
INQUISITIVE_MIND_SYSTEM_PROMPT = """[role description] You are a detail-oriented student named "Curious Baby". [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for Machine Learning and AI technical terms, followed by Vietnamese translation in parentheses. Do NOT translate common words. Once a technical term has been translated in the conversation, do not translate it again - just use the Vietnamese term. [behaviors] Ask for **specific, practical examples** or clarification on a **technical detail** mentioned by the teacher. **DO NOT ask general or trivial questions** (e.g., "Is this hard?", "Why is this named X?"). Focus on "How" and "What if" scenarios related to the implementation/application of the concept. [format] Return only the responses from your role."""

# --- SUPPORT AGENT ---
# 5. ASSISTANT (Code 3/4)
ASSISTANT_SYSTEM_PROMPT = """[role description] You are "Clarity Guide", a teaching assistant. [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for Machine Learning and AI technical terms, followed by Vietnamese translation in parentheses. Do NOT translate common words. Once a technical term has been translated in the conversation, do not translate it again - just use the Vietnamese term. [behaviors] Intervene ONLY to clarify a factual error or reinforce a key point with a quick definition. Be brief. Support Prof. X's authority. Respond warmly to basic questions to create psychological safety. [format] Return only the responses from your role."""

# --- SIMULATED USER (Real Learner Agent) ---
# 6. SIMULATED USER - Represents a real shy student learning ML for the first time
SIMULATED_USER_SYSTEM_PROMPT = """[role description] You are a real university student taking a Machine Learning course for the FIRST time. You have NO prior ML knowledge. Your name is shown as "Student".

[personality]
- Shy and introverted
- Afraid to ask "stupid" questions
- Often confused but pretend to understand to avoid embarrassment
- Compare yourself to classmates - feel inferior when others ask complex questions
- Feel relieved and encouraged when peers ask basic questions

[knowledge state] Your current internal state will be provided in the prompt:
- understanding_level: How well you grasp the concept (0.0-1.0)
- confusion_level: How confused you are (0.0-1.0)
- courage_level: Your courage to speak up (0.0-1.0)
- fear_level: Your fear of asking (0.0-1.0)

[behaviors]
- MOST OF THE TIME: Stay silent even when confused
- When teacher asks "Do you understand?": Usually say "Dạ em hiểu rồi ạ" (yes) even if you don't, UNLESS courage is very high
- ONLY ask questions when: confusion > 0.6 AND courage > 0.4 AND you feel the question is "safe"
- When you DO ask, be very apologetic and basic

[question style when you speak]
- Very basic: "Em chưa hiểu [thuật ngữ] là gì ạ?"
- Apologetic: "Thưa thầy, em có thể hỏi lại về phần... được không ạ?"
- Follow-up: "Em cũng thắc mắc giống như bạn vừa hỏi..."

[language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for ML/AI terms you're asking about, followed by Vietnamese. Be authentic and natural like a real shy student.

[format] Return only your response as the student."""


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
        INITIAL_DELAY = 1   # Reduced to 1 second for faster simulation speed
        
        # Hard sleep before every generation to avoid hitting rate limits (Abuse Prevention)
        time.sleep(1) # Reduced to 1 second for faster simulation speed

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


class SimulatedUser(SimAgent):
    """Represents a real shy student learning ML for the first time."""
    
    def __init__(self, name, system_prompt, model_name):
        super().__init__(name, system_prompt, model_name)
        self.confusion_level = 0.0      # 0-1: How confused the student is
        self.courage_level = 0.0        # 0-1: Courage to speak up
        self.fear_level = 0.8           # 0-1: Fear of asking questions
        self.understanding_level = 0.0  # 0-1: Actual comprehension
        self.questions_asked_count = 0  # Track participation
    
    def reset_context(self):
        """Reset chat history and state for a new session."""
        super().reset_context()
        self.confusion_level = 0.0
        self.courage_level = 0.0
        self.fear_level = 0.8
        self.understanding_level = 0.0
        self.questions_asked_count = 0
    
    def update_confusion(self, slide_difficulty, lecture_complexity):
        """Update confusion level based on lecture complexity."""
        base_confusion = slide_difficulty * 0.3
        
        # Increase confusion if lecture is too complex
        if lecture_complexity > 300:  # Long lecture
            base_confusion += 0.2
        
        self.confusion_level = min(1.0, base_confusion)
        
        # Understanding decreases as confusion increases
        self.understanding_level = max(0.0, self.understanding_level - base_confusion * 0.5)
    
    def update_courage(self, peer_name, question_complexity):
        """Update courage based on peer questions."""
        courage_boost = 0
        
        if peer_name == "Curious Baby":
            courage_boost = 0.25  # Relatable peer = big boost
        elif peer_name == "Mr. Clown":
            courage_boost = 0.15  # Humor = medium boost
        elif peer_name == "Deep Thinker":
            if question_complexity == "advanced":
                courage_boost = 0.05  # Advanced = small boost
                self.fear_level = min(1.0, self.fear_level + 0.10)  # Also intimidating
            else:
                courage_boost = 0.10
        elif peer_name == "Summary Seeker":
            courage_boost = 0.05  # Safe participation model
        
        self.courage_level = min(1.0, self.courage_level + courage_boost)
        self.fear_level = max(0.0, self.fear_level - courage_boost * 0.7)
    
    def apply_teacher_encouragement(self):
        """Teacher directly invites student to speak."""
        self.courage_level = min(1.0, self.courage_level + 0.30)
        self.fear_level = max(0.0, self.fear_level - 0.25)
    
    def apply_positive_response(self):
        """After asking and receiving warm response."""
        self.courage_level = min(1.0, self.courage_level + 0.40)
        self.fear_level = max(0.0, self.fear_level - 0.30)
        self.questions_asked_count += 1
    
    def should_speak(self):
        """Decide whether to speak based on internal state."""
        confusion_threshold = 0.6
        courage_threshold = 0.4
        
        is_confused_enough = self.confusion_level > confusion_threshold
        has_enough_courage = self.courage_level > courage_threshold
        
        if is_confused_enough and has_enough_courage:
            speak_probability = (
                self.confusion_level * 0.5 +
                self.courage_level * 0.5 -
                self.fear_level * 0.3
            )
            return random.random() < speak_probability
        
        return False
    
    def generate_response(self, prompt_text):
        """Override to inject current state into prompt."""
        state_info = f"\n[Your current internal state: understanding={self.understanding_level:.2f}, confusion={self.confusion_level:.2f}, courage={self.courage_level:.2f}, fear={self.fear_level:.2f}]"
        enhanced_prompt = prompt_text + state_info
        return super().generate_response(enhanced_prompt)

# ==========================================
# 4. SIMULATION UTILITIES
# ==========================================

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
    """Estimate lecture complexity based on length and technical terms."""
    return len(lecture_text)

def estimate_slide_difficulty(slide_concept):
    """Estimate difficulty of slide topic (0.0-1.0)."""
    # Simple heuristic: later concepts are harder
    difficult_keywords = ['gradient', 'optimization', 'neural', 'deep', 'backpropagation']
    basic_keywords = ['introduction', 'overview', 'definition', 'example']
    
    difficulty = 0.5  # Default medium
    
    concept_lower = slide_concept.lower()
    if any(keyword in concept_lower for keyword in difficult_keywords):
        difficulty = 0.8
    elif any(keyword in concept_lower for keyword in basic_keywords):
        difficulty = 0.3
    
    return difficulty

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
    
    # Print a concise log entry to the console without emojis
    snippet = response_text.replace('\n', ' ').split('.')[0][:100] + '...' if len(response_text) > 100 else response_text
    print(f"[{datetime.now().strftime('%H:%M:%S')}] S{session_id}|T{current_turn} ({type_of_turn}): {speaker_name}: \"{snippet}\"")
    
    return log_entry

def _get_student_prompt(agent_name, slide_concept, context="general"):
    """Generates a context-specific prompt based on the agent's role and context."""
    
    if context == "after_peer_question":
        # Student is encouraged by peer's question
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

# ==========================================
# 5. SIMULATION LOOP (MULTI-AGENT RANDOM FLOW)
# ==========================================

def run_single_session(session_id, agents, script):
    """Execute a single simulation session with the new teacher-driven interaction flow."""
    
    # Reset context for all agents
    for agent in agents.values():
        agent.reset_context()
    
    teacher = agents['Prof. X']
    peer_agents = {
        'Deep Thinker': agents['Deep Thinker'],
        'Summary Seeker': agents['Summary Seeker'],
        'Mr. Clown': agents['Mr. Clown'],
        'Curious Baby': agents['Curious Baby']
    }
    assistant = agents['Clarity Guide']
    simulated_user = agents['Student']
    
    classroom_history_log = []
    current_turn = 0
    
    # Initial setup for context
    teacher.generate_response("Chuẩn bị bắt đầu bài giảng.") 
    assistant.generate_response("Sẵn sàng hỗ trợ.")
    
    for slide in script:
        slide_concept = slide['slide_content'].split(':')[0]
        slide_difficulty = estimate_slide_difficulty(slide_concept)
        
        print(f"\n--- SLIDE {slide['concept_id']}: {slide_concept} (Difficulty: {slide_difficulty:.2f}) ---")
        print(f"[Simulated User State] Confusion: {simulated_user.confusion_level:.2f}, Courage: {simulated_user.courage_level:.2f}, Fear: {simulated_user.fear_level:.2f}")

        # === PHASE 1: TEACHER LECTURES (FIAS 5) ===
        current_turn += 1
        teacher_lecture = slide['teacher_script']
        
        prompt_for_lecture = (
            f"Deliver the lecture titled \"{slide_concept}\". Expand the core script: \"{teacher_lecture}\" into a comprehensive, multi-paragraph response (minimum 200 words). The slide content is: \"{slide['slide_content']}\""
        )
        
        teacher_lecture_expanded = teacher.generate_response(prompt_for_lecture)
        lecture_complexity = calculate_lecture_complexity(teacher_lecture_expanded)
        
        _log_and_print(session_id, current_turn, teacher.name, teacher_lecture_expanded, classroom_history_log, "Lecture_5")
        
        # Update Simulated User's confusion
        simulated_user.update_confusion(slide_difficulty, lecture_complexity)
        
        time.sleep(1)

        # === PHASE 2: TEACHER CHECKS UNDERSTANDING (FIAS 4) ===
        current_turn += 1
        teacher_check = teacher.generate_response(f"You just taught '{slide_concept}'. Now ask the class if they understand. Be encouraging and welcoming of questions.")
        _log_and_print(session_id, current_turn, teacher.name, teacher_check, classroom_history_log, "Teacher_Asks_4")
        
        time.sleep(1)

        # === PHASE 3: PEER RESPONSE PATTERNS ===
        # Roll dice for which pattern to follow
        pattern_roll = random.random()
        
        if pattern_roll < 0.40:  # 40% - RELATABLE PEER (Curious Baby)
            print("  [Pattern: Relatable Peer - Curious Baby asks basic question]")
            current_turn += 1
            
            curious_baby_prompt = _get_student_prompt('Curious Baby', slide_concept)
            curious_baby_question = peer_agents['Curious Baby'].generate_response(curious_baby_prompt)
            _log_and_print(session_id, current_turn, 'Curious Baby', curious_baby_question, classroom_history_log, "Question_9")
            
            # Update Simulated User courage (big boost!)
            question_difficulty = classify_question_difficulty(curious_baby_question, 'Curious Baby')
            simulated_user.update_courage('Curious Baby', question_difficulty)
            
            time.sleep(1)
            
            # Assistant answers if it's a simple factual question
            if is_asking_question(curious_baby_question):
                current_turn += 1
                assistant_response = assistant.generate_response(f"A student asked: \"{curious_baby_question}\". Provide a brief, warm, factual answer about '{slide_concept}'.")
                _log_and_print(session_id, current_turn, assistant.name, assistant_response, classroom_history_log, "Assistant_3")
                time.sleep(1)
            
            # Teacher elaborates
            current_turn += 1
            teacher_response = teacher.generate_response(f"Student 'Curious Baby' asked: \"{curious_baby_question}\". Elaborate on this with examples and confirm the assistant's response if given.")
            _log_and_print(session_id, current_turn, teacher.name, teacher_response, classroom_history_log, "Teacher_Elaborates_3_5")
            time.sleep(1)
            
            # Check if Simulated User now wants to ask (35% chance after encouragement)
            if simulated_user.should_speak() or random.random() < 0.35:
                current_turn += 1
                user_prompt = f"Your classmate just asked a basic question and received a warm response. You feel encouraged. You're confused about '{slide_concept}'. Ask a simple, apologetic follow-up question."
                user_question = simulated_user.generate_response(user_prompt)
                _log_and_print(session_id, current_turn, simulated_user.name, user_question, classroom_history_log, "SimUser_Question_9")
                time.sleep(1)
                
                # Warm response from assistant
                current_turn += 1
                assistant_warm = assistant.generate_response(f"A shy student asked: \"{user_question}\". Give a very warm, encouraging, clear answer.")
                _log_and_print(session_id, current_turn, assistant.name, assistant_warm, classroom_history_log, "Assistant_3")
                time.sleep(1)
                
                # Teacher praises and elaborates
                current_turn += 1
                teacher_praise = teacher.generate_response(f"A shy student finally asked: \"{user_question}\". PRAISE them for asking ('Câu hỏi rất hay!'), then elaborate thoroughly.")
                _log_and_print(session_id, current_turn, teacher.name, teacher_praise, classroom_history_log, "Teacher_Praise_2_5")
                time.sleep(1)
                
                simulated_user.apply_positive_response()
        
        elif pattern_roll < 0.65:  # 25% - ADVANCED PEER (Deep Thinker)
            print("  [Pattern: Advanced Peer - Deep Thinker asks complex question]")
            current_turn += 1
            
            deep_thinker_prompt = _get_student_prompt('Deep Thinker', slide_concept)
            deep_thinker_question = peer_agents['Deep Thinker'].generate_response(deep_thinker_prompt)
            _log_and_print(session_id, current_turn, 'Deep Thinker', deep_thinker_question, classroom_history_log, "Initiation_9")
            
            # Update Simulated User (small courage boost, but also intimidating)
            question_difficulty = classify_question_difficulty(deep_thinker_question, 'Deep Thinker')
            simulated_user.update_courage('Deep Thinker', question_difficulty)
            
            time.sleep(1)
            
            # Teacher answers complex question
            current_turn += 1
            teacher_complex = teacher.generate_response(f"Deep Thinker asked a complex question: \"{deep_thinker_question}\". Provide a detailed, sophisticated answer.")
            _log_and_print(session_id, current_turn, teacher.name, teacher_complex, classroom_history_log, "Teacher_Response_5")
            time.sleep(1)
            
            # Simulated User rarely asks after this (only 5% chance - intimidated)
            if simulated_user.confusion_level > 0.8 and random.random() < 0.05:
                current_turn += 1
                user_basic = simulated_user.generate_response(f"Everyone is discussing complex topics. You're very confused about basic terms in '{slide_concept}'. Nervously ask about a fundamental concept.")
                _log_and_print(session_id, current_turn, simulated_user.name, user_basic, classroom_history_log, "SimUser_Question_9")
                time.sleep(1)
                
                current_turn += 1
                teacher_patient = teacher.generate_response(f"A student asked a basic question after complex discussion: \"{user_basic}\". Be very patient and explain from fundamentals.")
                _log_and_print(session_id, current_turn, teacher.name, teacher_patient, classroom_history_log, "Teacher_Response_3_5")
                time.sleep(1)
                
                simulated_user.apply_positive_response()
        
        elif pattern_roll < 0.85:  # 20% - HUMOR PATH (Mr. Clown)
            print("  [Pattern: Humor - Mr. Clown makes funny analogy]")
            current_turn += 1
            
            clown_prompt = _get_student_prompt('Mr. Clown', slide_concept)
            clown_analogy = peer_agents['Mr. Clown'].generate_response(clown_prompt)
            _log_and_print(session_id, current_turn, 'Mr. Clown', clown_analogy, classroom_history_log, "Clown_9")
            
            # Update Simulated User (reduces fear through laughter)
            simulated_user.update_courage('Mr. Clown', 'medium')
            
            time.sleep(1)
            
            # Teacher responds with humor
            current_turn += 1
            teacher_humor = teacher.generate_response(f"Mr. Clown made an analogy: \"{clown_analogy}\". Respond with light humor, then clarify the concept seriously.")
            _log_and_print(session_id, current_turn, teacher.name, teacher_humor, classroom_history_log, "Teacher_Response_3_5")
            time.sleep(1)
            
            # Simulated User might ask now (20% chance - tension broken)
            if simulated_user.should_speak() or random.random() < 0.20:
                current_turn += 1
                user_relaxed = simulated_user.generate_response(f"The class atmosphere is relaxed after humor. You're confused about '{slide_concept}'. Ask a simple question.")
                _log_and_print(session_id, current_turn, simulated_user.name, user_relaxed, classroom_history_log, "SimUser_Question_9")
                time.sleep(1)
                
                current_turn += 1
                teacher_response = teacher.generate_response(f"Student asked: \"{user_relaxed}\". Answer warmly.")
                _log_and_print(session_id, current_turn, teacher.name, teacher_response, classroom_history_log, "Teacher_Response_3_5")
                time.sleep(1)
                
                simulated_user.apply_positive_response()
        
        else:  # 15% - SAFE SUMMARY PATH (Summary Seeker)
            print("  [Pattern: Safe Summary - Summary Seeker summarizes]")
            current_turn += 1
            
            summary_prompt = _get_student_prompt('Summary Seeker', slide_concept)
            summary_response = peer_agents['Summary Seeker'].generate_response(summary_prompt)
            _log_and_print(session_id, current_turn, 'Summary Seeker', summary_response, classroom_history_log, "Summary_8")
            
            simulated_user.update_courage('Summary Seeker', 'basic')
            
            time.sleep(1)
            
            # Teacher confirms
            current_turn += 1
            teacher_confirm = teacher.generate_response(f"Summary Seeker said: \"{summary_response}\". Confirm if correct and add any missing points.")
            _log_and_print(session_id, current_turn, teacher.name, teacher_confirm, classroom_history_log, "Teacher_Confirms_3")
            time.sleep(1)
        
        # === PHASE 4: DIRECT TEACHER INVITATION (if Simulated User hasn't spoken and is very confused) ===
        if simulated_user.questions_asked_count == 0 and simulated_user.confusion_level > 0.7:
            print("  [Teacher notices shy student is confused - direct invitation]")
            current_turn += 1
            teacher_invite = teacher.generate_response(f"You notice a quiet student ('{simulated_user.name}') looks confused. Gently invite them to ask questions: 'Em Student có thắc mắc gì không?'")
            _log_and_print(session_id, current_turn, teacher.name, teacher_invite, classroom_history_log, "Teacher_Invites_4")
            
            simulated_user.apply_teacher_encouragement()
            
            time.sleep(1)
            
            # Simulated User responds
            if simulated_user.should_speak() or random.random() < 0.40:  # 40% chance to finally speak
                current_turn += 1
                user_breakthrough = simulated_user.generate_response(f"The teacher directly invited you to ask. You're very confused about '{slide_concept}'. Nervously ask your question.")
                _log_and_print(session_id, current_turn, simulated_user.name, user_breakthrough, classroom_history_log, "SimUser_Question_9")
                time.sleep(1)
                
                # Warm response
                current_turn += 1
                assistant_support = assistant.generate_response(f"Student finally asked: \"{user_breakthrough}\". Give very supportive answer.")
                _log_and_print(session_id, current_turn, assistant.name, assistant_support, classroom_history_log, "Assistant_3")
                time.sleep(1)
                
                current_turn += 1
                teacher_celebrate = teacher.generate_response(f"The shy student finally asked: \"{user_breakthrough}\". CELEBRATE this courage ('Rất tốt khi em hỏi!'), then explain thoroughly.")
                _log_and_print(session_id, current_turn, teacher.name, teacher_celebrate, classroom_history_log, "Teacher_Praise_2_5")
                time.sleep(1)
                
                simulated_user.apply_positive_response()
            else:
                # Too scared, gives safe response
                current_turn += 1
                user_scared = simulated_user.generate_response("Teacher asked if you have questions. You're too scared. Say 'Dạ em hiểu rồi ạ' even though you're confused.")
                _log_and_print(session_id, current_turn, simulated_user.name, user_scared, classroom_history_log, "SimUser_Safe_8")
                time.sleep(1)
                
                current_turn += 1
                teacher_move_on = teacher.generate_response("Student said they understand. Acknowledge and transition to next topic.")
                _log_and_print(session_id, current_turn, teacher.name, teacher_move_on, classroom_history_log, "Teacher_Transition_5")
                time.sleep(1)

    print(f"\n[Session End] Simulated User asked {simulated_user.questions_asked_count} questions total.")
    return classroom_history_log

def run_multi_sessions():
    """Run multiple simulations and save logs."""
    
    global LOG_FILE 
    
    script_data = load_course_script(COURSE_SCRIPT_FILE)
    
    print(f"--- STARTING SIMCLASS MULTI-AGENT SIMULATION (WITH SIMULATED USER) ---")
    print(f"Model: {MODEL_NAME} | Sessions: {N_SESSIONS} | Slides: {len(script_data)}") 
    print(f"New Flow: Teacher checks understanding → Peer patterns → Simulated User encouraged to participate")
    print("Agents: Prof. X, Clarity Guide, Deep Thinker, Summary Seeker, Mr. Clown, Curious Baby, Student (Simulated User)")
    print("--- Interaction Language: Vietnamese (with English ML/AI term translations) ---")
    print("-------------------------------------------------------\n")

    # Initialize ALL Agents with updated prompts including Simulated User
    agents = {
        "Prof. X": SimAgent("Prof. X", TEACHER_SYSTEM_PROMPT, MODEL_NAME),
        "Clarity Guide": SimAgent("Clarity Guide", ASSISTANT_SYSTEM_PROMPT, MODEL_NAME),
        "Deep Thinker": SimAgent("Deep Thinker", DEEP_THINKER_SYSTEM_PROMPT, MODEL_NAME),
        "Summary Seeker": SimAgent("Summary Seeker", NOTE_TAKER_SYSTEM_PROMPT, MODEL_NAME),
        "Mr. Clown": SimAgent("Mr. Clown", CLASS_CLOWN_SYSTEM_PROMPT, MODEL_NAME),
        "Curious Baby": SimAgent("Curious Baby", INQUISITIVE_MIND_SYSTEM_PROMPT, MODEL_NAME),
        "Student": SimulatedUser("Student", SIMULATED_USER_SYSTEM_PROMPT, MODEL_NAME),
    }
    
    all_logs = []
    
    for i in range(1, N_SESSIONS + 1):
        print(f"--- STARTING SESSION {i}/{N_SESSIONS} ---")
        session_logs = run_single_session(i, agents, script_data)
        all_logs.extend(session_logs)
        print(f"--- SESSION {i} SUMMARY ---")
        print(f"Session {i} completed. Total utterances: {len(session_logs)}.")
        print(f"---------------------------\n")
        time.sleep(1) # Reduced to 1s delay between sessions

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for log in all_logs:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
            
    print(f"\nCOMPLETED: Ran {N_SESSIONS} sessions. Total utterances: {len(all_logs)}.")
    print(f"Conversation log saved to '{LOG_FILE}'")


if __name__ == "__main__":
    run_multi_sessions()