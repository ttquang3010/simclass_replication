"""
COPUS Classroom Simulation - Main Entry Point

Orchestrates the execution of classroom teaching scenarios with COPUS observation.
"""

import logging
from typing import Dict, List, Any, Optional

from multiagent_classroom import (
    APIClient,
    SimpleAgent,
    COPUSObserver,
    ScenarioExecutor,
    TeachingEvaluator,
    DataLoader,
    ResultSaver,
)
from multiagent_classroom import constants as const


# ============= Logging Setup =============
logging.basicConfig(
    level=logging.INFO,
    format=const.LOG_FORMAT,
    datefmt=const.LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)


class COPUSSimulation:
    """
    Main simulation coordinator for COPUS classroom scenarios.
    
    Manages the entire simulation lifecycle including initialization,
    scenario execution, evaluation, and results saving.
    """
    
    def __init__(self) -> None:
        """Initialize simulation components."""
        self.api_client: APIClient = APIClient()
        self.data_loader: DataLoader = DataLoader()
        self.evaluator: TeachingEvaluator = TeachingEvaluator()
        self.result_saver: ResultSaver = ResultSaver()
        
        self.api_provider: Optional[str] = None
        self.client: Optional[Any] = None
        self.model_name: str = ""
        self.prompts: Dict[str, Any] = {}
        self.slides: List[Dict[str, Any]] = []
        
        self.teacher: Optional[SimpleAgent] = None
        self.student_active: Optional[SimpleAgent] = None
        self.student_passive: Optional[SimpleAgent] = None
    
    def run(self) -> None:
        """
        Run the complete COPUS simulation.
        
        Executes initialization, scenario execution, evaluation,
        and results saving in sequence.
        """
        self._print_header()
        self._initialize_components()
        self._create_agents()
        
        results: Dict[str, Dict[str, Any]] = {}
        
        # Run Scenario 1
        eval1: Dict[str, Any] = self._run_scenario_1(results)
        
        # Pause before Scenario 2
        self._pause_between_scenarios()
        
        # Run Scenario 2
        eval2: Dict[str, Any] = self._run_scenario_2(results)
        
        # Save and display results
        self._save_and_display_results(results, eval1, eval2)
        
        self._print_completion()
    
    def _initialize_components(self) -> None:
        """Initialize API client and load data."""
        self.api_provider, self.client, self.model_name = self.api_client.initialize()
        self.prompts, self.slides = self.data_loader.load_all()
        
        logger.info(f"[OK] Loaded {len(self.slides)} slides")
        logger.info(
            f"[OK] Simulation: {const.TURNS_PER_SESSION} segments × 2 min = "
            f"{const.TURNS_PER_SESSION*2} min"
        )
    
    def _create_agents(self) -> None:
        """Create teacher and student agents."""
        self.teacher = self._create_agent("teacher", const.MAX_CONTEXT_TEACHER)
        self.student_active = self._create_agent("student_active", const.MAX_CONTEXT_STUDENT)
        self.student_passive = self._create_agent("student_passive", const.MAX_CONTEXT_STUDENT)
        
        logger.info("[OK] Created agents: Teacher, Active Student, Passive Student")
    
    def _create_agent(self, agent_type: str, max_context: int) -> SimpleAgent:
        """
        Create a single agent.
        
        Args:
            agent_type: Type of agent (teacher, student_active, student_passive)
            max_context: Maximum context window size
            
        Returns:
            Configured SimpleAgent instance
        """
        prompt_data: Dict[str, Any] = self.prompts[agent_type]
        
        return SimpleAgent(
            name=prompt_data["name"],
            system_prompt=prompt_data["system_prompt"],
            model_name=self.model_name,
            api_provider=self.api_provider,
            client=self.client,
            max_context=max_context
        )
    
    def _run_scenario_1(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run Scenario 1: Lec-only.
        
        Args:
            results: Results dictionary to populate
            
        Returns:
            Evaluation results for scenario 1
        """
        observer1: COPUSObserver = COPUSObserver()
        executor1: ScenarioExecutor = ScenarioExecutor(observer1)
        
        log1: List[Dict[str, Any]] = executor1.execute_lec_only(self.teacher, self.slides)
        summary1: Dict[str, Any] = observer1.get_summary()
        eval1: Dict[str, Any] = self.evaluator.evaluate(summary1, "Scenario 1: Lec-only")
        
        results["scenario1_lec_only"] = {
            "log": log1,
            "copus_summary": summary1,
            "evaluation": eval1
        }
        
        return eval1
    
    def _run_scenario_2(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run Scenario 2: PQ-only.
        
        Args:
            results: Results dictionary to populate
            
        Returns:
            Evaluation results for scenario 2
        """
        observer2: COPUSObserver = COPUSObserver()
        executor2: ScenarioExecutor = ScenarioExecutor(observer2)
        
        log2: List[Dict[str, Any]] = executor2.execute_pq_only(
            self.teacher, 
            self.student_active, 
            self.student_passive, 
            self.slides
        )
        summary2: Dict[str, Any] = observer2.get_summary()
        eval2: Dict[str, Any] = self.evaluator.evaluate(summary2, "Scenario 2: PQ-only")
        
        results["scenario2_pq_only"] = {
            "log": log2,
            "copus_summary": summary2,
            "evaluation": eval2
        }
        
        return eval2
    
    def _save_and_display_results(
        self,
        results: Dict[str, Dict[str, Any]],
        eval1: Dict[str, Any],
        eval2: Dict[str, Any]
    ) -> None:
        """
        Save results to files and display comparison.
        
        Args:
            results: Complete results dictionary
            eval1: Scenario 1 evaluation
            eval2: Scenario 2 evaluation
        """
        output_file: str = self.result_saver.save_results(results)
        logger.info(f"\n[SUCCESS] Results saved to: {output_file}")
        
        self._display_comparison(eval1, eval2)
    
    def _display_comparison(
        self, 
        eval1: Dict[str, Any], 
        eval2: Dict[str, Any]
    ) -> None:
        """
        Display comparison of two scenarios.
        
        Args:
            eval1: Scenario 1 evaluation
            eval2: Scenario 2 evaluation
        """
        logger.info("\n" + "="*60)
        logger.info("COMPARISON OF 2 SCENARIOS")
        logger.info("="*60)
        
        logger.info(f"\nScenario 1 (Lec-only): {eval1['classroom_type']}")
        logger.info(f"  - Lecturing: {eval1['lec_percentage']:.1f}%")
        logger.info(f"  - Student Listening: {eval1['student_listening_percentage']:.1f}%")
        
        logger.info(f"\nScenario 2 (PQ-only): {eval2['classroom_type']}")
        logger.info(f"  - Asking Questions: {eval2['pq_percentage']:.1f}%")
        logger.info(f"  - Student Answering: {eval2['student_answering_percentage']:.1f}%")
        logger.info(f"  - Student Asking: {eval2['student_asking_percentage']:.1f}%")
    
    def _print_header(self) -> None:
        """Print simulation header."""
        logger.info("="*60)
        logger.info("COPUS CLASSROOM SIMULATION")
        logger.info("="*60)
    
    def _print_completion(self) -> None:
        """Print simulation completion message."""
        logger.info("\n" + "="*60)
        logger.info("[DONE] Simulation completed!")
        logger.info("="*60)
    
    def _pause_between_scenarios(self) -> None:
        """Pause for user input between scenarios."""
        logger.info("\n" + "[PAUSE] "*30)
        input("Press Enter to continue to Scenario 2...")


def main() -> None:
    """
    Main entry point for COPUS classroom simulation.
    
    Creates and runs the simulation coordinator.
    """
    simulation = COPUSSimulation()
    simulation.run()


if __name__ == "__main__":
    main()
