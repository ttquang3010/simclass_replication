"""
Simulation orchestration for SimClass Multi-Agent System
Handles the main classroom interaction flow with teacher-driven patterns
"""

import random
import time
from datetime import datetime
from src.utils import (
    log_and_print, get_student_prompt, is_asking_question,
    classify_question_difficulty, estimate_slide_difficulty,
    calculate_lecture_complexity, write_logs_to_file
)
from src import config


def run_single_session(session_id, agents, script, log_file):
    """Execute a single simulation session with teacher-driven interaction flow."""
    
    # Reset context for all agents
    print(f"\n[CONTEXT RESET] All agents starting fresh for Session {session_id}")
    for agent in agents.values():
        agent.reset_context()
    
    # Initialize auto-save tracking
    # For lecture 2+ (session_id >= 200), always use append mode
    last_save_time = time.time()
    pending_logs = []
    is_continuation = session_id >= 200  # Lectures 2-5
    
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
    
    print(f"[AUTO-SAVE] Enabled. Logs will be saved every {config.AUTO_SAVE_INTERVAL} seconds.\n")
    
    for slide_idx, slide in enumerate(script, 1):
        slide_concept = slide['slide_content'].split(':')[0]
        slide_difficulty = estimate_slide_difficulty(slide_concept)
        
        # Periodic context reset to prevent token overflow
        if slide_idx % config.CONTEXT_RESET_INTERVAL == 0 and slide_idx > 1:
            print(f"\n[PERIODIC CONTEXT RESET] Slide {slide_idx}: Clearing context for all agents to prevent overflow")
            for agent_name, agent in agents.items():
                token_count = agent.estimate_context_tokens()
                print(f"  - {agent_name}: ~{token_count:,} tokens before reset")
                agent.reset_context()
            # Re-establish agent references after reset
            teacher = agents['Prof. X']
            assistant = agents['Clarity Guide']
            simulated_user = agents['Student']
        
        print(f"\n--- SLIDE {slide['concept_id']}: {slide_concept} (Difficulty: {slide_difficulty:.2f}) ---")
        print(f"[Simulated User State] Confusion: {simulated_user.confusion_level:.2f}, "
              f"Courage: {simulated_user.courage_level:.2f}, Fear: {simulated_user.fear_level:.2f}")

        # === PHASE 1: TEACHER LECTURES (FIAS 5) ===
        current_turn += 1
        teacher_lecture = slide['teacher_script']
        
        prompt_for_lecture = (
            f"Deliver the lecture titled \"{slide_concept}\". "
            f"Expand the core script: \"{teacher_lecture}\" into a comprehensive, "
            f"multi-paragraph response (minimum 200 words). "
            f"The slide content is: \"{slide['slide_content']}\""
        )
        
        teacher_lecture_expanded = teacher.generate_response(prompt_for_lecture)
        lecture_complexity = calculate_lecture_complexity(teacher_lecture_expanded)
        
        log_and_print(session_id, current_turn, teacher.name, teacher_lecture_expanded, 
                     classroom_history_log, "Lecture_5")
        
        simulated_user.update_confusion(slide_difficulty, lecture_complexity)

        # === PHASE 2: TEACHER CHECKS UNDERSTANDING (FIAS 4) ===
        current_turn += 1
        teacher_check = teacher.generate_response(
            f"You just taught '{slide_concept}'. Now ask the class if they understand. "
            f"Be encouraging and welcoming of questions."
        )
        log_and_print(session_id, current_turn, teacher.name, teacher_check, 
                     classroom_history_log, "Teacher_Asks_4")
        
        # PASSIVE RESPONSE SCENARIO
        if simulated_user.should_give_passive_response() and random.random() < 0.5:
            current_turn += 1
            passive_prompt = (
                f"Teacher asked if you understand '{slide_concept}'. "
                f"You're confused but too shy to ask. Give a SHORT passive response "
                f"like 'Dạ, em hiểu rồi ạ' or 'Vâng ạ' (maximum 10 words)."
            )
            user_passive = simulated_user.generate_response(passive_prompt)
            log_and_print(session_id, current_turn, simulated_user.name, user_passive, 
                         classroom_history_log, "SimUser_Passive_8")
            print(f"    [Simulated User: Passive Response - Code 8]")

        # === PHASE 3: PEER RESPONSE PATTERNS ===
        pattern_roll = random.random()
        
        if pattern_roll < 0.40:  # 40% - RELATABLE PEER (Curious Baby)
            _handle_curious_baby_pattern(current_turn, slide_concept, peer_agents, assistant, 
                                        teacher, simulated_user, classroom_history_log, session_id)
        
        elif pattern_roll < 0.65:  # 25% - ADVANCED PEER (Deep Thinker)
            _handle_deep_thinker_pattern(current_turn, slide_concept, peer_agents, teacher, 
                                        simulated_user, classroom_history_log, session_id)
        
        elif pattern_roll < 0.85:  # 20% - HUMOR PATH (Mr. Clown)
            _handle_clown_pattern(current_turn, slide_concept, peer_agents, teacher, 
                                 simulated_user, classroom_history_log, session_id)
        
        else:  # 15% - SAFE SUMMARY PATH (Summary Seeker)
            _handle_summary_pattern(current_turn, slide_concept, peer_agents, teacher, 
                                   simulated_user, classroom_history_log, session_id)
        
        # === PHASE 4: DIRECT TEACHER INVITATION ===
        if simulated_user.questions_asked_count == 0 and simulated_user.confusion_level > 0.7:
            _handle_teacher_invitation(current_turn, slide_concept, teacher, assistant, 
                                      simulated_user, classroom_history_log, session_id)
        
        # === AUTO-SAVE CHECK ===
        current_time = time.time()
        if current_time - last_save_time >= config.AUTO_SAVE_INTERVAL:
            # Calculate new logs since last save
            new_logs = classroom_history_log[len(pending_logs):]
            if new_logs:
                # Use append mode if: (1) we have pending logs OR (2) this is a continuation lecture
                write_mode = 'a' if (pending_logs or is_continuation) else 'w'
                write_logs_to_file(new_logs, log_file, mode=write_mode)
                pending_logs = classroom_history_log.copy()
                elapsed_minutes = int((current_time - last_save_time) / 60)
                print(f"\n  [AUTO-SAVE] Saved {len(new_logs)} new utterances after {elapsed_minutes} minutes. Total: {len(classroom_history_log)}")
                last_save_time = current_time

    # Final save for any remaining logs
    new_logs = classroom_history_log[len(pending_logs):]
    if new_logs:
        # Use append mode if: (1) we have pending logs OR (2) this is a continuation lecture
        write_mode = 'a' if (pending_logs or is_continuation) else 'w'
        write_logs_to_file(new_logs, log_file, mode=write_mode)
        print(f"\n[FINAL SAVE] Saved {len(new_logs)} final utterances. Total session: {len(classroom_history_log)}")
    
    # Report final token usage
    print(f"\n[FINAL TOKEN USAGE REPORT]")
    for agent_name, agent in agents.items():
        token_count = agent.estimate_context_tokens()
        print(f"  - {agent_name}: ~{token_count:,} tokens (Max window: {agent.max_context_window or 'Unlimited'})")
    
    print(f"\n[Session End] Simulated User asked {simulated_user.questions_asked_count} questions total.")
    return classroom_history_log


