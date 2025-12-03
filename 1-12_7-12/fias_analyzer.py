import google.generativeai as genai
import json
import os
import glob
import time

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Replace "YOUR_API_KEY" with your actual key (use the same key as the previous file)
GOOGLE_API_KEY = "AIzaSyDLKsILJJD7IM0mpV9f_lxnN0DgnfY4MoA" 
# Find the latest log file based on the pattern (replace if needed)
LOG_FILE_PATTERN = "simulation_log_structured_*.jsonl"
OUTPUT_LABELED_FILE = "fias_labeled_results.jsonl"
# --- MODEL UPDATE AS REQUESTED ---
MODEL_NAME = "gemini-2.0-flash"

if GOOGLE_API_KEY == "YOUR_API_KEY":
    if "GOOGLE_API_KEY" in os.environ:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    else:
        # Error if key is not provided
        raise ValueError("API Key is not provided. Please enter GOOGLE_API_KEY.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# ==========================================
# 2. FIAS ANALYST AGENT (Step 4.1)
# ==========================================

FIAS_ANALYST_SYSTEM_PROMPT = """[ROLE] You are an Educational Analyst responsible for categorizing classroom interactions using the Flanders Interaction Analysis System (FIAS).
[TASK] Analyze the provided turn of dialogue and classify its type using exactly ONE number from 1 to 9. Do NOT output any explanation, text, or markdown formatting, only the single digit.
[FIAS CODES - Refined based on SimClass and original Flanders principles]
1: Accepts Feeling (Teacher): Requires clear labeling of the student's feeling (rare event).
2: Praise or Encouragement (Teacher): Praise or encouragement. Avoid coding habitual routine superficial exclamations of praise. Code more than once if extended praise is given.
3: Accepts or Uses Ideas of Student (Teacher): Responds to, acknowledges, modifies (e.g., "That's right, modifying the learning rate will prevent overfitting"), applies (e.g., "We can apply your suggestion to the Decision Tree model"), compares, or summarizes the student's idea. Code more than once if an extended response is given. Caution: Be careful not to let it become Lecturing (Code 5) or Asking Question (Code 4).
4: Asks Questions (Teacher): Teacher poses a question and expects an answer (not a rhetorical question). DO NOT code if the purpose is to bring others into the discussion (e.g., "What do you think Joe?").
5: Lecturing (Teacher): Delivering the main content (from script), expressing opinions, giving facts (e.g., "The key concept of a CNN is weight sharing"), injecting thoughts, and off-handed comments. This is the most common category for most Teacher talk.
6: Giving Directions (Teacher): Instructions or commands intended to produce compliance. Includes questions during drill exercises. Avoid confusion with announcements (Code 5).
7: Criticizing or Justifying Authority (Teacher): Criticizing or justifying authority (N/A in this Sim).
8: Student Response (Student): Direct (and expected) response to the Teacher's question or direction (usually closed questions). **Use Code 8 in all cases where there is doubt between 8 and 9.**
9: Student Initiation (Student): Student VOLUNTARILY initiates: 
    A) Response to an open-ended teacher question (e.g., "What are the limitations of the linear regression model?"). 
    B) Student adds voluntary/independent information to the response (turns an 8 into a 9). 
    C) Raises a new question, counter-argument (e.g., "But wouldn't using a larger dataset increase the risk of concept drift?"), or makes an off-target/resistance comment.
[OUTPUT FORMAT] Only a single digit (1-9).
"""

# Initialize Analyst Model
analyst_model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=FIAS_ANALYST_SYSTEM_PROMPT
)

def get_fias_label(speaker, text):
    """
    Send the turn to the Analyst Agent for FIAS labeling (1-9).
    """
    prompt = f"Speaker: {speaker}\nText: \"{text}\""
    
    # Simple retry mechanism
    for attempt in range(3):
        try:
            response = analyst_model.generate_content(prompt)
            # Get the response and clean it to keep only the digit
            label_text = response.text.strip()
            if label_text.isdigit() and 1 <= int(label_text) <= 9:
                return int(label_text)
            else:
                print(f"  [WARNING] Invalid response: '{label_text}'. Retrying...")
        except Exception as e:
            print(f"  [API ERROR] Error on attempt {attempt+1}: {e}")
        time.sleep(2 ** attempt) # Exponential backoff
        
    return 0 # Return 0 if failed after multiple attempts

# ==========================================
# 3. METRICS CALCULATION (Step 4.2)
# ==========================================

