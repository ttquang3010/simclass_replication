"""
Evaluator Module

Evaluates teaching effectiveness based on COPUS metrics.
"""

import logging
from typing import Dict, Any, Optional

from . import constants as const


logger = logging.getLogger(__name__)


class TeachingEvaluator:
    """
    Evaluates teaching methods using COPUS observation data.
    
    Classifies teaching as DIDACTIC, INTERACTIVE, or MIXED based on
    instructor and student activity patterns.
    """
    
    def __init__(self) -> None:
        """Initialize teaching evaluator."""
        pass
    
    def evaluate(
        self, 
        copus_summary: Dict[str, Any], 
        scenario_name: str
    ) -> Dict[str, Any]:
        """
        Evaluate teaching effectiveness based on COPUS metrics.
        
        Args:
            copus_summary: COPUS summary with instructor/student counts
            scenario_name: Name of the scenario being evaluated
            
        Returns:
            Evaluation results dictionary containing:
                - scenario: Scenario name
                - classroom_type: Classification
                - Various percentage metrics
        """
        self._log_evaluation_header(scenario_name)
        
        instructor_counts: Dict[str, int] = copus_summary["instructor_counts"]
        student_counts: Dict[str, int] = copus_summary["student_counts"]
        total: int = copus_summary["total_segments"]
        
        self._log_segment_count(total)
        self._log_instructor_activities(instructor_counts, total)
        self._log_student_activities(student_counts, total)
        
        metrics: Dict[str, float] = self._calculate_metrics(
            instructor_counts, student_counts, total
        )
        
        self._log_analysis(metrics)
        
        classroom_type: str = self._classify_classroom(metrics)
        self._log_classification(classroom_type)
        
        return self._build_evaluation_result(scenario_name, classroom_type, metrics)
    
    def _calculate_metrics(
        self,
        instructor_counts: Dict[str, int],
        student_counts: Dict[str, int],
        total: int
    ) -> Dict[str, float]:
        """
        Calculate key teaching metrics percentages.
        
        Args:
            instructor_counts: Instructor COPUS code counts
            student_counts: Student COPUS code counts
            total: Total number of segments
            
        Returns:
            Dictionary of metric percentages
        """
        return {
            "lec_pct": instructor_counts.get("Lec", 0) / total * 100,
            "pq_pct": instructor_counts.get("PQ", 0) / total * 100,
            "l_pct": student_counts.get("L", 0) / total * 100,
            "anq_pct": student_counts.get("AnQ", 0) / total * 100,
            "sq_pct": student_counts.get("SQ", 0) / total * 100
        }
    
    def _classify_classroom(self, metrics: Dict[str, float]) -> str:
        """
        Classify classroom type based on metrics.
        
        Args:
            metrics: Teaching metrics dictionary
            
        Returns:
            Classroom type classification string
        """
        lec_pct: float = metrics["lec_pct"]
        pq_pct: float = metrics["pq_pct"]
        l_pct: float = metrics["l_pct"]
        anq_pct: float = metrics["anq_pct"]
        sq_pct: float = metrics["sq_pct"]
        
        if (lec_pct > const.DIDACTIC_THRESHOLD and 
            l_pct > const.DIDACTIC_THRESHOLD):
            return "DIDACTIC (Truyền thống)"
        elif (pq_pct > const.INTERACTIVE_THRESHOLD and 
              (anq_pct + sq_pct) > const.INTERACTIVE_THRESHOLD):
            return "INTERACTIVE (Tương tác)"
        else:
            return "MIXED (Kết hợp)"
    
    def _build_evaluation_result(
        self,
        scenario_name: str,
        classroom_type: str,
        metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Build evaluation result dictionary.
        
        Args:
            scenario_name: Scenario name
            classroom_type: Classroom classification
            metrics: Teaching metrics
            
        Returns:
            Complete evaluation result dictionary
        """
        return {
            "scenario": scenario_name,
            "classroom_type": classroom_type,
            "lec_percentage": metrics["lec_pct"],
            "pq_percentage": metrics["pq_pct"],
            "student_listening_percentage": metrics["l_pct"],
            "student_answering_percentage": metrics["anq_pct"],
            "student_asking_percentage": metrics["sq_pct"]
        }
    
    def _log_evaluation_header(self, scenario_name: str) -> None:
        """Log evaluation header."""
        logger.info("="*60)
        logger.info(f"COPUS EVALUATION - {scenario_name}")
        logger.info("="*60)
    
    def _log_segment_count(self, total: int) -> None:
        """Log total segment count."""
        logger.info(f"Total observation segments: {total} (2 minutes each)")
    
    def _log_instructor_activities(
        self, 
        instructor_counts: Dict[str, int], 
        total: int
    ) -> None:
        """
        Log instructor activities.
        
        Args:
            instructor_counts: Instructor code counts
            total: Total segments
        """
        logger.info("\nINSTRUCTOR ACTIVITIES:")
        for code, count in instructor_counts.items():
            desc: str = const.INSTRUCTOR_CODES.get(code, "Unknown")
            pct: float = count/total*100
            logger.info(f"  {code} ({desc}): {count}/{total} ({pct:.1f}%)")
    
    def _log_student_activities(
        self, 
        student_counts: Dict[str, int], 
        total: int
    ) -> None:
        """
        Log student activities.
        
        Args:
            student_counts: Student code counts
            total: Total segments
        """
        logger.info("\nSTUDENT ACTIVITIES:")
        for code, count in student_counts.items():
            desc: str = const.STUDENT_CODES.get(code, "Unknown")
            pct: float = count/total*100
            logger.info(f"  {code} ({desc}): {count}/{total} ({pct:.1f}%)")
    
    def _log_analysis(self, metrics: Dict[str, float]) -> None:
        """
        Log teaching method analysis.
        
        Args:
            metrics: Teaching metrics
        """
        logger.info("\nANALYSIS:")
        
        if metrics["lec_pct"] > const.DIDACTIC_THRESHOLD:
            self._log_traditional_method(metrics)
        
        if metrics["pq_pct"] > const.DIDACTIC_THRESHOLD:
            self._log_interactive_method(metrics)
    
    def _log_traditional_method(self, metrics: Dict[str, float]) -> None:
        """Log traditional teaching method characteristics."""
        logger.info(
            f"  [MARK] Teaching method: TRADITIONAL (Lec: {metrics['lec_pct']:.0f}%)"
        )
        logger.info(f"    - Teacher primarily lectures")
        logger.info(f"    - Students primarily listen (L: {metrics['l_pct']:.0f}%)")
        logger.info(f"    - Low interaction")
    
    def _log_interactive_method(self, metrics: Dict[str, float]) -> None:
        """Log interactive teaching method characteristics."""
        logger.info(
            f"  [MARK] Teaching method: HIGH INTERACTION (PQ: {metrics['pq_pct']:.0f}%)"
        )
        logger.info(f"    - Teacher poses many questions")
        logger.info(
            f"    - Students actively answer (AnQ: {metrics['anq_pct']:.0f}%)"
        )
        if metrics["sq_pct"] > 0:
            logger.info(f"    - Students ask back (SQ: {metrics['sq_pct']:.0f}%)")
    
    def _log_classification(self, classroom_type: str) -> None:
        """
        Log classroom classification.
        
        Args:
            classroom_type: Classroom type classification
        """
        logger.info(f"\nCOPUS CLASSIFICATION:")
        logger.info(f"  Class type: {classroom_type}")
        
        if "DIDACTIC" in classroom_type:
            logger.info(f"  Characteristics: Teacher talks, students listen")
        elif "INTERACTIVE" in classroom_type:
            logger.info(f"  Characteristics: Q&A, discussion, two-way interaction")
    
    def compare_observers(
        self,
        observer1: Any,
        observer2: Any,
        coder1_name: str = "Observer 1",
        coder2_name: str = "Observer 2"
    ) -> Dict[str, Any]:
        """
        Compare two observers' COPUS coding using inter-rater reliability metrics.
        
        Calculates Jaccard similarity, Cohen's kappa, and percent agreement
        between two observers' observations. Based on methodology from
        Smith et al. (2013) COPUS paper.
        
        Args:
            observer1: First COPUSObserver instance (or any object with .observations list)
            observer2: Second COPUSObserver instance
            coder1_name: Name/label for first observer (default: "Observer 1")
            coder2_name: Name/label for second observer (default: "Observer 2")
            
        Returns:
            Dictionary containing all reliability metrics:
                - jaccard_similarity: Average Jaccard coefficient (0.0-1.0)
                - cohens_kappa: Cohen's kappa coefficient (-1.0 to 1.0)
                - kappa_interpretation: Text interpretation (e.g., "Substantial")
                - percent_agreement: Percentage of perfect matches (0-100)
                - n_segments: Number of segments compared
                - disagreements: Detailed analysis of disagreement segments
                - coder1_name: Name of first coder
                - coder2_name: Name of second coder
                
        Raises:
            ValueError: If observers have different numbers of observations
            AttributeError: If observers don't have .observations attribute
            
        Example:
            >>> evaluator = TeachingEvaluator()
            >>> observer_human = COPUSObserver()
            >>> observer_agent = COPUSObserver()
            >>> # ... run coding ...
            >>> metrics = evaluator.compare_observers(
            ...     observer_human, observer_agent,
            ...     coder1_name="Human", coder2_name="Agent"
            ... )
            >>> print(f"Kappa: {metrics['cohens_kappa']}")
        """
        # Get observations from both observers
        try:
            obs1: list = observer1.observations
            obs2: list = observer2.observations
        except AttributeError as e:
            raise AttributeError(
                f"Observers must have .observations attribute. "
                f"Error: {str(e)}"
            )
        
        # Validate observation counts match
        if len(obs1) != len(obs2):
            raise ValueError(
                f"Observers have different numbers of observations: "
                f"{coder1_name}={len(obs1)}, {coder2_name}={len(obs2)}. "
                f"Both observers must code the same segments."
            )
        
        if len(obs1) == 0:
            logger.warning("No observations to compare.")
            return {
                "jaccard_similarity": 0.0,
                "cohens_kappa": 0.0,
                "kappa_interpretation": "No data",
                "percent_agreement": 0.0,
                "n_segments": 0,
                "disagreements": {
                    "disagreement_segments": [],
                    "disagreement_count": 0,
                    "disagreement_details": [],
                    "common_confusions": []
                },
                "coder1_name": coder1_name,
                "coder2_name": coder2_name
            }
        
        # Import reliability_metrics locally to avoid circular import
        from . import reliability_metrics
        
        # Calculate all reliability metrics
        logger.info("="*60)
        logger.info(f"INTER-RATER RELIABILITY ANALYSIS")
        logger.info(f"Comparing: {coder1_name} vs {coder2_name}")
        logger.info("="*60)
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(
            obs1, obs2, coder1_name, coder2_name
        )
        metrics: Dict[str, Any] = analyzer.calculate_all_metrics()
        
        # Log summary
        logger.info("\n" + "="*60)
        logger.info("SUMMARY:")
        logger.info(f"  Jaccard Similarity: {metrics['jaccard_similarity']:.3f}")
        logger.info(
            f"  Cohen's Kappa: {metrics['cohens_kappa']:.3f} "
            f"({metrics['kappa_interpretation']})"
        )
        logger.info(f"  Percent Agreement: {metrics['percent_agreement']:.1f}%")
        logger.info(f"  Segments with Disagreement: {metrics['disagreements']['disagreement_count']}")
        
        # Interpretation guidance
        self._log_irr_interpretation(metrics['cohens_kappa'])
        
        # Log top confusions if any
        if metrics['disagreements']['common_confusions']:
            logger.info("\n  Top Code Confusions:")
            for (code1, code2), count in metrics['disagreements']['common_confusions'][:5]:
                logger.info(f"    {coder1_name}={code1} vs {coder2_name}={code2}: {count} times")
        
        logger.info("="*60)
        
        return metrics
    
    def _log_irr_interpretation(self, kappa: float) -> None:
        """
        Log interpretation guidance for Cohen's kappa value.
        
        Args:
            kappa: Cohen's kappa coefficient
        """
        logger.info("\n  Interpretation Guidance (Landis & Koch, 1977):")
        
        if kappa >= 0.81:
            logger.info("  [EXCELLENT] Almost perfect agreement")
            logger.info("    Observer coding is highly reliable.")
        elif kappa >= 0.61:
            logger.info("  [GOOD] Substantial agreement")
            logger.info("    Observer coding is reliable and acceptable.")
        elif kappa >= 0.41:
            logger.info("  [MODERATE] Moderate agreement")
            logger.info("    Consider refining observer training or code definitions.")
        elif kappa >= 0.21:
            logger.info("  [FAIR] Fair agreement")
            logger.info("    Significant improvement needed in observer training.")
        else:
            logger.info("  [POOR] Slight or no agreement")
            logger.info("    Review observer protocol and code definitions urgently.")