def _handle_curious_baby_pattern(current_turn, slide_concept, peer_agents, assistant, 
                                  teacher, simulated_user, classroom_history_log, session_id):
    """Handle the Curious Baby (relatable peer) interaction pattern."""
    print("  [Pattern: Relatable Peer - Curious Baby asks basic question]")
    current_turn += 1
    
    curious_baby_prompt = get_student_prompt('Curious Baby', slide_concept)
    curious_baby_question = peer_agents['Curious Baby'].generate_response(curious_baby_prompt)
    log_and_print(session_id, current_turn, 'Curious Baby', curious_baby_question, 
                 classroom_history_log, "Question_9")
    
    question_difficulty = classify_question_difficulty(curious_baby_question, 'Curious Baby')
    simulated_user.update_courage('Curious Baby', question_difficulty)
    
    if is_asking_question(curious_baby_question):
        current_turn += 1
        assistant_response = assistant.generate_response(
            f"A student asked: \"{curious_baby_question}\". "
            f"Provide a brief, warm, factual answer about '{slide_concept}'."
        )
        log_and_print(session_id, current_turn, assistant.name, assistant_response, 
                     classroom_history_log, "Assistant_3")
    
    current_turn += 1
    teacher_response = teacher.generate_response(
        f"Student 'Curious Baby' asked: \"{curious_baby_question}\". "
        f"Elaborate on this with examples and confirm the assistant's response if given."
    )
    log_and_print(session_id, current_turn, teacher.name, teacher_response, 
                 classroom_history_log, "Teacher_Elaborates_3_5")
    
    if simulated_user.should_speak() or random.random() < 0.35:
        current_turn += 1
        user_prompt = (
            f"Your classmate just asked a basic question and received a warm response. "
            f"You feel encouraged. You're confused about '{slide_concept}'. "
            f"Ask a simple, apologetic follow-up question."
        )
        user_question = simulated_user.generate_response(user_prompt)
        log_and_print(session_id, current_turn, simulated_user.name, user_question, 
                     classroom_history_log, "SimUser_Question_9")
        
        current_turn += 1
        assistant_warm = assistant.generate_response(
            f"A shy student asked: \"{user_question}\". Give a very warm, encouraging, clear answer."
        )
        log_and_print(session_id, current_turn, assistant.name, assistant_warm, 
                     classroom_history_log, "Assistant_3")
        
        current_turn += 1
        teacher_praise = teacher.generate_response(
            f"A shy student finally asked: \"{user_question}\". "
            f"PRAISE them for asking ('Câu hỏi rất hay!'), then elaborate thoroughly."
        )
        log_and_print(session_id, current_turn, teacher.name, teacher_praise, 
                     classroom_history_log, "Teacher_Praise_2_5")
        
        simulated_user.apply_positive_response()


