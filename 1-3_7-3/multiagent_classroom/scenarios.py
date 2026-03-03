"""
Scenario Module

Implements teaching scenario execution for COPUS observation.
"""

import time
import logging
from typing import Dict, List, Any

from .agent import SimpleAgent
from .observer import COPUSObserver
from . import constants as const


logger = logging.getLogger(__name__)


class ScenarioExecutor:
    """
    Executes teaching scenarios for COPUS observation.
    
    Manages scenario execution with proper logging and timing.
    """
    
    def __init__(self, observer: COPUSObserver) -> None:
        """
        Initialize scenario executor.
        
        Args:
            observer: COPUSObserver instance for recording
        """
        self.observer: COPUSObserver = observer
        self.conversation_log: List[Dict[str, Any]] = []
    
    def execute_lec_only(
        self, 
        teacher: SimpleAgent, 
        slides: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute Scenario 1: Lec-only (lecture-based teaching).
        
        Teacher lectures continuously (Lec code) while students
        listen and take notes (L code).
        
        Args:
            teacher: Teacher agent instance
            slides: List of slide content dictionaries
            
        Returns:
            List of conversation log dictionaries
        """
        self.conversation_log = []
        self._log_scenario_start("Scenario 1: Lec-only")
        
        for turn in range(const.TURNS_PER_SESSION):
            segment: int = turn + 1
            self._log_segment_start(segment)
            
            slide_content: str = self._get_slide_content(slides, turn)
            teacher_response: str = self._generate_lecture(teacher, segment, slide_content)
            
            self._record_lec_segment(segment, teacher_response, slide_content, slides, turn)
            time.sleep(const.BRIEF_PAUSE)
        
        self._log_scenario_complete("Scenario 1: Lec-only")
        return self.conversation_log
    
    def execute_pq_only(
        self,
        teacher: SimpleAgent,
        student_active: SimpleAgent,
        student_passive: SimpleAgent,
        slides: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute Scenario 2: PQ-only (question-driven teaching).
        
        Teacher poses questions (PQ code) while students answer (AnQ code)
        or ask questions (SQ code).
        
        Args:
            teacher: Teacher agent instance
            student_active: Active student agent instance
            student_passive: Passive student agent instance
            slides: List of slide content dictionaries
            
        Returns:
            List of conversation log dictionaries
        """
        self.conversation_log = []
        self._log_scenario_start("Scenario 2: PQ-only")
        
        for turn in range(const.TURNS_PER_SESSION):
            segment: int = turn + 1
            self._log_segment_start(segment)
            
            topic, key_terms = self._get_slide_metadata(slides, turn)
            teacher_question: str = self._generate_question(teacher, segment, topic, key_terms)
            
            student_answer, student_codes = self._get_student_response(
                turn, teacher_question, student_active, student_passive
            )
            
            self._record_pq_segment(
                segment, teacher_question, student_answer, student_codes, topic
            )
            time.sleep(const.BRIEF_PAUSE)
        
        self._log_scenario_complete("Scenario 2: PQ-only")
        return self.conversation_log
    
    def _get_slide_content(self, slides: List[Dict[str, Any]], turn: int) -> str:
        """
        Get slide content for current turn.
        
        Args:
            slides: List of slides
            turn: Current turn number
            
        Returns:
            Formatted slide content string
        """
        if turn < len(slides):
            slide: Dict[str, Any] = slides[turn]
            content: str = f"Slide {slide['slide_number']}: {slide['title']}\n"
            content += "\n".join(slide['content'])
            return content
        return "Tổng kết và câu hỏi"
    
    def _get_slide_metadata(
        self, 
        slides: List[Dict[str, Any]], 
        turn: int
    ) -> tuple[str, str]:
        """
        Get slide topic and key terms.
        
        Args:
            slides: List of slides
            turn: Current turn number
            
        Returns:
            Tuple of (topic, key_terms)
        """
        if turn < len(slides):
            slide: Dict[str, Any] = slides[turn]
            topic: str = slide['title']
            key_terms: str = ', '.join(slide.get('key_terms', []))
            return topic, key_terms
        return "Tổng kết", "Linear regression, loss function"
    
    def _generate_lecture(
        self, 
        teacher: SimpleAgent, 
        segment: int, 
        slide_content: str
    ) -> str:
        """
        Generate lecture content from teacher.
        
        Args:
            teacher: Teacher agent
            segment: Segment number
            slide_content: Slide content to lecture on
            
        Returns:
            Generated lecture text
        """
        prompt: str = f"""Bạn đang ở phút thứ {segment*2-2} đến {segment*2} của buổi học.
        
Nhiệm vụ: GIẢNG BÀI (Lecturing - mã Lec) về nội dung sau:

{slide_content}

Hãy trình bày nội dung này một cách rõ ràng, sử dụng thuật ngữ chuyên ngành chính xác.
Chỉ giảng bài, KHÔNG đặt câu hỏi cho sinh viên.
Giới hạn: 3-4 câu ngắn gọn."""
        
        response: str = teacher.generate_response(prompt)
        logger.info(f"[Teacher] {response}")
        return response
    
    def _generate_question(
        self, 
        teacher: SimpleAgent, 
        segment: int, 
        topic: str, 
        key_terms: str
    ) -> str:
        """
        Generate question from teacher.
        
        Args:
            teacher: Teacher agent
            segment: Segment number
            topic: Current topic
            key_terms: Key terms for the topic
            
        Returns:
            Generated question text
        """
        prompt: str = f"""Bạn đang ở phút thứ {segment*2-2} đến {segment*2} của buổi học.

Chủ đề: {topic}
Từ khóa: {key_terms}

Nhiệm vụ: ĐẶT CÂU HỎI (Posing Question - mã PQ) để kích thích tư duy sinh viên.

Ví dụ câu hỏi tốt:
- "Theo các bạn, tại sao ta cần tối thiểu hóa hàm mất mát?"
- "Nếu hệ số góc w = 0, điều gì xảy ra với mô hình?"
- "Gradient Descent và phương pháp giải tích khác nhau thế nào?"

Hãy đặt 1 câu hỏi mở để sinh viên suy nghĩ. KHÔNG giảng bài."""
        
        question: str = teacher.generate_response(prompt)
        logger.info(f"[Teacher] {question}")
        return question
    
    def _get_student_response(
        self,
        turn: int,
        teacher_question: str,
        student_active: SimpleAgent,
        student_passive: SimpleAgent
    ) -> tuple[str, List[str]]:
        """
        Get student response to teacher's question.
        
        Args:
            turn: Current turn number
            teacher_question: Question from teacher
            student_active: Active student agent
            student_passive: Passive student agent
            
        Returns:
            Tuple of (student_answer, student_codes)
        """
        if turn % 2 == 0:
            return self._get_active_student_answer(teacher_question, student_active)
        else:
            return self._get_passive_student_response(
                turn, teacher_question, student_passive
            )
    
    def _get_active_student_answer(
        self, 
        question: str, 
        student: SimpleAgent
    ) -> tuple[str, List[str]]:
        """
        Get answer from active student.
        
        Args:
            question: Teacher's question
            student: Active student agent
            
        Returns:
            Tuple of (answer, ["AnQ"])
        """
        prompt: str = f"Giảng viên hỏi: {question}\n\nHãy trả lời câu hỏi này (2-3 câu ngắn)."
        answer: str = student.generate_response(prompt)
        logger.info(f"[Student A] {answer}")
        return answer, ["AnQ"]
    
    def _get_passive_student_response(
        self, 
        turn: int, 
        question: str, 
        student: SimpleAgent
    ) -> tuple[str, List[str]]:
        """
        Get response from passive student.
        
        Args:
            turn: Current turn number
            question: Teacher's question
            student: Passive student agent
            
        Returns:
            Tuple of (response, student_codes)
        """
        if turn == 1:
            return self._get_student_question(question, student)
        else:
            return self._get_uncertain_answer(question, student)
    
    def _get_student_question(
        self, 
        teacher_question: str, 
        student: SimpleAgent
    ) -> tuple[str, List[str]]:
        """
        Get clarifying question from student.
        
        Args:
            teacher_question: Teacher's original question
            student: Student agent
            
        Returns:
            Tuple of (student_question, ["SQ"])
        """
        prompt: str = (
            f"Giảng viên hỏi: {teacher_question}\n\n"
            "Bạn hơi bối rối. Hãy đặt câu hỏi ngắn gọn để giảng viên làm rõ."
        )
        question: str = student.generate_response(prompt)
        logger.info(f"[Student B] {question}")
        return question, ["SQ"]
    
    def _get_uncertain_answer(
        self, 
        teacher_question: str, 
        student: SimpleAgent
    ) -> tuple[str, List[str]]:
        """
        Get uncertain answer from student.
        
        Args:
            teacher_question: Teacher's question
            student: Student agent
            
        Returns:
            Tuple of (answer, ["AnQ"])
        """
        prompt: str = (
            f"Giảng viên hỏi: {teacher_question}\n\n"
            "Hãy thử trả lời (1-2 câu, có thể không chắc chắn)."
        )
        answer: str = student.generate_response(prompt)
        logger.info(f"[Student B] {answer}")
        return answer, ["AnQ"]
    
    def _record_lec_segment(
        self,
        segment: int,
        teacher_response: str,
        slide_content: str,
        slides: List[Dict[str, Any]],
        turn: int
    ) -> None:
        """
        Record lecture segment observation.
        
        Args:
            segment: Segment number
            teacher_response: Teacher's lecture content
            slide_content: Slide content
            slides: All slides
            turn: Current turn
        """
        slide_title: str = (
            slides[turn].get('title', 'content') 
            if turn < len(slides) 
            else 'summary'
        )
        
        obs: Dict[str, Any] = self.observer.observe_segment(
            segment_number=segment,
            teacher_action=["Lec"],
            student_actions=["L"],
            description=f"Teacher lectures on {slide_title}. Students listen and take notes."
        )
        
        self.conversation_log.append({
            "segment": segment,
            "teacher": teacher_response,
            "students": "Listening and taking notes",
            "copus": obs
        })
    
    def _record_pq_segment(
        self,
        segment: int,
        teacher_question: str,
        student_answer: str,
        student_codes: List[str],
        topic: str
    ) -> None:
        """
        Record question-driven segment observation.
        
        Args:
            segment: Segment number
            teacher_question: Teacher's question
            student_answer: Student's response
            student_codes: Student COPUS codes
            topic: Current topic
        """
        obs: Dict[str, Any] = self.observer.observe_segment(
            segment_number=segment,
            teacher_action=["PQ", "AnQ"],
            student_actions=student_codes,
            description=f"Teacher poses question on {topic}. Student responds."
        )
        
        self.conversation_log.append({
            "segment": segment,
            "teacher": teacher_question,
            "student": student_answer,
            "copus": obs
        })
    
    def _log_scenario_start(self, scenario_name: str) -> None:
        """Log scenario start."""
        logger.info(f"Starting {scenario_name}")
        logger.info("="*60)
    
    def _log_scenario_complete(self, scenario_name: str) -> None:
        """Log scenario completion."""
        logger.info(f"Completed {scenario_name}")
    
    def _log_segment_start(self, segment: int) -> None:
        """Log segment start."""
        logger.info(f"Segment {segment}: Minutes {segment*2-2} - {segment*2}")
