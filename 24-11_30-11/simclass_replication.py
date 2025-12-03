import google.generativeai as genai
import json
import time
import os
import random 
from datetime import datetime

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Replace "YOUR_API_KEY" with your key
GOOGLE_API_KEY = "AIzaSyDLKsILJJD7IM0mpV9f_lxnN0DgnfY4MoA" 
N_SESSIONS = 5  # Number of simulation runs (Increase to 15 for final results)

# --- DYNAMIC FLOW CONFIGURATION (V4) ---
# Total interaction probability: 1.0 - NO_INTERACTION_PROBABILITY
NO_INTERACTION_PROBABILITY = 0.15 # 15% chance of a silent turn (skips student response)
# The remaining 85% of turns are active interactions, split below:
# 80% of active interactions: Student Initiation (Code 9 -> Code 3) -> Maximize SIR
INITIATION_PROBABILITY_OF_ACTIVE = 0.80 

# --- TIMESTAMP UPDATE ---
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"simulation_log_structured_{TIMESTAMP}.jsonl"

MODEL_NAME = "gemini-2.0-flash"

if GOOGLE_API_KEY == "YOUR_API_KEY":
    print("WARNING: API Key not set. Please set GOOGLE_API_KEY in the code.")
    if "GOOGLE_API_KEY" in os.environ:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    else:
        pass 
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# ==========================================
# 2. AGENT PROMPTS (UPDATED for extreme TT and high SIR)
# ==========================================

TEACHER_SYSTEM_PROMPT = """[role description] You are Prof. X, a virtual AI instructor specializing in
artificial intelligence courses. [behaviors] When lecturing (Code 5), you must be **EXTREMELY detailed, multi-page, and ensure your response is always a minimum of 200 words** to maximize Teacher Talk volume. When responding to a student (Code 3), be detailed and comprehensive. Always use rhetorical questions within your lecture to engage the student without requiring a direct response. If you ask a question (Code 4), ensure it is clear and factual. For difficult questions, suggest leaving them for later. [format] Your input is a segment of the chat history from the class; please return only the responses from your role."""

DEEP_THINKER_SYSTEM_PROMPT = """[role description] You are a classroom assistant named "Deep Thinker", responsible for critical reflection and active participation. [behaviors] Your primary goal is to simulate realistic student behavior. You are strongly encouraged to use **Active Initiation (Code 9)**.
1. **Passive Response (Code 8):** If Prof. X asks a specific, closed, or factual question, you must respond directly and concisely in Vietnamese.
2. **Active Initiation (Code 9):** If Prof. X is lecturing, or after a detailed response, you must raise a relevant and constructive counterexample or complex, open-ended question in Vietnamese. 
Your default behavior when not directly questioned is Code 9.
[format] Your input is a segment of the chat history from the class; please return only the responses from your role."""