def _handle_deep_thinker_pattern(current_turn, slide_concept, peer_agents, teacher, 
                                  simulated_user, classroom_history_log, session_id):
    """Handle the Deep Thinker (advanced peer) interaction pattern."""
    print("  [Pattern: Advanced Peer - Deep Thinker asks complex question]")
    current_turn += 1
    
    deep_thinker_prompt = get_student_prompt('Deep Thinker', slide_concept)
    deep_thinker_question = peer_agents['Deep Thinker'].generate_response(deep_thinker_prompt)
    log_and_print(session_id, current_turn, 'Deep Thinker', deep_thinker_question, 
                 classroom_history_log, "Initiation_9")
    
    question_difficulty = classify_question_difficulty(deep_thinker_question, 'Deep Thinker')
    simulated_user.update_courage('Deep Thinker', question_difficulty)
    
    current_turn += 1
    teacher_complex = teacher.generate_response(
        f"Deep Thinker asked a complex question: \"{deep_thinker_question}\". "
        f"Provide a detailed, sophisticated answer."
    )
    log_and_print(session_id, current_turn, teacher.name, teacher_complex, 
                 classroom_history_log, "Teacher_Response_5")
    
    if simulated_user.confusion_level > 0.8 and random.random() < 0.05:
        current_turn += 1
        user_basic = simulated_user.generate_response(
            f"Everyone is discussing complex topics. You're very confused about basic terms "
            f"in '{slide_concept}'. Nervously ask about a fundamental concept."
        )
        log_and_print(session_id, current_turn, simulated_user.name, user_basic, 
                     classroom_history_log, "SimUser_Question_9")
        
        current_turn += 1
        teacher_patient = teacher.generate_response(
            f"A student asked a basic question after complex discussion: \"{user_basic}\". "
            f"Be very patient and explain from fundamentals."
        )
        log_and_print(session_id, current_turn, teacher.name, teacher_patient, 
                     classroom_history_log, "Teacher_Response_3_5")
        
        simulated_user.apply_positive_response()


