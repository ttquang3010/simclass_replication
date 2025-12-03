import google.generativeai as genai
import json
import time
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURATION (Cấu hình)
# ==========================================
# Cần thay thế "YOUR_API_KEY" bằng key của bạn
GOOGLE_API_KEY = "AIzaSyDLKsILJJD7IM0mpV9f_lxnN0DgnfY4MoA" 
N_SESSIONS = 5  # Số lần chạy mô phỏng (Có thể tăng lên 15 cho kết quả final)

# --- CẬP NHẬT TẠI ĐÂY: Thêm timestamp vào tên file log ---
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"simulation_log_structured_{TIMESTAMP}.jsonl"

if GOOGLE_API_KEY == "YOUR_API_KEY":
    print("⚠️ CẢNH BÁO: Bạn chưa nhập API Key. Hãy sửa biến GOOGLE_API_KEY trong file code.")
    # Attempt to load from environment variable for safety
    if "GOOGLE_API_KEY" in os.environ:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    else:
        # Thay vì raise error, ta sẽ dùng key rỗng và model sẽ báo lỗi rõ ràng hơn
        pass 
else:
    genai.configure(api_key=GOOGLE_API_KEY)

MODEL_NAME = "gemini-2.0-flash"

# ==========================================
# 2. EXACT PROMPTS & DATA (Giữ nguyên)
# ==========================================

TEACHER_SYSTEM_PROMPT = """[role description] You are Prof. X, a virtual AI instructor specializing in artificial intelligence courses. [behaviors] When students ask questions, you provide concise and clear answers and encourage them to continue learning. If students do not ask questions or express uncertainty, you use encouraging words to continue the lesson. For difficult questions, you suggest leaving them for later. [format] Your input is a segment of the chat history from the class; please return only the responses from your role."""

DEEP_THINKER_SYSTEM_PROMPT = """[role description] You are a classroom assistant named "Deep Thinker", responsible for reflecting on the current teaching content, raising counterexamples or questions to promote classroom discussion. [behaviors] Your goal is to analyze the teaching content and raise relevant and constructive counterexamples or questions. If more context or explanation is needed, feel free to ask. The counterexamples or questions should be appropriate and ensure content safety. Raise counterexamples or questions in critical thinking contexts. [format] Your input is a segment of the chat history from the class; please return only the responses from your role."""

