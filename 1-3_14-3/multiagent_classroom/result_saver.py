"""
Result Saver Module

Handles saving simulation results to files.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

from . import constants as const


logger = logging.getLogger(__name__)


class ResultSaver:
    """
    Manages saving simulation results to JSON files.
    """
    
    def __init__(self, output_dir: str = const.RESULTS_DIR) -> None:
        """
        Initialize result saver.
        
        Args:
            output_dir: Directory to save results
        """
        self.output_dir: str = output_dir
        self._ensure_output_dir_exists()
    
    def save_results(
        self, 
        results: Dict[str, Any], 
        timestamp: str = None
    ) -> str:
        """
        Save simulation results to JSON file.
        
        Args:
            results: Results dictionary to save
            timestamp: Optional timestamp string (generated if None)
            
        Returns:
            Path to saved file
        """
        if timestamp is None:
            timestamp = self._generate_timestamp()
        
        output_file: str = self._build_output_path(timestamp)
        
        self._write_json_file(output_file, results)
        logger.info(f"Results saved to: {output_file}")
        
        return output_file
    
    def save_comparison(
        self, 
        eval1: Dict[str, Any], 
        eval2: Dict[str, Any],
        timestamp: str = None
    ) -> str:
        """
        Save scenario comparison to text file.
        
        Args:
            eval1: Evaluation results for scenario 1
            eval2: Evaluation results for scenario 2
            timestamp: Optional timestamp string
            
        Returns:
            Path to saved file
        """
        if timestamp is None:
            timestamp = self._generate_timestamp()
        
        output_file: str = self._build_comparison_path(timestamp)
        comparison_text: str = self._format_comparison(eval1, eval2)
        
        self._write_text_file(output_file, comparison_text)
        logger.info(f"Comparison saved to: {output_file}")
        
        return output_file
    
    def _ensure_output_dir_exists(self) -> None:
        """Create output directory if it doesn't exist."""
        os.makedirs(self.output_dir, exist_ok=True)
        logger.debug(f"Output directory ready: {self.output_dir}")
    
    def _generate_timestamp(self) -> str:
        """
        Generate timestamp string.
        
        Returns:
            Timestamp in format YYYYMMDD_HHMMSS
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _build_output_path(self, timestamp: str) -> str:
        """
        Build output file path.
        
        Args:
            timestamp: Timestamp string
            
        Returns:
            Full path to output file
        """
        filename: str = f"copus_simulation_{timestamp}.json"
        return os.path.join(self.output_dir, filename)
    
    def _build_comparison_path(self, timestamp: str) -> str:
        """
        Build comparison file path.
        
        Args:
            timestamp: Timestamp string
            
        Returns:
            Full path to comparison file
        """
        filename: str = f"comparison_{timestamp}.txt"
        return os.path.join(self.output_dir, filename)
    
    def _write_json_file(self, file_path: str, data: Dict[str, Any]) -> None:
        """
        Write data to JSON file.
        
        Args:
            file_path: Path to output file
            data: Data to write
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to write JSON file {file_path}: {e}")
            raise
    
    def _write_text_file(self, file_path: str, text: str) -> None:
        """
        Write text to file.
        
        Args:
            file_path: Path to output file
            text: Text to write
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            logger.error(f"Failed to write text file {file_path}: {e}")
            raise
    
    def _format_comparison(
        self, 
        eval1: Dict[str, Any], 
        eval2: Dict[str, Any]
    ) -> str:
        """
        Format comparison text.
        
        Args:
            eval1: Scenario 1 evaluation
            eval2: Scenario 2 evaluation
            
        Returns:
            Formatted comparison string
        """
        lines: list[str] = [
            "="*60,
            "COMPARISON OF 2 SCENARIOS",
            "="*60,
            "",
            f"Scenario 1 (Lec-only): {eval1['classroom_type']}",
            f"  - Lecturing: {eval1['lec_percentage']:.1f}%",
            f"  - Student Listening: {eval1['student_listening_percentage']:.1f}%",
            "",
            f"Scenario 2 (PQ-only): {eval2['classroom_type']}",
            f"  - Asking Questions: {eval2['pq_percentage']:.1f}%",
            f"  - Student Answering: {eval2['student_answering_percentage']:.1f}%",
            f"  - Student Asking: {eval2['student_asking_percentage']:.1f}%",
            "",
            "="*60
        ]
        return "\n".join(lines)
    
    def get_output_dir(self) -> str:
        """
        Get output directory path.
        
        Returns:
            Output directory path
        """
        return self.output_dir