def _handle_clown_pattern(current_turn, slide_concept, peer_agents, teacher, 
                          simulated_user, classroom_history_log, session_id):
    """Handle the Mr. Clown (humor) interaction pattern."""
    print("  [Pattern: Humor - Mr. Clown makes funny analogy]")
    current_turn += 1
    
    clown_prompt = get_student_prompt('Mr. Clown', slide_concept)
    clown_analogy = peer_agents['Mr. Clown'].generate_response(clown_prompt)
    log_and_print(session_id, current_turn, 'Mr. Clown', clown_analogy, 
                 classroom_history_log, "Clown_9")
    
    simulated_user.update_courage('Mr. Clown', 'medium')
    
    current_turn += 1
    teacher_humor = teacher.generate_response(
        f"Mr. Clown made an analogy: \"{clown_analogy}\". "
        f"Respond with light humor, then clarify the concept seriously."
    )
    log_and_print(session_id, current_turn, teacher.name, teacher_humor, 
                 classroom_history_log, "Teacher_Response_3_5")
    
    if simulated_user.should_speak() or random.random() < 0.20:
        current_turn += 1
        user_relaxed = simulated_user.generate_response(
            f"The class atmosphere is relaxed after humor. You're confused about '{slide_concept}'. "
            f"Ask a simple question."
        )
        log_and_print(session_id, current_turn, simulated_user.name, user_relaxed, 
                     classroom_history_log, "SimUser_Question_9")
        
        current_turn += 1
        teacher_response = teacher.generate_response(
            f"Student asked: \"{user_relaxed}\". Answer warmly."
        )
        log_and_print(session_id, current_turn, teacher.name, teacher_response, 
                     classroom_history_log, "Teacher_Response_3_5")
        
        simulated_user.apply_positive_response()


def _handle_summary_pattern(current_turn, slide_concept, peer_agents, teacher, 
                            simulated_user, classroom_history_log, session_id):
    """Handle the Summary Seeker (safe summary) interaction pattern."""
    print("  [Pattern: Safe Summary - Summary Seeker summarizes]")
    current_turn += 1
    
    summary_prompt = get_student_prompt('Summary Seeker', slide_concept)
    summary_response = peer_agents['Summary Seeker'].generate_response(summary_prompt)
    log_and_print(session_id, current_turn, 'Summary Seeker', summary_response, 
                 classroom_history_log, "Summary_8")
    
    simulated_user.update_courage('Summary Seeker', 'basic')
    
    current_turn += 1
    teacher_confirm = teacher.generate_response(
        f"Summary Seeker said: \"{summary_response}\". "
        f"Confirm if correct and add any missing points."
    )
    log_and_print(session_id, current_turn, teacher.name, teacher_confirm, 
                 classroom_history_log, "Teacher_Confirms_3")


def _handle_teacher_invitation(current_turn, slide_concept, teacher, assistant, 
                                simulated_user, classroom_history_log, session_id):
    """Handle direct teacher invitation to shy student."""
    print("  [Teacher notices shy student is confused - direct invitation]")
    current_turn += 1
    teacher_invite = teacher.generate_response(
        f"You notice a quiet student ('{simulated_user.name}') looks confused. "
        f"Gently invite them to ask questions: 'Em Student có thắc mắc gì không?'"
    )
    log_and_print(session_id, current_turn, teacher.name, teacher_invite, 
                 classroom_history_log, "Teacher_Invites_4")
    
    simulated_user.apply_teacher_encouragement()
    
    if simulated_user.should_speak() or random.random() < 0.40:
        current_turn += 1
        user_breakthrough = simulated_user.generate_response(
            f"The teacher directly invited you to ask. You're very confused about '{slide_concept}'. "
            f"Nervously ask your question."
        )
        log_and_print(session_id, current_turn, simulated_user.name, user_breakthrough, 
                     classroom_history_log, "SimUser_Question_9")
        
        current_turn += 1
        assistant_support = assistant.generate_response(
            f"Student finally asked: \"{user_breakthrough}\". Give very supportive answer."
        )
        log_and_print(session_id, current_turn, assistant.name, assistant_support, 
                     classroom_history_log, "Assistant_3")
        
        current_turn += 1
        teacher_celebrate = teacher.generate_response(
            f"The shy student finally asked: \"{user_breakthrough}\". "
            f"CELEBRATE this courage ('Rất tốt khi em hỏi!'), then explain thoroughly."
        )
        log_and_print(session_id, current_turn, teacher.name, teacher_celebrate, 
                     classroom_history_log, "Teacher_Praise_2_5")
        
        simulated_user.apply_positive_response()
    else:
        current_turn += 1
        user_scared = simulated_user.generate_response(
            "Teacher asked if you have questions. You're too scared. "
            "Say 'Dạ em hiểu rồi ạ' even though you're confused."
        )
        log_and_print(session_id, current_turn, simulated_user.name, user_scared, 
                     classroom_history_log, "SimUser_Safe_8")
        
        current_turn += 1
        teacher_move_on = teacher.generate_response(
            "Student said they understand. Acknowledge and transition to next topic."
        )
        log_and_print(session_id, current_turn, teacher.name, teacher_move_on, 
                     classroom_history_log, "Teacher_Transition_5")