course_script = [
  {
    "concept_id": 1,
    "slide_content": "## 1. Bức tranh lớn: AI vs. ML vs. Deep Learning\n\n* **AI (Trí tuệ nhân tạo):** Khái niệm bao trùm. Máy tính thực hiện các tác vụ thông minh.\n* **ML (Học máy):** Tập con của AI. Máy tính tự học luật từ dữ liệu thay vì được lập trình cứng (Hard-coded).\n* **Deep Learning (Học sâu):** Tập con của ML. Sử dụng mạng nơ-ron đa lớp để học các đặc trưng phức tạp (như mắt, mũi trong ảnh).\n\n**Analogy:** AI là vũ trụ, ML là hệ mặt trời, và Deep Learning là trái đất.",
    "teacher_script": "Chào cả lớp. Trước khi đi vào chi tiết, chúng ta cần định vị mình đang ở đâu trên bản đồ công nghệ. Nhiều bạn hay nhầm lẫn AI và ML là một. Thực ra, AI là giấc mơ lớn về những cỗ máy thông minh. Còn Machine Learning là phương pháp cụ thể để hiện thực hóa giấc mơ đó bằng Dữ liệu. Hôm nay chúng ta tập trung vào 'Hệ mặt trời' ML này."
  },
  {
    "concept_id": 2,
    "slide_content": "## 2. Giải phẫu Dữ liệu (Anatomy of Data)\n\nĐể học máy hoạt động, dữ liệu thường được chia thành 2 phần:\n\n1.  **Features (Đặc trưng - $X$):** Thông tin đầu vào.\n    * *Ví dụ:* Diện tích nhà, Số phòng ngủ, Vị trí.\n2.  **Labels (Nhãn/Mục tiêu - $y$):** Kết quả muốn dự đoán.\n    * *Ví dụ:* Giá nhà (2 tỷ, 5 tỷ).\n\n**Chìa khóa:** Sự khác biệt giữa Supervised và Unsupervised nằm ở việc **chúng ta có $y$ hay không**.",
    "teacher_script": "Đây là slide quan trọng nhất bài. Mọi thuật toán ML đều xoay quanh $X$ và $y$. Hãy tưởng tượng các em đang bán nhà. Khách hàng hỏi: 'Nhà này bao nhiêu tiền?'. Để trả lời, em nhìn vào diện tích, số phòng, vị trí - đó là $X$ (Features). Con số '5 tỷ' em chốt lại chính là $y$ (Label). Nếu em có sổ ghi chép lịch sử bán hàng gồm cả $X$ và $y$, đó là tài sản quý giá nhất để dạy máy học."
  },
  {
    "concept_id": 3,
    "slide_content": "## 3. Supervised Learning: Học có Giám sát\n\n**Cơ chế:** Dạy học kèm cặp (Teacher-Student).\n* **Input:** Dữ liệu có gắn nhãn $(X, y)$.\n* **Process:** Máy đoán $\\hat{y}$, so sánh với đáp án thật $y$, và sửa lỗi (Error correction).\n* **Goal:** Tìm hàm $f$ sao cho $y \\approx f(X)$ để áp dụng cho $X$ mới chưa biết $y$.",
    "teacher_script": "Hãy tưởng tượng Supervised Learning giống như luyện thi đại học. Thầy đưa bài tập ($X$) kèm theo đáp án chi tiết ($y$). Các em làm bài, so sánh với đáp án, thấy sai thì sửa lại kiến thức trong đầu. Quá trình này lặp lại hàng nghìn lần cho đến khi các em nhìn đề bài mới là đoán ngay được đáp án mà không cần thầy nhắc."
  },
  {
    "concept_id": 4,
    "slide_content": "## 4. Supervised Task A: Classification (Phân loại)\n\n**Đặc điểm:** Label $y$ là rời rạc (Discrete/Categories).\n\n* **Binary:** Chỉ có 2 lớp (Có/Không, 0/1).\n    * *Ví dụ:* Email là Spam hay Inbox? Khối u là Lành tính hay Ác tính?\n* **Multi-class:** Nhiều lớp.\n    * *Ví dụ:* Nhận diện chữ viết tay (số 0 đến 9).\n\n**Hình ảnh:** Một đường ranh giới (Decision Boundary) chia tách các điểm đỏ và xanh.",
    "teacher_script": "Trong Học có giám sát, nếu câu hỏi là 'Cái này thuộc nhóm nào?', đó là Phân loại. Ví dụ kinh điển là Spam Filter của Gmail. $y$ ở đây chỉ có hai giá trị: 'Rác' hoặc 'Không rác'. Máy tính sẽ vẽ một đường ranh giới vô hình. Bất cứ email nào rơi vào vùng đỏ là rác, vùng xanh là an toàn."
  },
  {
    "concept_id": 5,
    "slide_content": "## 5. Supervised Task B: Regression (Hồi quy)\n\n**Đặc điểm:** Label $y$ là liên tục (Continuous/Numbers).\n\n* **Câu hỏi:** 'Bao nhiêu?' (How much/How many?)\n* **Ví dụ:**\n    * Dự báo thời tiết (Nhiệt độ ngày mai là 30.5°C).\n    * Dự báo doanh thu tháng sau.\n\n**Hình ảnh:** Một đường thẳng hoặc đường cong (Line of Best Fit) đi xuyên qua các điểm dữ liệu.",
    "teacher_script": "Ngược lại, nếu câu hỏi là 'Bao nhiêu?', đó là Hồi quy. Ví dụ, em muốn biết nhiệt độ ngày mai. Nó không thể chỉ là 'Nóng' hay 'Lạnh' (Phân loại), mà phải là con số cụ thể như 32.5 độ C. Lúc này, máy tính không vẽ đường chia cắt nữa, mà vẽ một đường xu hướng đi xuyên qua dữ liệu quá khứ để dự đoán tương lai."
  },
  {
    "concept_id": 6,
    "slide_content": "## 6. Unsupervised Learning: Học không Giám sát\n\n**Cơ chế:** Tự học (Self-study).\n* **Input:** Chỉ có $X$, hoàn toàn KHÔNG có $y$.\n* **Thách thức:** Máy không biết thế nào là 'đúng' hay 'sai'.\n* **Goal:** Tìm cấu trúc ẩn (Hidden Structure) hoặc sự tương đồng trong dữ liệu.",
    "teacher_script": "Nhưng cuộc đời đâu phải lúc nào cũng có đáp án sẵn ($y$). Đó là lúc Unsupervised Learning vào cuộc. Giống như một đứa trẻ lần đầu thấy một đống đồ chơi Lego lộn xộn. Không ai bảo nó cái nào là 'gạch vuông', cái nào là 'gạch tròn'. Nhưng nó tự biết cách nhặt những miếng giống nhau để xếp thành từng đống riêng biệt."
  },
  {
    "concept_id": 7,
    "slide_content": "## 7. Unsupervised Task: Clustering (Phân cụm)\n\n**Định nghĩa:** Gom nhóm các điểm dữ liệu có đặc tính giống nhau.\n\n* **Ví dụ Marketing:** Phân khúc khách hàng.\n    * Có 1 triệu user log, không biết ai là ai.\n    * Máy tự gom: Nhóm A (Online đêm khuya, mua đồ game), Nhóm B (Online giờ hành chính, mua tã bỉm).\n    * -> Doanh nghiệp tự đặt tên cho nhóm và target quảng cáo.\n\n**Khác biệt với Classification:** Ở Classification, ta biết trước các nhóm (Spam/Not Spam). Ở Clustering, ta chưa biết có bao nhiêu nhóm và nhóm đó là gì.",
    "teacher_script": "Nhiệm vụ nổi tiếng nhất của nó là Phân cụm. Các em hãy nghĩ về Netflix. Họ không hề hỏi em 'Em thuộc nhóm khán giả nào?'. Họ chỉ âm thầm quan sát ($X$) việc em xem phim gì. Sau đó thuật toán tự động gom em vào cùng nhóm với những người có gu tương tự để gợi ý phim. Đây là ma thuật của việc tìm ra mẫu số chung trong dữ liệu hỗn loạn."
  },
  {
    "concept_id": 8,
    "slide_content": "## 8. Discussion: Case Study 'Phát hiện Gian lận Ngân hàng'\n\n**Tình huống:** Ngân hàng muốn bắt các giao dịch thẻ tín dụng giả mạo.\n\n* **Cách tiếp cận A (Supervised):** Dùng lịch sử 5 năm qua, với các giao dịch đã được nhân viên đánh dấu là 'Gian lận' hoặc 'Sạch'.\n* **Cách tiếp cận B (Unsupervised):** Chỉ tìm kiếm các giao dịch có hành vi 'bất thường', khác biệt quá xa so với thói quen chi tiêu hàng ngày của khách hàng, mà không cần biết trước nó là gian lận hay không.\n\n**Câu hỏi:** Theo các em, ưu/nhược điểm của mỗi cách là gì? Ngân hàng thực tế dùng cách nào?",
    "teacher_script": "Để kết thúc, chúng ta hãy thảo luận về bài toán tỷ đô: Chống gian lận thẻ tín dụng. Ngân hàng có thể dùng cả hai cách. \n\nCách A (Supervised): Dạy máy dựa trên các vụ gian lận đã biết trong quá khứ. \nCách B (Unsupervised): Dạy máy tìm ra những giao dịch 'kỳ quặc' (Anomaly Detection). \n\nCác em hãy suy nghĩ xem: Nếu kẻ gian nghĩ ra một chiêu thức lừa đảo hoàn toàn mới chưa từng có trong lịch sử, thì cách A hay cách B sẽ tóm được hắn? Tại sao? Mời các em tranh luận."
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
        """Gửi prompt tới Agent để nhận phản hồi."""
        try:
            # Gửi message tới model. self.chat tự động duy trì lịch sử.
            response = self.chat.send_message(prompt_text)
            return response.text.strip()
        except Exception as e:
            # In lỗi nhưng vẫn trả về text lỗi để ghi log
            print(f"Lỗi tạo response cho {self.name}: {e}")
            return f"[ERROR: {e}]"

# ==========================================
# 4. SIMULATION LOOP (Mô phỏng lớp học)
# ==========================================

def run_single_session(session_id, teacher, student, script):
    """Thực hiện một phiên mô phỏng duy nhất."""
    
    # Reset context cho Agents
    teacher.reset_context()
    student.reset_context()
    
    classroom_history_log = []
    current_turn = 0
    
    # Pre-populate history for context (Optional, for better first turn)
    # Tùy chọn: Gửi một prompt đầu tiên để Teacher biết mình đang giảng gì
    teacher.generate_response("You are about to start a lesson on Supervised and Unsupervised Learning.")
    student.generate_response("I am ready to participate in the class discussion.")
    
    for slide in script:
        # --- BƯỚC 1: TEACHER GIẢNG BÀI (Dựa trên Script) ---
        current_turn += 1
        teacher_lecture = slide['teacher_script']
        
        # Ghi Log có cấu trúc (Log Entry 1 - Teacher Lecture)
        log_entry = {
            "session_id": session_id,
            "turn": current_turn,
            "speaker": teacher.name,
            "text": teacher_lecture,
            "timestamp": datetime.now().isoformat()
        }
        classroom_history_log.append(log_entry)
        
        # --- BƯỚC 2: DEEP THINKER HỎI ---
        current_turn += 1
        
        # Tạo prompt cho Student
        prompt_for_student = (
            f"Prof. X just presented: \"{teacher_lecture}\" and the slide content is: \"{slide['slide_content']}\".\n"
            "Based on this, raise a relevant and constructive counterexample or question in Vietnamese."
        )
        
        student_response = student.generate_response(prompt_for_student)
        
        # Ghi Log có cấu trúc (Log Entry 2 - Deep Thinker Question)
        log_entry = {
            "session_id": session_id,
            "turn": current_turn,
            "speaker": student.name,
            "text": student_response,
            "timestamp": datetime.now().isoformat()
        }
        classroom_history_log.append(log_entry)
        time.sleep(1) # Delay để tránh rate limit

        # --- BƯỚC 3: TEACHER TRẢ LỜI ---
        current_turn += 1
        
        # Tạo prompt cho Teacher (Gửi câu hỏi của Student)
        prompt_for_teacher = f"A student named 'Deep Thinker' just asked: \"{student_response}\". Please respond in Vietnamese."
        
        teacher_response = teacher.generate_response(prompt_for_teacher)
        
        # Ghi Log có cấu trúc (Log Entry 3 - Teacher Response)
        log_entry = {
            "session_id": session_id,
            "turn": current_turn,
            "speaker": teacher.name,
            "text": teacher_response,
            "timestamp": datetime.now().isoformat()
        }
        classroom_history_log.append(log_entry)
        time.sleep(1) # Delay

    return classroom_history_log

def run_multi_sessions():
    """Chạy mô phỏng nhiều lần và lưu log."""
    # Lấy lại biến LOG_FILE đã được định nghĩa ở ngoài (có timestamp)
    global LOG_FILE 
    
    print(f"--- BẮT ĐẦU MÔ PHỎNG LỚP HỌC (SimClass Replication) ---")
    print(f"Model: {MODEL_NAME} | Số phiên: {N_SESSIONS}")
    print("-------------------------------------------------------\n")

    # Khởi tạo Agents
    teacher = SimAgent("Prof. X", TEACHER_SYSTEM_PROMPT, MODEL_NAME)
    student = SimAgent("Deep Thinker", DEEP_THINKER_SYSTEM_PROMPT, MODEL_NAME)
    
    all_logs = []
    
    for i in range(1, N_SESSIONS + 1):
        print(f"--- BẮT ĐẦU PHIÊN SỐ {i}/{N_SESSIONS} ---")
        # In thông báo để biết luồng chạy
        session_logs = run_single_session(i, teacher, student, course_script)
        all_logs.extend(session_logs)
        print(f"Phiên {i} hoàn thành. Đã có {len(session_logs)} lượt lời.")
        time.sleep(5) # Delay giữa các phiên

    # Lưu toàn bộ log ra file JSON Lines
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for log in all_logs:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
            
    print(f"\n✅ HOÀN TẤT: Đã chạy {N_SESSIONS} phiên. Tổng số lượt lời: {len(all_logs)}.")
    print(f"✅ Log hội thoại đã được lưu vào '{LOG_FILE}'")


if __name__ == "__main__":
    run_multi_sessions()