# Course script (No changes to content)
course_script = [
    {
        "concept_id": 1,
        "slide_content": "## 1. Bức tranh lớn: AI vs. ML vs. Deep Learning\n\n* **AI (Trí tuệ nhân tạo):** Khái niệm bao trùm. Máy tính thực hiện các tác vụ thông minh.\n* **ML (Học máy):** Tập con của AI. Máy tính tự học luật từ dữ liệu thay vì được lập trình cứng (Hard-coded).\n* **Deep Learning (Học sâu):** Tập con của ML. Sử dụng mạng nơ-ron đa lớp để học các đặc trưng phức tạp (như mắt, mũi trong ảnh).\n\n**Analogy:** AI là vũ trụ, ML là hệ mặt trời, và Deep Learning là trái đất.",
        "teacher_script": "Chào cả lớp. Trước khi đi vào chi tiết, chúng ta cần định vị mình đang ở đâu trên bản đồ công nghệ. Nhiều bạn hay nhầm lẫn AI và ML là một. Thực ra, AI là giấc mơ lớn về những cỗ máy thông minh. Còn Machine Learning là phương pháp cụ thể để hiện thực hóa giấc mơ đó bằng Dữ liệu. Hôm nay chúng ta tập trung vào 'Hệ mặt trời' ML này. (Phần này sẽ được mở rộng thêm tối thiểu 200 từ trong response)."
    },
    {
        "concept_id": 2,
        "slide_content": "## 2. Giải phẫu Dữ liệu (Anatomy of Data)\n\nĐể học máy hoạt động, dữ liệu thường được chia thành 2 phần:\n\n1.  **Features (Đặc trưng - $X$):** Thông tin đầu vào.\n    * *Ví dụ:* Diện tích nhà, Số phòng ngủ, Vị trí.\n2.  **Labels (Nhãn/Mục tiêu - $y$):** Kết quả muốn dự đoán.\n    * *Ví dụ:* Giá nhà (2 tỷ, 5 tỷ).\n\n**Chìa khóa:** Sự khác biệt giữa Supervised và Unsupervised nằm ở việc **chúng ta có $y$ hay không**.",
        "teacher_script": "Đây là slide quan trọng nhất bài. Mọi thuật toán ML đều xoay quanh $X$ và $y$. Hãy tưởng tượng các em đang bán nhà. Khách hàng hỏi: 'Nhà này bao nhiêu tiền?'. Để trả lời, em nhìn vào diện tích, số phòng, vị trí - đó là $X$ (Features). Con số '5 tỷ' em chốt lại chính là $y$ (Label). Việc chuẩn hóa và lựa chọn Features là công đoạn tốn thời gian nhất trong mọi dự án. (Phần này sẽ được mở rộng thêm tối thiểu 200 từ trong response)."
    },
    {
        "concept_id": 3,
        "slide_content": "## 3. Supervised Learning: Học có Giám sát\n\n**Cơ chế:** Dạy học kèm cặp (Teacher-Student).\n* **Input:** Dữ liệu có gắn nhãn $(X, y)$.\n* **Process:** Máy đoán $\\hat{y}$, so sánh với đáp án thật $y$, và sửa lỗi (Error correction).\n* **Goal:** Tìm hàm $f$ sao cho $y \\approx f(X)$ để áp dụng cho $X$ mới chưa biết $y$.",
        "teacher_script": "Hãy tưởng tượng Supervised Learning giống như luyện thi đại học. Thầy đưa bài tập ($X$) kèm theo đáp án chi tiết ($y$). Các em làm bài, so sánh với đáp án, thấy sai thì sửa lại kiến thức trong đầu. Quá trình này lặp lại hàng nghìn lần. Đây là nền tảng của hầu hết các mô hình dự đoán thương mại hiện nay. (Phần này sẽ được mở rộng thêm tối thiểu 200 từ trong response)."
    },
    {
        "concept_id": 4,
        "slide_content": "## 4. Supervised Task A: Classification (Phân loại)\n\n**Đặc điểm:** Label $y$ là rời rạc (Discrete/Categories).\n\n* **Binary:** Chỉ có 2 lớp (Có/Không, 0/1).\n    * *Ví dụ:* Email là Spam hay Inbox? Khối u là Lành tính hay Ác tính?\n* **Multi-class:** Nhiều lớp.\n    * *Ví dụ:* Nhận diện chữ viết tay (số 0 đến 9).\n\n**Hình ảnh:** Một đường ranh giới (Decision Boundary) chia tách các điểm đỏ và xanh.",
        "teacher_script": "Trong Học có giám sát, nếu câu hỏi là 'Cái này thuộc nhóm nào?', đó là Phân loại. Ví dụ kinh điển là Spam Filter của Gmail. $y$ ở đây chỉ có hai giá trị: 'Rác' hoặc 'Không rác'. Máy tính sẽ vẽ một đường ranh giới vô hình. Bất cứ email nào rơi vào vùng đỏ là rác, vùng xanh là an toàn. Việc chọn thuật toán phù hợp (như Logistic Regression hay SVM) là bước tiếp theo cực kỳ quan trọng. (Phần này sẽ được mở rộng thêm tối thiểu 200 từ trong response)."
    },
    {
        "concept_id": 5,
        "slide_content": "## 5. Supervised Task B: Regression (Hồi quy)\n\n**Đặc điểm:** Label $y$ là liên tục (Continuous/Numbers).\n\n* **Câu hỏi:** 'Bao nhiêu?' (How much/How many?)\n* **Ví dụ:**\n    * Dự báo thời tiết (Nhiệt độ ngày mai là 30.5°C).\n    * Dự báo doanh thu tháng sau.\n\n**Hình ảnh:** Một đường thẳng hoặc đường cong (Line of Best Fit) đi xuyên qua các điểm dữ liệu.",
        "teacher_script": "Ngược lại, nếu câu hỏi là 'Bao nhiêu?', đó là Hồi quy. Ví dụ, em muốn biết nhiệt độ ngày mai. Nó không thể chỉ là 'Nóng' hay 'Lạnh' (Phân loại), mà phải là con số cụ thể như 32.5 độ C. Lúc này, máy tính không vẽ đường chia cắt nữa, mà vẽ một đường xu hướng đi xuyên qua dữ liệu quá khứ để dự đoán tương lai. Sai số (Error) trong Regression thường được đo bằng MSE (Mean Squared Error). (Phần này sẽ được mở rộng thêm tối thiểu 200 từ trong response)."
    },
    {
        "concept_id": 6,
        "slide_content": "## 6. Unsupervised Learning: Học không Giám sát\n\n**Cơ chế:** Tự học (Self-study).\n* **Input:** Chỉ có $X$, hoàn toàn KHÔNG có $y$.\n* **Thách thức:** Máy không biết thế nào là 'đúng' hay 'sai'.\n* **Goal:** Tìm cấu trúc ẩn (Hidden Structure) hoặc sự tương đồng trong dữ liệu.",
        "teacher_script": "Nhưng cuộc đời đâu phải lúc nào cũng có đáp án sẵn ($y$). Đó là lúc Unsupervised Learning vào cuộc. Giống như một đứa trẻ lần đầu thấy một đống đồ chơi Lego lộn xộn. Không ai bảo nó cái nào là 'gạch vuông', cái nào là 'gạch tròn'. Nhưng nó tự biết cách nhặt những miếng giống nhau để xếp thành từng đống riêng biệt. Mục đích là khám phá cấu trúc thay vì dự đoán. (Phần này sẽ được mở rộng thêm tối thiểu 200 từ trong response)."
    },
    {
        "concept_id": 7,
        "slide_content": "## 7. Unsupervised Task: Clustering (Phân cụm)\n\n**Định nghĩa:** Gom nhóm các điểm dữ liệu có đặc tính giống nhau.\n\n* **Ví dụ Marketing:** Phân khúc khách hàng.\n    * Có 1 triệu user log, không biết ai là ai.\n    * Máy tự gom: Nhóm A (Online đêm khuya, mua đồ game), Nhóm B (Online giờ hành chính, mua tã bỉm).\n    * -> Doanh nghiệp tự đặt tên cho nhóm và target quảng cáo.\n\n**Khác biệt với Classification:** Ở Classification, ta biết trước các nhóm (Spam/Not Spam). Ở Clustering, ta chưa biết có bao nhiêu nhóm và nhóm đó là gì.",
        "teacher_script": "Nhiệm vụ nổi tiếng nhất của nó là Phân cụm. Các em hãy nghĩ về Netflix. Họ không hề hỏi em 'Em thuộc nhóm khán giả nào?'. Họ chỉ âm thầm quan sát ($X$) việc em xem phim gì. Sau đó thuật toán tự động gom em vào cùng nhóm với những người có gu tương tự để gợi ý phim. Đây là ma thuật của việc tìm ra mẫu số chung trong dữ liệu hỗn loạn. K-Means là thuật toán phổ biến nhất trong lĩnh vực này. (Phần này sẽ được mở rộng thêm tối thiểu 200 từ trong response)."
    },
    {
        "concept_id": 8,
        "slide_content": "## 8. Discussion: Case Study 'Phát hiện Gian lận Ngân hàng'\n\n**Tình huống:** Ngân hàng muốn bắt các giao dịch thẻ tín dụng giả mạo.\n\n* **Cách tiếp cận A (Supervised):** Dùng lịch sử 5 năm qua, với các giao dịch đã được nhân viên đánh dấu là 'Gian lận' hoặc 'Sạch'.\n* **Cách tiếp cận B (Unsupervised):** Chỉ tìm kiếm các giao dịch có hành vi 'bất thường', khác biệt quá xa so với thói quen chi tiêu hàng ngày của khách hàng, mà không cần biết trước nó là gian lận hay không.\n\n**Câu hỏi:** Theo các em, ưu/nhược điểm của mỗi cách là gì? Ngân hàng thực tế dùng cách nào?",
        "teacher_script": "Để kết thúc, chúng ta hãy thảo luận về bài toán tỷ đô: Chống gian lận thẻ tín dụng. Ngân hàng có thể dùng cả hai cách. \n\nCách A (Supervised): Dạy máy dựa trên các vụ gian lận đã biết trong quá khứ, nhược điểm là khó phát hiện gian lận mới. \nCách B (Unsupervised): Dạy máy tìm ra những giao dịch 'kỳ quặc' (Anomaly Detection), ưu điểm là tóm được chiêu thức mới. \n\nTrong thực tế, các ngân hàng thường kết hợp cả hai để tối ưu hóa việc phát hiện. Mời các em tranh luận. (Phần này sẽ được mở rộng thêm tối thiểu 200 từ trong response)."
    }
]

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
        try:
            # Send message to the model. self.chat automatically maintains history.
            response = self.chat.send_message(prompt_text)
            return response.text.strip()
        except Exception as e:
            # Print error but return error text for logging
            print(f"Error generating response for {self.name}: {e}")
            return f"[ERROR: {e}]"

