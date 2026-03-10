"""
Reliability Metrics Module

Implements inter-rater reliability (IRR) metrics for COPUS observation validation
using scikit-learn for robust statistical calculations.

Based on methodology from Smith et al. (2013) COPUS paper.
"""

import logging
from typing import List, Dict, Set, Any, Tuple
from collections import Counter
import numpy as np
from sklearn.metrics import cohen_kappa_score


logger = logging.getLogger(__name__)


class COPUSReliabilityAnalyzer:
    """
    Analyzer for inter-rater reliability of COPUS observations.
    
    Calculates Jaccard similarity, Cohen's kappa, percent agreement,
    and performs disagreement analysis between two coders.
    
    Attributes:
        observations1: First coder's observations
        observations2: Second coder's observations
        coder1_name: Name/label for first coder
        coder2_name: Name/label for second coder
        n_segments: Number of observation segments
        all_codes: Set of all unique COPUS codes used by either coder
    """
    
    def __init__(
        self,
        observations1: List[Dict[str, Any]],
        observations2: List[Dict[str, Any]],
        coder1_name: str = "Coder 1",
        coder2_name: str = "Coder 2"
    ) -> None:
        """
        Initialize reliability analyzer with two sets of observations.
        
        Args:
            observations1: List of observation dicts from first coder
            observations2: List of observation dicts from second coder
            coder1_name: Name for first coder (for reporting)
            coder2_name: Name for second coder (for reporting)
            
        Raises:
            ValueError: If observation lists have different lengths
        """
        if len(observations1) != len(observations2):
            raise ValueError(
                f"Observation lists have different lengths: "
                f"{len(observations1)} vs {len(observations2)}"
            )
        
        self.observations1 = observations1
        self.observations2 = observations2
        self.coder1_name = coder1_name
        self.coder2_name = coder2_name
        self.n_segments = len(observations1)
        self.all_codes = self._collect_all_codes()
    
    def _collect_all_codes(self) -> List[str]:
        """
        Collect all unique COPUS codes used by either coder.
        
        Returns:
            Sorted list of unique codes
        """
        codes_set: Set[str] = set()
        
        for obs in self.observations1 + self.observations2:
            codes_set.update(obs.get("instructor_codes", []))
            codes_set.update(obs.get("student_codes", []))
        
        return sorted(list(codes_set))
    
    def _get_segment_codes(self, obs: Dict[str, Any]) -> Set[str]:
        """
        Extract all codes from a single observation segment.
        
        Args:
            obs: Observation dictionary
            
        Returns:
            Set of all codes (instructor + student)
        """
        instructor = obs.get("instructor_codes", [])
        student = obs.get("student_codes", [])
        return set(instructor + student)
    
    def calculate_jaccard_similarity(self) -> float:
        """
        Calculate average Jaccard similarity coefficient across all segments.
        
        Jaccard similarity = |A ∩ B| / |A ∪ B|
        Measures overlap between two code sets, ranges from 0 to 1.
        
        Returns:
            Average Jaccard similarity (0.0 to 1.0)
        """
        if self.n_segments == 0:
            return 0.0
        
        similarities = []
        
        for obs1, obs2 in zip(self.observations1, self.observations2):
            codes1 = self._get_segment_codes(obs1)
            codes2 = self._get_segment_codes(obs2)
            
            if len(codes1) == 0 and len(codes2) == 0:
                similarities.append(1.0)
            else:
                intersection = len(codes1 & codes2)
                union = len(codes1 | codes2)
                jaccard = intersection / union if union > 0 else 0.0
                similarities.append(jaccard)
        
        return sum(similarities) / len(similarities)
    
    def calculate_cohens_kappa(self) -> float:
        """
        Calculate Cohen's kappa coefficient using scikit-learn.
        
        Cohen's kappa measures inter-rater agreement adjusted for chance.
        Ranges from -1 (complete disagreement) to 1 (perfect agreement).
        
        Uses sklearn.metrics.cohen_kappa_score for robust calculation.
        
        Returns:
            Cohen's kappa coefficient (-1.0 to 1.0)
        """
        if self.n_segments == 0 or len(self.all_codes) == 0:
            return 0.0
        
        # Build binary presence matrix for each code
        # For each segment, create a binary vector indicating code presence
        coder1_vectors = []
        coder2_vectors = []
        
        for obs1, obs2 in zip(self.observations1, self.observations2):
            codes1 = self._get_segment_codes(obs1)
            codes2 = self._get_segment_codes(obs2)
            
            # Create binary vector for this segment
            vector1 = [1 if code in codes1 else 0 for code in self.all_codes]
            vector2 = [1 if code in codes2 else 0 for code in self.all_codes]
            
            coder1_vectors.append(vector1)
            coder2_vectors.append(vector2)
        
        # Flatten to 1D arrays for sklearn
        coder1_flat = np.array(coder1_vectors).flatten()
        coder2_flat = np.array(coder2_vectors).flatten()
        
        # Handle edge case: if arrays are identical and have only one unique value
        # sklearn returns NaN, but this should be perfect agreement (kappa=1.0)
        if np.array_equal(coder1_flat, coder2_flat):
            unique_values = np.unique(coder1_flat)
            if len(unique_values) == 1:
                return 1.0
        
        # Calculate Cohen's kappa using sklearn with explicit labels
        kappa = cohen_kappa_score(coder1_flat, coder2_flat, labels=[0, 1])
        
        # Handle NaN result (edge case in sklearn)
        if np.isnan(kappa):
            # If arrays are identical, treat as perfect agreement
            if np.array_equal(coder1_flat, coder2_flat):
                return 1.0
            else:
                return 0.0
        
        return float(kappa)
    
    def calculate_percent_agreement(self) -> float:
        """
        Calculate percentage of segments with perfect code agreement.
        
        A segment has perfect agreement if both coders recorded exactly
        the same set of codes (both instructor and student codes).
        
        Returns:
            Percentage of segments with perfect agreement (0.0 to 100.0)
        """
        if self.n_segments == 0:
            return 0.0
        
        perfect_matches = 0
        
        for obs1, obs2 in zip(self.observations1, self.observations2):
            codes1_instructor = set(obs1.get("instructor_codes", []))
            codes1_student = set(obs1.get("student_codes", []))
            codes2_instructor = set(obs2.get("instructor_codes", []))
            codes2_student = set(obs2.get("student_codes", []))
            
            if (codes1_instructor == codes2_instructor and 
                codes1_student == codes2_student):
                perfect_matches += 1
        
        return (perfect_matches / self.n_segments) * 100.0
    
    def analyze_disagreements(self) -> Dict[str, Any]:
        """
        Analyze segments where coders disagreed.
        
        Identifies segments with mismatches and provides detailed breakdown
        of which codes were marked differently.
        
        Returns:
            Dictionary containing:
                - disagreement_segments: List of segment numbers with disagreements
                - disagreement_count: Number of segments with disagreements
                - disagreement_details: List of dicts with details per segment
                - common_confusions: Counter of most common code confusions
        """
        disagreement_segments = []
        disagreement_details = []
        confusion_pairs = []
        
        for idx, (obs1, obs2) in enumerate(zip(self.observations1, self.observations2)):
            segment_num = obs1.get("segment", idx + 1)
            
            codes1 = self._get_segment_codes(obs1)
            codes2 = self._get_segment_codes(obs2)
            
            if codes1 != codes2:
                disagreement_segments.append(segment_num)
                
                only_coder1 = codes1 - codes2
                only_coder2 = codes2 - codes1
                both = codes1 & codes2
                
                detail = {
                    "segment": segment_num,
                    f"{self.coder1_name}_codes": list(codes1),
                    f"{self.coder2_name}_codes": list(codes2),
                    "agreement": list(both),
                    f"only_{self.coder1_name}": list(only_coder1),
                    f"only_{self.coder2_name}": list(only_coder2),
                    "jaccard": (len(both) / len(codes1 | codes2) 
                               if len(codes1 | codes2) > 0 else 0.0)
                }
                disagreement_details.append(detail)
                
                # Track confusion pairs
                for c1 in only_coder1:
                    for c2 in only_coder2:
                        confusion_pairs.append((c1, c2))
        
        common_confusions = Counter(confusion_pairs)
        
        return {
            "disagreement_segments": disagreement_segments,
            "disagreement_count": len(disagreement_segments),
            "disagreement_details": disagreement_details,
            "common_confusions": common_confusions.most_common(10)
        }
    
    @staticmethod
    def interpret_kappa(kappa: float) -> str:
        """
        Interpret Cohen's kappa value using Landis & Koch (1977) guidelines.
        
        Args:
            kappa: Cohen's kappa value
            
        Returns:
            Interpretation string
        """
        if kappa < 0.0:
            return "Poor (< 0.00)"
        elif kappa < 0.20:
            return "Slight (0.00-0.20)"
        elif kappa < 0.40:
            return "Fair (0.21-0.40)"
        elif kappa < 0.60:
            return "Moderate (0.41-0.60)"
        elif kappa < 0.80:
            return "Substantial (0.61-0.80)"
        else:
            return "Almost Perfect (0.81-1.00)"
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """
        Calculate all reliability metrics in one call.
        
        Convenience method that computes Jaccard, Cohen's kappa,
        percent agreement, and disagreement analysis.
        
        Returns:
            Dictionary with all metrics and analysis:
                - jaccard_similarity: Average Jaccard coefficient
                - cohens_kappa: Cohen's kappa coefficient
                - kappa_interpretation: Text interpretation of kappa
                - percent_agreement: Percentage of perfect matches
                - n_segments: Total number of segments compared
                - disagreements: Detailed disagreement analysis
                - coder1_name: Name of first coder
                - coder2_name: Name of second coder
        """
        jaccard = self.calculate_jaccard_similarity()
        kappa = self.calculate_cohens_kappa()
        agreement = self.calculate_percent_agreement()
        disagreements = self.analyze_disagreements()
        
        result = {
            "jaccard_similarity": round(jaccard, 3),
            "cohens_kappa": round(kappa, 3),
            "kappa_interpretation": self.interpret_kappa(kappa),
            "percent_agreement": round(agreement, 1),
            "n_segments": self.n_segments,
            "disagreements": disagreements,
            "coder1_name": self.coder1_name,
            "coder2_name": self.coder2_name
        }
        
        logger.info(f"Reliability Metrics ({self.coder1_name} vs {self.coder2_name}):")
        logger.info(f"  Jaccard Similarity: {result['jaccard_similarity']}")
        logger.info(f"  Cohen's Kappa: {result['cohens_kappa']} ({result['kappa_interpretation']})")
        logger.info(f"  Percent Agreement: {result['percent_agreement']}%")
        logger.info(f"  Segments Compared: {result['n_segments']}")
        logger.info(f"  Disagreements: {disagreements['disagreement_count']} segments")
        
        return result


