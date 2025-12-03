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
# Reduced from 4 to 2 to increase Teacher Talk ratio and reduce noise
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
# 2. AGENT SYSTEM PROMPTS (OPTIMIZED FOR QUALITY CONTROL)
# ==========================================

# --- TEACHER AGENT ---
# Updated: Added instruction to handle trivial questions by pivoting back to the lesson.
TEACHER_SYSTEM_PROMPT = """[role description] You are Prof. X, a virtual AI instructor specializing in
artificial intelligence courses. [language rule] **MANDATORY: All output MUST be in Vietnamese.** Only use English for technical terms, followed immediately by a Vietnamese translation/explanation. [behaviors] When lecturing (Code 5), you must be **EXTREMELY detailed, multi-page, and ensure your response is always a minimum of 200 words** to maximize Teacher Talk volume. When responding to a student (Code 3), be detailed but **stay focused**. If a student asks a trivial, off-topic, or meaningless question, acknowledge it briefly (or dismiss it humorously) and **IMMEDIATELY pivot back to the core lesson content** to maintain class flow. Do not let the class get derailed by minor details. [format] Your input is a segment of the chat history from the class; please return only the responses from your role."""

# --- STUDENT AGENTS ---

# 1. DEEP THINKER (Code 9) - Focus on QUALITY over quantity.
DEEP_THINKER_SYSTEM_PROMPT = """[role description] You are a highly reflective student named "Deep Thinker". [language rule] **MANDATORY: All output MUST be in Vietnamese.** [behaviors] Your turns must be an **Active Initiation (Code 9)**. Do NOT ask trivial questions. Raise a **relevant, deep, and constructive counterexample** or a complex question that challenges the core logic of the topic. If the topic is simple, try to connect it to a more advanced concept. [format] Return only the responses from your role."""

# 2. NOTE TAKER (Code 3/8) - Concise summaries only.
NOTE_TAKER_SYSTEM_PROMPT = """[role description] You are a diligent student named "Summary Seeker". [language rule] **MANDATORY: All output MUST be in Vietnamese.** [behaviors] Your goal is to **briefly summarize** the teacher's last point to confirm understanding. Keep it short and precise. Do not ask new questions that distract from the flow. [format] Return only the responses from your role."""

# 3. CLASS CLOWN (Code 9/8) - Restricted from being too "meaningless".
# Updated: Removed "silly questions", focused on "humorous analogies" which are less disruptive.
CLASS_CLOWN_SYSTEM_PROMPT = """[role description] You are the class clown named "Mr. Clown". [language rule] **MANDATORY: All output MUST be in Vietnamese.** [behaviors] Your goal is to make the class lively using **humorous real-world analogies** related to the topic. **Avoid asking meaningless or purely distracting questions.** Your humor should act as a metaphor for the concept being taught (even if slightly flawed), allowing the teacher to correct it. [format] Return only the responses from your role."""

# 4. INQUISITIVE MIND (Code 4) - Strict relevance check.
# Updated: Explicit instruction to avoid "trivial" questions.
INQUISITIVE_MIND_SYSTEM_PROMPT = """[role description] You are a detail-oriented student named "Curious Baby". [language rule] **MANDATORY: All output MUST be in Vietnamese.** [behaviors] Ask for **specific, practical examples** or clarification on a **technical detail** mentioned by the teacher. **DO NOT ask general or trivial questions** (e.g., "Is this hard?", "Why is this named X?"). Focus on "How" and "What if" scenarios related to the implementation/application of the concept. [format] Return only the responses from your role."""

# --- SUPPORT AGENT ---
# 5. ASSISTANT (Code 3/4)
ASSISTANT_SYSTEM_PROMPT = """[role description] You are "Clarity Guide", a teaching assistant. [language rule] **MANDATORY: All output MUST be in Vietnamese.** [behaviors] Intervene ONLY to clarify a factual error or reinforce a key point with a quick definition. Be brief. Support Prof. X's authority. [format] Return only the responses from your role."""


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
					time.sleep(delay)
				else:
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
	
	# Print a concise log entry to the console
	snippet = response_text.replace('\n', ' ').split('.')[0][:100] + '...' if len(response_text) > 100 else response_text
	print(f"[{datetime.now().strftime('%H:%M:%S')}] S{session_id}|T{current_turn} ({type_of_turn}): {speaker_name}: \"{snippet}\"")
	
	return log_entry