# ==========================================
# 4. SIMULATION LOOP (V4 DYNAMIC FLOW IMPLEMENTATION)
# ==========================================

def run_single_session(session_id, teacher, student, script):
    """Execute a single simulation session using the dynamic flow."""
    
    teacher.reset_context()
    student.reset_context()
    
    classroom_history_log = []
    current_turn = 0
    
    # Initial setup for context
    teacher.generate_response("You are about to start a detailed lesson on core AI/ML concepts. Remember your strict minimum word count of 200 for lectures (Code 5).")
    student.generate_response("I am ready to participate and reflect critically on the content. My default is to ask a new, deep question (Code 9).")
    
    for slide in script:
        # --- PHASE 1: TEACHER LECTURES (Expected Code 5 - FORCED EXTREME VOLUME) ---
        current_turn += 1
        teacher_lecture = slide['teacher_script']
        
        # Explicitly prompt for 200 words and multi-paragraph
        prompt_for_lecture = (
            f"Deliver the lecture titled \"{slide['slide_content'].split(':')[0]}\". Expand the core script: \"{teacher_lecture}\" into a comprehensive, multi-paragraph response (minimum 200 words). The slide content is: \"{slide['slide_content']}\""
        )
        
        teacher_lecture_expanded = teacher.generate_response(prompt_for_lecture)
        
        # Log Entry 1 - Teacher Lecture (Code 5)
        log_entry = {
            "session_id": session_id,
            "turn": current_turn,
            "speaker": teacher.name,
            "text": teacher_lecture_expanded,
            "timestamp": datetime.now().isoformat()
        }
        classroom_history_log.append(log_entry)
        time.sleep(1)
        
        # --- PHASE 2: DYNAMIC INTERACTION CHECK (Control flow for TT/ST balance) ---
        
        interaction_roll = random.random()
        
        if interaction_roll < NO_INTERACTION_PROBABILITY:
            # --- SCENARIO C (15%): SILENT TURN (Skipped interaction) ---
            print(f"Session {session_id}, Slide {slide['concept_id']}: No student interaction (Silent Turn).")
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
            log_entry = {
                "session_id": session_id,
                "turn": current_turn,
                "speaker": student.name,
                "text": student_initiation_9,
                "timestamp": datetime.now().isoformat()
            }
            classroom_history_log.append(log_entry)
            time.sleep(1) 

            # 2b. Teacher Responds to Initiation (Expected Code 3/5 - Detailed response)
            current_turn += 1
            prompt_for_teacher_response = f"A student 'Deep Thinker' just initiated a discussion with: \"{student_initiation_9}\". Provide a detailed and comprehensive response in Vietnamese to address their critical point."
            teacher_final_response = teacher.generate_response(prompt_for_teacher_response)
            
            # Log Entry 3 - Teacher Response (Code 3/5)
            log_entry = {
                "session_id": session_id,
                "turn": current_turn,
                "speaker": teacher.name,
                "text": teacher_final_response,
                "timestamp": datetime.now().isoformat()
            }
            classroom_history_log.append(log_entry)
            time.sleep(1)
            
        else:
            # --- SCENARIO B (20% of active, 17% total): TEACHER CHECK (Code 4 -> Code 8 -> Code 3) ---
            
            # 2a. Teacher Asks Closed Question (Expected Code 4)
            current_turn += 1
            closed_question = f"Giờ chúng ta hãy làm rõ một điểm cốt lõi. Dựa trên nội dung về {slide['slide_content'].split(':')[0]}, hãy nói tóm tắt sự khác biệt về bản chất giữa $X$ (Features) và $y$ (Labels) mà chúng ta vừa học là gì?"
            teacher_response_q = teacher.generate_response(closed_question) # Teacher asks a question (Code 4)
            
            # Log Entry 2 - Teacher Asks a closed question (Code 4)
            log_entry = {
                "session_id": session_id,
                "turn": current_turn,
                "speaker": teacher.name,
                "text": teacher_response_q,
                "timestamp": datetime.now().isoformat()
            }
            classroom_history_log.append(log_entry)
            time.sleep(1) 

            # 2b. Deep Thinker Responds (Expected Code 8 - Forced response)
            current_turn += 1
            prompt_for_student_response = f"Prof. X just asked a factual question: \"{teacher_response_q}\". Please respond directly and concisely in Vietnamese to this specific question, without adding any new points."
            student_response_8 = student.generate_response(prompt_for_student_response) # Student responds (Code 8)
            
            # Log Entry 3 - Deep Thinker Responds (Code 8)
            log_entry = {
                "session_id": session_id,
                "turn": current_turn,
                "speaker": student.name,
                "text": student_response_8,
                "timestamp": datetime.now().isoformat()
            }
            classroom_history_log.append(log_entry)
            time.sleep(1)

            # 2c. Teacher Acknowledges (Expected Code 3 - Detailed acknowledgement)
            current_turn += 1
            prompt_for_teacher_ack = f"The student 'Deep Thinker' responded: \"{student_response_8}\". Please acknowledge the correct response, elaborate significantly on the importance of X and Y, and encourage further focus on the material. Ensure your response is detailed."
            teacher_ack = teacher.generate_response(prompt_for_teacher_ack) # Teacher acknowledges (Code 3)
            
            # Log Entry 4 - Teacher Acknowledgement (Code 3)
            log_entry = {
                "session_id": session_id,
                "turn": current_turn,
                "speaker": teacher.name,
                "text": teacher_ack,
                "timestamp": datetime.now().isoformat()
            }
            classroom_history_log.append(log_entry)
            time.sleep(1)


    return classroom_history_log

