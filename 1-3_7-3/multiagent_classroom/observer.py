"""
COPUS Observer Module

Implements COPUS (Classroom Observation Protocol for Undergraduate STEM)
observation and recording functionality.
"""

import logging
from typing import Dict, List, Any

from . import constants as const


logger = logging.getLogger(__name__)


class COPUSObserver:
    """
    COPUS-based classroom observer for recording teaching activities.
    
    Tracks instructor and student behaviors using standardized COPUS codes
    in 2-minute intervals.
    
    Attributes:
        observations: List of recorded observation segments
    """
    
    INSTRUCTOR_CODES: Dict[str, str] = const.INSTRUCTOR_CODES
    STUDENT_CODES: Dict[str, str] = const.STUDENT_CODES
    
    def __init__(self) -> None:
        """Initialize observer with empty observations list."""
        self.observations: List[Dict[str, Any]] = []
    
    def observe_segment(
        self, 
        segment_number: int, 
        teacher_action: List[str], 
        student_actions: List[str], 
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Record observations for a 2-minute segment.
        
        Args:
            segment_number: Sequential segment number (1-indexed)
            teacher_action: List of COPUS instructor codes
            student_actions: List of COPUS student codes
            description: Optional textual description
            
        Returns:
            Dictionary containing recorded observation details
        """
        obs: Dict[str, Any] = self._create_observation(
            segment_number, teacher_action, student_actions, description
        )
        self.observations.append(obs)
        self._log_observation(segment_number, teacher_action, student_actions)
        return obs
    
    def _create_observation(
        self,
        segment_number: int,
        teacher_action: List[str],
        student_actions: List[str],
        description: str
    ) -> Dict[str, Any]:
        """
        Create observation dictionary.
        
        Args:
            segment_number: Segment number
            teacher_action: Instructor COPUS codes
            student_actions: Student COPUS codes
            description: Description text
            
        Returns:
            Observation dictionary
        """
        return {
            "segment": segment_number,
            "time_range": f"{segment_number*2}-{(segment_number+1)*2} min",
            "instructor_codes": teacher_action,
            "student_codes": student_actions,
            "description": description
        }
    
    def _log_observation(
        self,
        segment_number: int,
        teacher_action: List[str],
        student_actions: List[str]
    ) -> None:
        """
        Log observation details.
        
        Args:
            segment_number: Segment number
            teacher_action: Instructor codes
            student_actions: Student codes
        """
        logger.debug(
            f"Recorded segment {segment_number}: "
            f"I={teacher_action}, S={student_actions}"
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Generate COPUS summary statistics.
        
        Calculates frequency counts and percentages for each COPUS code
        across all recorded segments.
        
        Returns:
            Dictionary containing:
                - total_segments: Total observation segments
                - instructor_frequency: Instructor code frequencies with percentages
                - student_frequency: Student code frequencies with percentages
                - instructor_counts: Raw counts for instructor codes
                - student_counts: Raw counts for student codes
        """
        instructor_counts: Dict[str, int] = self._count_instructor_codes()
        student_counts: Dict[str, int] = self._count_student_codes()
        total_segments: int = len(self.observations)
        
        return {
            "total_segments": total_segments,
            "instructor_frequency": self._calculate_frequencies(
                instructor_counts, total_segments
            ),
            "student_frequency": self._calculate_frequencies(
                student_counts, total_segments
            ),
            "instructor_counts": instructor_counts,
            "student_counts": student_counts
        }
    
    def _count_instructor_codes(self) -> Dict[str, int]:
        """
        Count occurrences of instructor COPUS codes.
        
        Returns:
            Dictionary mapping codes to counts
        """
        counts: Dict[str, int] = {}
        for obs in self.observations:
            for code in obs["instructor_codes"]:
                counts[code] = counts.get(code, 0) + 1
        return counts
    
    def _count_student_codes(self) -> Dict[str, int]:
        """
        Count occurrences of student COPUS codes.
        
        Returns:
            Dictionary mapping codes to counts
        """
        counts: Dict[str, int] = {}
        for obs in self.observations:
            for code in obs["student_codes"]:
                counts[code] = counts.get(code, 0) + 1
        return counts
    
    def _calculate_frequencies(
        self, 
        counts: Dict[str, int], 
        total: int
    ) -> Dict[str, str]:
        """
        Calculate frequency percentages.
        
        Args:
            counts: Code count dictionary
            total: Total number of segments
            
        Returns:
            Dictionary mapping codes to formatted frequency strings
        """
        return {
            code: f"{count}/{total} ({count/total*100:.1f}%)"
            for code, count in counts.items()
        }
    
    def get_observation_count(self) -> int:
        """
        Get total number of observations recorded.
        
        Returns:
            Number of observation segments
        """
        return len(self.observations)
    
    def clear_observations(self) -> None:
        """Clear all recorded observations."""
        self.observations = []
        logger.info("Cleared all observations")