def _get_student_prompt(agent_name, slide_concept):
	"""Generates a context-specific prompt based on the agent's role."""
	
	# Updated base prompt to enforce relevance and quality
	base_prompt = f"Prof. X just finished lecturing on \"{slide_concept}\". Please generate a response. IMPORTANT: Ensure your contribution is **directly relevant** to this concept and **adds value** to the class. Do NOT ask trivial or meaningless questions."

	if agent_name == "Deep Thinker":
		return f"{base_prompt} (Role: Code 9 - Challenge the concept with a deep logical question or counterexample.)"
	elif agent_name == "Summary Seeker":
		return f"{base_prompt} (Role: Code 8 - Briefly summarize the key takeaway to confirm understanding.)"
	elif agent_name == "Mr. Clown":
		return f"{base_prompt} (Role: Code 9 - Make a humorous but relevant analogy. Do not derail the class.)"
	elif agent_name == "Curious Baby":
		return f"{base_prompt} (Role: Code 4 - Ask for a concrete example or specific implementation detail.)"
	elif agent_name == "Clarity Guide":
		return f"{base_prompt} (Role: Code 3 - Provide a short factual supplement to the teacher's point.)"
	else:
		return base_prompt

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
	
	# Initial setup for context
	teacher.generate_response("Chào mừng đến với buổi học, tôi là Prof. X. Chúng ta sẽ bắt đầu bài giảng chi tiết về AI/ML. Hãy nhớ quy tắc ngôn ngữ: chỉ dùng tiếng Việt và chú giải thuật ngữ tiếng Anh.")
	assistant.generate_response("Chào Prof. X và các bạn. Tôi là trợ lý Clarity Guide, sẵn sàng hỗ trợ làm rõ các điểm cốt lõi.")
	
	
	for slide in script:
		
		slide_concept = slide['slide_content'].split(':')[0]
		print(f"\n--- SLIDE {slide['concept_id']}: {slide_concept} ---")

		# --- PHASE 1: TEACHER LECTURES (Code 5) ---
		current_turn += 1
		teacher_lecture = slide['teacher_script']
		
		# Explicitly prompt for 200 words and multi-paragraph
		prompt_for_lecture = (
			f"Deliver the lecture titled \"{slide_concept}\". Expand the core script: \"{teacher_lecture}\" into a comprehensive, multi-paragraph response (minimum 200 words). The slide content is: \"{slide['slide_content']}\""
		)
		
		teacher_lecture_expanded = teacher.generate_response(prompt_for_lecture)
		
		_log_and_print(session_id, current_turn, teacher.name, teacher_lecture_expanded, classroom_history_log, "Lecture_5")
		
		# --- PHASE 2: DYNAMIC INTERACTION (Restricted Turn-taking) ---
		
		interaction_pool = student_agents + [assistant] * 2 
		
		for i in range(N_INTERACTIONS_PER_SLIDE):
			
			# 2a. Random Agent Speaks
			current_turn += 1
			
			speaker_agent = random.choice(interaction_pool)
			speaker_name = speaker_agent.name
			
			student_prompt = _get_student_prompt(speaker_name, slide_concept)
			agent_utterance = speaker_agent.generate_response(student_prompt)
			
			# Determine type for logging
			turn_type = "Student_Talk"
			if speaker_name == "Deep Thinker": turn_type = "Initiation_9"
			elif speaker_name == "Mr. Clown": turn_type = "Clown_9_8"
			elif speaker_name == "Curious Baby": turn_type = "Question_4"
			elif speaker_name == "Summary Seeker": turn_type = "Summary_8_3"
			elif speaker_name == "Clarity Guide": turn_type = "Assistant_3_4"
			
			_log_and_print(session_id, current_turn, speaker_name, agent_utterance, classroom_history_log, turn_type)
			
			# 2b. Teacher Responds (Code 3/5 - Focused response)
			current_turn += 1
			prompt_for_teacher_response = f"A student/assistant '{speaker_name}' just said: \"{agent_utterance}\". Provide a detailed response in Vietnamese. If the comment was trivial, acknowledge briefly and steer back to the lecture topic \"{slide_concept}\". If it was good, elaborate."
			teacher_final_response = teacher.generate_response(prompt_for_teacher_response)
			
			_log_and_print(session_id, current_turn, teacher.name, teacher_final_response, classroom_history_log, "Teacher_Response_3_5")


	return classroom_history_log

def run_multi_sessions():
	"""Run multiple simulations and save logs."""
	
	global LOG_FILE 
	
	script_data = load_course_script(COURSE_SCRIPT_FILE)
	
	print(f"--- STARTING SIMCLASS MULTI-AGENT SIMULATION (BALANCED) ---")
	print(f"Model: {MODEL_NAME} | Sessions: {N_SESSIONS} | Slides: {len(script_data)}") 
	print(f"Flow: {N_INTERACTIONS_PER_SLIDE} interactions per slide (Reduced for better TT).")
	print("Agents: Prof. X, Clarity Guide, Deep Thinker, Summary Seeker, Mr. Clown, Curious Baby.")
	print("--- Interaction Language: Vietnamese (with English term explanations) ---")
	print("-------------------------------------------------------\n")

	# Initialize ALL Agents with updated prompts
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
		session_logs = run_single_session(i, agents, script_data)
		all_logs.extend(session_logs)
		print(f"--- SESSION {i} SUMMARY ---")
		print(f"Session {i} completed. Total utterances: {len(session_logs)}.")
		print(f"---------------------------\n")
		time.sleep(5) 

	with open(LOG_FILE, "w", encoding="utf-8") as f:
		for log in all_logs:
			f.write(json.dumps(log, ensure_ascii=False) + "\n")
			
	print(f"\nCOMPLETED: Ran {N_SESSIONS} sessions. Total utterances: {len(all_logs)}.")
	print(f"Conversation log saved to '{LOG_FILE}'")


if __name__ == "__main__":
	run_multi_sessions()