def run_multi_sessions():
    """Run multiple simulations and save logs."""
    # Retrieve the global LOG_FILE variable (which includes the timestamp)
    global LOG_FILE 
    
    print(f"--- STARTING SIMCLASS REPLICATION (V4: EXTREME TT & HIGH SIR) ---")
    print(f"Model: {MODEL_NAME} | Sessions: {N_SESSIONS}")
    print(f"Flow: 15% Silent, 68% Code 9, 17% Code 4->8. Teacher Lecture forced to >200 words.")
    print("-------------------------------------------------------\n")

    # Initialize Agents
    teacher = SimAgent("Prof. X", TEACHER_SYSTEM_PROMPT, MODEL_NAME)
    student = SimAgent("Deep Thinker", DEEP_THINKER_SYSTEM_PROMPT, MODEL_NAME)
    
    all_logs = []
    
    for i in range(1, N_SESSIONS + 1):
        print(f"--- STARTING SESSION {i}/{N_SESSIONS} ---")
        # Run simulation for a single session
        session_logs = run_single_session(i, teacher, student, course_script)
        all_logs.extend(session_logs)
        print(f"Session {i} completed. Total utterances: {len(session_logs)}.")
        time.sleep(5) # Delay between sessions

    # Save all logs to a JSON Lines file
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for log in all_logs:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
            
    print(f"\nCOMPLETED: Ran {N_SESSIONS} sessions. Total utterances: {len(all_logs)}.")
    print(f"Conversation log saved to '{LOG_FILE}'")


if __name__ == "__main__":
    run_multi_sessions()