class ConfusionMatrixBuilder:
    """
    Builder for confusion matrix showing code agreement patterns.
    
    Matrix[code1][code2] = count of times coder1 marked code1 and coder2 marked code2.
    Diagonal elements show agreement, off-diagonal show disagreements.
    
    Attributes:
        observations1: First coder's observations
        observations2: Second coder's observations
        all_codes: List of all unique codes
    """
    
    def __init__(
        self,
        observations1: List[Dict[str, Any]],
        observations2: List[Dict[str, Any]]
    ) -> None:
        """
        Initialize confusion matrix builder.
        
        Args:
            observations1: First coder's observations
            observations2: Second coder's observations
        """
        self.observations1 = observations1
        self.observations2 = observations2
        self.all_codes = self._collect_all_codes()
    
    def _collect_all_codes(self) -> List[str]:
        """Collect all unique codes from both coders."""
        codes_set: Set[str] = set()
        
        for obs in self.observations1 + self.observations2:
            codes_set.update(obs.get("instructor_codes", []))
            codes_set.update(obs.get("student_codes", []))
        
        return sorted(list(codes_set))
    
    def _get_segment_codes(self, obs: Dict[str, Any]) -> Set[str]:
        """Extract all codes from a segment."""
        instructor = obs.get("instructor_codes", [])
        student = obs.get("student_codes", [])
        return set(instructor + student)
    
    def build_matrix(self) -> Dict[str, Dict[str, int]]:
        """
        Generate confusion matrix.
        
        Returns:
            Nested dict representing confusion matrix:
            {code_from_coder1: {code_from_coder2: count}}
        """
        # Initialize matrix including 'absent' for codes not marked
        matrix: Dict[str, Dict[str, int]] = {
            code1: {code2: 0 for code2 in self.all_codes + ["absent"]}
            for code1 in self.all_codes + ["absent"]
        }
        
        # For each segment and each possible code, track what both coders marked
        for obs1, obs2 in zip(self.observations1, self.observations2):
            codes1 = self._get_segment_codes(obs1)
            codes2 = self._get_segment_codes(obs2)
            
            for code in self.all_codes:
                code1_marked = code in codes1
                code2_marked = code in codes2
                
                row_key = code if code1_marked else "absent"
                col_key = code if code2_marked else "absent"
                
                matrix[row_key][col_key] += 1
        
        return matrix


def calculate_all_metrics(
    observations1: List[Dict[str, Any]],
    observations2: List[Dict[str, Any]],
    coder1_name: str = "Coder 1",
    coder2_name: str = "Coder 2"
) -> Dict[str, Any]:
    """
    Convenience function to calculate all reliability metrics.
    
    Args:
        observations1: First coder's observations
        observations2: Second coder's observations
        coder1_name: Name for first coder
        coder2_name: Name for second coder
        
    Returns:
        Dictionary with all metrics (see COPUSReliabilityAnalyzer.calculate_all_metrics)
    """
    analyzer = COPUSReliabilityAnalyzer(
        observations1, observations2, coder1_name, coder2_name
    )
    return analyzer.calculate_all_metrics()
