"""
Pytest Test Suite for Reliability Metrics Module

Tests inter-rater reliability metrics including Jaccard similarity,
Cohen's kappa, percent agreement, and disagreement analysis.

Run with: pytest tests/test_reliability_metrics.py -v
"""

import pytest
from multiagent_classroom import reliability_metrics
from multiagent_classroom.observer import COPUSObserver
from multiagent_classroom.evaluator import TeachingEvaluator


class TestCOPUSReliabilityAnalyzer:
    """Test suite for COPUSReliabilityAnalyzer class."""
    
    def test_initialization_valid(self):
        """Test successful initialization with valid observations."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(
            obs1, obs2, "Observer A", "Observer B"
        )
        
        assert analyzer.coder1_name == "Observer A"
        assert analyzer.coder2_name == "Observer B"
        assert analyzer.n_segments == 2
        assert "Lec" in analyzer.all_codes
        assert "L" in analyzer.all_codes
        assert "PQ" in analyzer.all_codes
        assert "AnQ" in analyzer.all_codes
    
    def test_initialization_mismatched_lengths(self):
        """Test that initialization fails with mismatched observation lengths."""
        obs1 = [{"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]}]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        
        with pytest.raises(ValueError, match="different lengths"):
            reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
    
    def test_collect_all_codes(self):
        """Test that all unique codes are collected from both observers."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec", "RtW"], "student_codes": ["L"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L", "SQ"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        
        assert "Lec" in analyzer.all_codes
        assert "RtW" in analyzer.all_codes
        assert "L" in analyzer.all_codes
        assert "SQ" in analyzer.all_codes
        assert len(analyzer.all_codes) == 4


class TestJaccardSimilarity:
    """Test suite for Jaccard similarity calculation."""
    
    def test_perfect_agreement(self):
        """Test Jaccard similarity with perfect agreement."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        jaccard = analyzer.calculate_jaccard_similarity()
        
        assert jaccard == 1.0, "Perfect agreement should yield Jaccard = 1.0"
    
    def test_no_overlap(self):
        """Test Jaccard similarity with no code overlap."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        jaccard = analyzer.calculate_jaccard_similarity()
        
        assert jaccard == 0.0, "No overlap should yield Jaccard = 0.0"
    
    def test_partial_overlap(self):
        """Test Jaccard similarity with partial code overlap."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["SQ"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        jaccard = analyzer.calculate_jaccard_similarity()
        
        assert 0.0 < jaccard < 1.0, "Partial overlap should be between 0 and 1"
        assert jaccard > 0.5, "Should have more than 50% overlap"


class TestCohensKappa:
    """Test suite for Cohen's kappa calculation."""
    
    def test_perfect_agreement(self):
        """Test Cohen's kappa with perfect agreement."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 3, "instructor_codes": ["Lec"], "student_codes": ["L"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 3, "instructor_codes": ["Lec"], "student_codes": ["L"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        kappa = analyzer.calculate_cohens_kappa()
        
        assert kappa > 0.95, "Perfect agreement should have kappa near 1.0"
    
    def test_moderate_agreement(self):
        """Test Cohen's kappa with moderate agreement."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
            {"segment": 3, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 4, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["SQ"]},
            {"segment": 3, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 4, "instructor_codes": ["Lec"], "student_codes": ["AnQ"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        kappa = analyzer.calculate_cohens_kappa()
        
        assert 0.0 <= kappa <= 1.0, "Kappa should be between 0 and 1"
    
    def test_kappa_interpretation(self):
        """Test interpretation strings for different kappa values."""
        analyzer_class = reliability_metrics.COPUSReliabilityAnalyzer
        
        assert "Poor" in analyzer_class.interpret_kappa(-0.1)
        assert "Slight" in analyzer_class.interpret_kappa(0.1)
        assert "Fair" in analyzer_class.interpret_kappa(0.3)
        assert "Moderate" in analyzer_class.interpret_kappa(0.5)
        assert "Substantial" in analyzer_class.interpret_kappa(0.7)
        assert "Almost Perfect" in analyzer_class.interpret_kappa(0.9)


class TestPercentAgreement:
    """Test suite for percent agreement calculation."""
    
    def test_full_agreement(self):
        """Test percent agreement with 100% agreement."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        agreement = analyzer.calculate_percent_agreement()
        
        assert agreement == 100.0
    
    def test_partial_agreement(self):
        """Test percent agreement with partial agreement."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
            {"segment": 3, "instructor_codes": ["Lec"], "student_codes": ["L"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["SQ"]},
            {"segment": 3, "instructor_codes": ["Lec"], "student_codes": ["L"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        agreement = analyzer.calculate_percent_agreement()
        
        assert abs(agreement - 66.7) < 0.1, "Expected ~66.7% agreement (2/3)"
    
    def test_no_agreement(self):
        """Test percent agreement with no perfect matches."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
            {"segment": 2, "instructor_codes": ["Lec"], "student_codes": ["SQ"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        agreement = analyzer.calculate_percent_agreement()
        
        assert agreement == 0.0


class TestDisagreementAnalysis:
    """Test suite for disagreement analysis."""
    
    def test_identify_disagreements(self):
        """Test identification of disagreement segments."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
            {"segment": 3, "instructor_codes": ["Lec", "PQ"], "student_codes": ["L", "AnQ"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["CQ"], "student_codes": ["AnQ"]},
            {"segment": 3, "instructor_codes": ["Lec"], "student_codes": ["L"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        analysis = analyzer.analyze_disagreements()
        
        assert analysis['disagreement_count'] == 2
        assert 2 in analysis['disagreement_segments']
        assert 3 in analysis['disagreement_segments']
    
    def test_disagreement_details(self):
        """Test detailed disagreement information."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["CQ"], "student_codes": ["SQ"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(
            obs1, obs2, "Coder A", "Coder B"
        )
        analysis = analyzer.analyze_disagreements()
        
        assert len(analysis['disagreement_details']) == 1
        detail = analysis['disagreement_details'][0]
        assert detail['segment'] == 2
        assert 'Coder A_codes' in detail
        assert 'Coder B_codes' in detail
    
    def test_common_confusions(self):
        """Test tracking of common code confusions."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["PQ"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["L"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["CQ"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["CQ"], "student_codes": ["L"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        analysis = analyzer.analyze_disagreements()
        
        assert len(analysis['common_confusions']) > 0
        most_common = analysis['common_confusions'][0]
        assert most_common[1] >= 2  # Count should be at least 2


class TestCalculateAllMetrics:
    """Test suite for calculate_all_metrics convenience method."""
    
    def test_all_metrics_returned(self):
        """Test that all expected metrics are calculated and returned."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["SQ"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        metrics = analyzer.calculate_all_metrics()
        
        assert 'jaccard_similarity' in metrics
        assert 'cohens_kappa' in metrics
        assert 'kappa_interpretation' in metrics
        assert 'percent_agreement' in metrics
        assert 'n_segments' in metrics
        assert 'disagreements' in metrics
        assert 'coder1_name' in metrics
        assert 'coder2_name' in metrics
    
    def test_metrics_values_valid(self):
        """Test that calculated metric values are within valid ranges."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        
        analyzer = reliability_metrics.COPUSReliabilityAnalyzer(obs1, obs2)
        metrics = analyzer.calculate_all_metrics()
        
        assert 0.0 <= metrics['jaccard_similarity'] <= 1.0
        assert -1.0 <= metrics['cohens_kappa'] <= 1.0
        assert 0.0 <= metrics['percent_agreement'] <= 100.0
        assert metrics['n_segments'] == 2


class TestConfusionMatrixBuilder:
    """Test suite for ConfusionMatrixBuilder class."""
    
    def test_build_matrix_structure(self):
        """Test that confusion matrix has correct structure."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["PQ"], "student_codes": ["AnQ"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
            {"segment": 2, "instructor_codes": ["CQ"], "student_codes": ["AnQ"]},
        ]
        
        builder = reliability_metrics.ConfusionMatrixBuilder(obs1, obs2)
        matrix = builder.build_matrix()
        
        assert isinstance(matrix, dict)
        assert "Lec" in matrix
        assert "PQ" in matrix
        assert "CQ" in matrix
        assert "absent" in matrix
    
    def test_matrix_diagonal_agreement(self):
        """Test that diagonal elements show code agreement."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
        ]
        
        builder = reliability_metrics.ConfusionMatrixBuilder(obs1, obs2)
        matrix = builder.build_matrix()
        
        # Both coders marked "Lec", so Lec-Lec should be > 0
        assert matrix["Lec"]["Lec"] > 0
        assert matrix["L"]["L"] > 0


class TestEvaluatorIntegration:
    """Test suite for evaluator integration with reliability metrics."""
    
    def test_compare_observers_basic(self):
        """Test basic observer comparison through evaluator."""
        observer1 = COPUSObserver()
        observer2 = COPUSObserver()
        
        for i in range(3):
            observer1.observe_segment(
                segment_number=i+1,
                teacher_action=["Lec"],
                student_actions=["L"]
            )
            observer2.observe_segment(
                segment_number=i+1,
                teacher_action=["Lec"],
                student_actions=["L"]
            )
        
        evaluator = TeachingEvaluator()
        metrics = evaluator.compare_observers(observer1, observer2)
        
        assert metrics['jaccard_similarity'] == 1.0
        assert metrics['cohens_kappa'] > 0.95
        assert metrics['percent_agreement'] == 100.0
    
    def test_compare_observers_with_disagreement(self):
        """Test observer comparison with some disagreements."""
        observer1 = COPUSObserver()
        observer2 = COPUSObserver()
        
        for i in range(5):
            if i == 2:
                observer1.observe_segment(
                    segment_number=i+1,
                    teacher_action=["Lec"],
                    student_actions=["L"]
                )
                observer2.observe_segment(
                    segment_number=i+1,
                    teacher_action=["Lec", "PQ"],
                    student_actions=["L"]
                )
            else:
                observer1.observe_segment(
                    segment_number=i+1,
                    teacher_action=["Lec"],
                    student_actions=["L"]
                )
                observer2.observe_segment(
                    segment_number=i+1,
                    teacher_action=["Lec"],
                    student_actions=["L"]
                )
        
        evaluator = TeachingEvaluator()
        metrics = evaluator.compare_observers(
            observer1, observer2,
            coder1_name="Human",
            coder2_name="Agent"
        )
        
        assert metrics['n_segments'] == 5
        assert metrics['disagreements']['disagreement_count'] == 1
        assert metrics['percent_agreement'] == 80.0
        assert metrics['coder1_name'] == "Human"
        assert metrics['coder2_name'] == "Agent"
    
    def test_compare_observers_mismatched_lengths(self):
        """Test that evaluator raises error for mismatched observation counts."""
        observer1 = COPUSObserver()
        observer2 = COPUSObserver()
        
        observer1.observe_segment(1, ["Lec"], ["L"])
        observer2.observe_segment(1, ["Lec"], ["L"])
        observer2.observe_segment(2, ["PQ"], ["AnQ"])
        
        evaluator = TeachingEvaluator()
        
        with pytest.raises(ValueError, match="different numbers of observations"):
            evaluator.compare_observers(observer1, observer2)


class TestConvenienceFunction:
    """Test suite for module-level convenience function."""
    
    def test_calculate_all_metrics_function(self):
        """Test convenience function for calculating all metrics."""
        obs1 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
        ]
        obs2 = [
            {"segment": 1, "instructor_codes": ["Lec"], "student_codes": ["L"]},
        ]
        
        metrics = reliability_metrics.calculate_all_metrics(
            obs1, obs2, "Observer A", "Observer B"
        )
        
        assert metrics['coder1_name'] == "Observer A"
        assert metrics['coder2_name'] == "Observer B"
        assert 'jaccard_similarity' in metrics
        assert 'cohens_kappa' in metrics
        assert 'percent_agreement' in metrics