def calculate_fias_metrics(labeled_data):
    """
    Calculate Teacher Talk (TT) and Student Initiation Ratio (SIR) metrics.
    """
    # Count frequency of each FIAS code
    fias_counts = {i: 0 for i in range(1, 10)}
    for entry in labeled_data:
        label = entry.get('fias_label')
        if label in fias_counts:
            fias_counts[label] += 1
            
    # Total number of analyzable turns (FIAS 1-9)
    total_analyzable_turns = sum(fias_counts.values())
    if total_analyzable_turns == 0:
        return {"TT": 0, "ST": 0, "SIR": 0}

    # Total Teacher Talk
    # TT Numerator (FIAS 1-4: Indirect Influence, FIAS 5-7: Direct Influence)
    teacher_talk_count = fias_counts[1] + fias_counts[2] + fias_counts[3] + fias_counts[4] + \
                         fias_counts[5] + fias_counts[6] + fias_counts[7]
                         
    # Total Student Talk
    student_talk_count = fias_counts[8] + fias_counts[9]

    # Teacher Talk Ratio (TT): Teacher Talk / (Teacher Talk + Student Talk)
    # Note: The SimClass paper defines TT as (1-4) / (1-7), but the classical formula is T / (T+S)
    # We use the TT definition in the context of SimClass: T/(T+S)
    if teacher_talk_count + student_talk_count > 0:
        tt_ratio = teacher_talk_count / (teacher_talk_count + student_talk_count)
        st_ratio = student_talk_count / (teacher_talk_count + student_talk_count)
    else:
        tt_ratio = 0
        st_ratio = 0

    # Student Initiation Ratio (SIR): Initiation (9) / Student Talk (8+9)
    if student_talk_count > 0:
        sir_ratio = fias_counts[9] / student_talk_count
    else:
        sir_ratio = 0

    return {
        "FIAS_COUNTS": fias_counts,
        "Teacher Talk (TT)": round(tt_ratio, 3), # Expected TT ~ 0.816
        "Student Talk (ST)": round(st_ratio, 3),
        "Student Initiation Ratio (SIR)": round(sir_ratio, 3) # Expected SIR ~ 0.896
    }

# ==========================================
# 4. MAIN EXECUTION
# ==========================================

def run_fias_analysis():
    # Find the latest log file
    list_of_files = glob.glob(LOG_FILE_PATTERN)
    if not list_of_files:
        print(f"ERROR: No log file found matching pattern '{LOG_FILE_PATTERN}'.")
        print("Please run 'simclass_replication_v2.py' first.")
        return

    latest_log_file = max(list_of_files, key=os.path.getctime)
    print(f"--- STARTING FIAS ANALYSIS ---")
    print(f"Latest log file found: {latest_log_file}")

    # 1. Load and Label Data
    original_data = []
    labeled_data = []
    try:
        with open(latest_log_file, "r", encoding="utf-8") as f:
            for line in f:
                original_data.append(json.loads(line))
    except Exception as e:
        print(f"ERROR reading file: {e}")
        return

    print(f"Total turns to label: {len(original_data)}")
    
    count = 0
    for entry in original_data:
        count += 1
        speaker = entry['speaker']
        text = entry['text']
        
        print(f"[{count}/{len(original_data)}] Labeling turn for {speaker}...")
        label = get_fias_label(speaker, text)
        
        entry['fias_label'] = label
        labeled_data.append(entry)

    # 2. Save labeled results
    with open(OUTPUT_LABELED_FILE, "w", encoding="utf-8") as f:
        for entry in labeled_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
    print(f"\nLabeled data saved to '{OUTPUT_LABELED_FILE}'")

    # 3. Calculate Metrics (Step 4.2)
    metrics = calculate_fias_metrics(labeled_data)
    
    # 4. Comparison and Conclusion (Step 4.3)
    
    print("\n" + "="*50)
    print("      KẾT QUẢ PHÂN TÍCH FIAS (Bước 4.3)      ")
    print("="*50)
    print(f"Tần suất FIAS Codes (1-9): {metrics['FIAS_COUNTS']}")
    print("-" * 50)
    
    # Comparison data from SimClass paper (Table 2)
    EXPECTED_TT = 0.816
    EXPECTED_SIR = 0.896

    print(f"Chỉ số Teacher Talk (TT): {metrics['Teacher Talk (TT)']:.3f}")
    print(f"  (So sánh với SimClass gốc: ~{EXPECTED_TT})")
    print(f"Chỉ số Student Talk (ST): {metrics['Student Talk (ST)']:.3f}")
    print("-" * 50)
    print(f"Chỉ số Student Initiation Ratio (SIR): {metrics['Student Initiation Ratio (SIR)']:.3f}")
    print(f"  (So sánh với SimClass gốc: ~{EXPECTED_SIR})")
    print("="*50)
    
    # Conclusion
    print("\n--- NHẬN XÉT VÀ KẾT LUẬN ---")
    print("Dựa trên kết quả này, bạn có thể so sánh mức độ tương tác giữa Agent bạn tạo với số liệu baseline của bài báo gốc.")
    if metrics['Student Initiation Ratio (SIR)'] >= EXPECTED_SIR * 0.9:
        print("Kết quả SIR RẤT TỐT, cho thấy Agent Deep Thinker đang khởi xướng thảo luận mạnh mẽ, tương đồng với nghiên cứu gốc.")
    else:
        print("SIR thấp hơn dự kiến, có thể cần tinh chỉnh prompt của Agent Deep Thinker để khuyến khích nó đặt câu hỏi ĐỘC LẬP hơn.")
    
    if metrics['Teacher Talk (TT)'] > EXPECTED_TT * 1.05:
        print("TT cao hơn dự kiến, cho thấy Giáo sư X đang nói nhiều hơn và cần được khuyến khích tương tác gián tiếp (FIAS 2, 3, 4) thay vì chỉ giảng bài (FIAS 5).")
    elif metrics['Teacher Talk (TT)'] < EXPECTED_TT * 0.95:
        print("TT thấp hơn dự kiến, Giáo sư X có thể đang quá ngắn gọn và cần truyền tải nhiều nội dung hơn.")
    else:
        print("TT nằm trong phạm vi chấp nhận được.")

if __name__ == "__main__":
    run_fias_analysis()