# COPUS Classroom Simulation

AI-powered classroom simulation based on COPUS (Classroom Observation Protocol for Undergraduate STEM) to compare different teaching methods.

## Project Overview

This project simulates two distinct teaching scenarios with modular, professional architecture:

### Scenario 1: Lec-only (Lecture-based)
- **Instructor**: Lecturing only (COPUS code: Lec)
- **Students**: Listening and note-taking (COPUS code: L)
- **Characteristics**: Traditional, one-way instruction

### Scenario 2: PQ-only (Question-driven)
- **Instructor**: Posing questions (COPUS codes: PQ, FUp)
- **Students**: Answering and asking questions (COPUS codes: AnQ, SQ)
- **Characteristics**: High interaction, two-way engagement

## Installation

### 1. Create virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure API key

Copy `.env.template` to `.env` and add your API key:

```powershell
copy .env.template .env
```

Then edit the `.env` file and add:
- **DeepSeek API key** (recommended): https://platform.deepseek.com/
- OR **Google Gemini API key**: https://aistudio.google.com/app/apikey

## Run Simulation

```powershell
# Run the multi-agent classroom simulation
python main.py
```

## Run Tests

```powershell
# Run all tests with pytest
pytest tests/ -v

# Run specific test file
pytest tests/test_reliability_metrics.py -v

# Run with coverage
pytest tests/ --cov=multiagent_classroom --cov-report=html

## Module Responsibilities

### 1. `constants.py`
**Responsibility**: Centralized configuration management

- API configuration (DeepSeek, Google Gemini)
- Simulation parameters (turns, temperature, tokens)
- COPUS codes (instructor and student)
- Thresholds and file paths
- Logging configuration

### 2. `api_client.py`
**Responsibility**: API client initialization and management

**Classes**:
- `APIClient`: Manages API provider selection and client configuration

**Key Methods**:
- `initialize()`: Initialize API based on available keys
- `get_provider()`: Get current API provider
- `get_client()`: Get OpenAI client instance
- `get_model_name()`: Get current model name

### 3. `agent.py`
**Responsibility**: LLM agent interaction and conversation management

**Classes**:
- `SimpleAgent`: Agent for classroom simulation with LLM interaction

**Key Methods**:
- `generate_response()`: Generate response with retry logic
- `_generate_google_response()`: Handle Google Gemini API
- `_generate_deepseek_response()`: Handle DeepSeek/OpenAI API
- `_apply_context_window()`: Manage context size with sliding window
- `_handle_retry()`: Implement exponential backoff
- `clear_context()`: Reset conversation history

### 4. `observer.py`
**Responsibility**: COPUS observation recording and analysis

**Classes**:
- `COPUSObserver`: Records teaching activities using COPUS protocol

**Key Methods**:
- `observe_segment()`: Record 2-minute observation segment
- `get_summary()`: Generate frequency statistics
- `_count_instructor_codes()`: Count instructor COPUS codes
- `_count_student_codes()`: Count student COPUS codes
- `_calculate_frequencies()`: Calculate percentages
- `clear_observations()`: Reset observations

### 5. `scenarios.py`
**Responsibility**: Teaching scenario execution

**Classes**:
- `ScenarioExecutor`: Executes teaching scenarios with COPUS observation

**Key Methods**:
- `execute_lec_only()`: Run lecture-based scenario
- `execute_pq_only()`: Run question-driven scenario
- `_get_slide_content()`: Extract slide content
- `_get_slide_metadata()`: Extract topic and key term and inter-rater reliability

**Classes**:
- `TeachingEvaluator`: Evaluates teaching methods using COPUS metrics

**Key Methods**:
- `evaluate()`: Main evaluation orchestrator
- `compare_observers()`: Compare two observers using IRR metrics
- `_calculate_metrics()`: Calculate percentage metrics
- `_classify_classroom()`: Classify as DIDACTIC/INTERACTIVE/MIXED
- `_build_evaluation_result()`: Construct result dictionary
- `_log_irr_interpretation()`: Interpret Cohen's kappa values

### 6a. `reliability_metrics.py`
**Responsibility**: Inter-rater reliability (IRR) calculations

**Classes**:
- `COPUSReliabilityAnalyzer`: Calculates reliability metrics between two coders
- `ConfusionMatrixBuilder`: Builds confusion matrices for code comparisons

**Key Methods**:
- `calculate_jaccard_similarity()`: Compute Jaccard similarity coefficient
- `calculate_cohens_kappa()`: Compute Cohen's kappa using scikit-learn
- `calculate_percent_agreement()`: Calculate perfect match percentage
- `analyze_disagreements()`: Identify and analyze coding disagreements
- `calculate_all_metrics()`: Convenience method for all metrics at once
- `build_matrix()`: Generate confusion matrix for code patterns

**Statistical Metrics**:
- **Jaccard Similarity**: Measures code overlap between observers (0.0-1.0)
- **Cohen's Kappa**: Measures agreement adjusted for chance (-1.0 to 1.0)
- **Percent Agreement**: Percentage of segments with perfect code match
- **Disagreement Analysis**: Identifies segments and codes with mismatchesUS metrics

**Key Methods**:
- `evaluate()`: Main evaluation orchestrator
- `_calculate_metrics()`: Calculate percentage metrics
- `_classify_classroom()`: Classify as DIDACTIC/INTERACTIVE/MIXED
- `_build_evaluation_result()`: Construct result dictionary

### 7. `data_loader.py`
**Responsibility**: Data loading and validation

**Classes**:
- `DataLoader`: Loads and validates prompts and slides

**Key Methods**:
- `load_prompts()`: Load agent prompts from JSON
- `load_slides()`: Load slides data from JSON
- `load_all()`: Load both prompts and slides
- `_validate_prompts()`: Validate prompt structure
- `_validate_slides()`: Validate slide structure

### 8. `result_saver.py`
**Responsibility**: Results persistence

**Classes**:
- `ResultSaver`: Saves simulation results to files

**Key Methods**:
- `save_results()`: Save results to JSON
- `save_comparison()`: Save comparison to text file
- `_generate_timestamp()`: Generate timestamp string
- `_write_json_file()`: Write JSON data
- `_write_text_file()`: Write text data

### 9. `main.py`
**Responsibility**: Simulation orchestration

**Classes**:
- `COPUSSimulation`: Main simulation coordinator

**Key Methods**:
- `run()`: Execute complete simulation workflow
- `_initialize_components()`: Initialize API and load data
- `_create_agents()`: Create teacher and student agents
- `_run_scenario_1()`: Execute Scenario 1
- `_run_scenario_2()`: Execute Scenario 2
- `_save_and_display_results()`: Save and display results

## Output

After running, you will see:

1. **Console output**: 
   - Dialogue between instructor and students
   - COPUS codes for each 2-minute interval
   - Statistics and evaluation

2. **JSON file** in `results/` directory:
   - Detailed dialogue for each interval
   - COPUS code frequencies
   - Class type classification (Didactic/Interactive/Mixed)
   - Comparison between 2 scenarios
   - Filename format: `copus_simulation_YYYYMMDD_HHMMSS.json`

3. **Log file** in `logs/` directory:
   - Timestamped simulation execution log
   - API calls and agent interactions
   - COPUS observation recordings
   - Error messages and warnings
   - Filename format: `simulation_YYYYMMDD_HHMMSS.log`

## COPUS Codes Used

### Instructor
- **Lec**: Lecturing
- **PQ**: Posing Question
- **FUp**: Follow-up/Feedback
- **CQ**: Comprehension Question
- **AnQ**: Answering student questions
- **D/V**: Demo/Video
- **MG**: Moving & Guiding

### Student
- **L**: Listening/taking notes
- **AnQ**: Answering question
- **SQ**: Asking question
- **WC**: Whole Class discussion
- **Prd**: Prediction
- **Ind**: Individual thinking
- **CG**: Discussing clicker question
- **WG**: Working in groups

## Configuration

Edit values in `multiagent_classroom/constants.py`:

```python
TURNS_PER_SESSION = 5    # Number of 2-minute intervals (default: 5 = 10 minutes)
MAX_CONTEXT_TEACHER = 15  # Context window for instructor
MAX_CONTEXT_STUDENT = 10  # Context window for students
TEMValidation and Reliability

The system includes inter-rater reliability (IRR) analysis to validate COPUS coding accuracy:

### Observer Comparison

```python
from multiagent_classroom.evaluator import TeachingEvaluator
from multiagent_classroom.observer import COPUSObserver

# Create two observers
observer_human = COPUSObserver()
observer_agent = COPUSObserver()

# ... perform coding ...

# Compare observers
evaluator = TeachingEvaluator()
metrics = evaluator.compare_observers(
    observer_human, 
    observer_agent380 lines - Teaching evaluation + IRR analysis
- `reliability_metrics.py`: 520 lines - Inter-rater reliability metrics
- `data_loader.py`: 190 lines - Data loading/validation
- `result_saver.py`: 175 lines - Results persistence

**Entry Point**:
- `main.py`: 255 lines - Simulation orchestration

**Testing**:
- `tests/test_reliability_metrics.py`: 450+ lines - Comprehensive IRR testsilarity']}")
print(f"Cohen's Kappa: {metrics['cohens_kappa']}")
print(f"Interpretation: {metrics['kappa_interpretation']}")
print(f"Percent Agreement: {metrics['percent_agreement']}%")
```

### Reliability Metrics

Based on Smith et al. (2013) COPUS paper methodology:

- **Jaccard Similarity**: Measures code overlap (target: > 0.75)
- **Cohen's Kappa**: Agreement adjusted for chance (target: > 0.70 for "Substantial")
- **Percent Agreement**: Perfect segment matches (informative, not primary metric)

### Kappa Interpretation (Landis & Koch, 1977)

| Range | Interpretation |
|-------|----------------|
| < 0.00 | Poor |
| 0.00-0.20 | Slight |
| 0.21-0.40 | Fair |
| 0.41-0.60 | Moderate |
| 0.61-0.80 | Substantial |
| 0.81-1.00 | Almost Perfect |

## Benefits of Modular Architecture

1. **Maintainability**: Each module has clear boundaries and responsibilities
2. **Testability**: Individual modules can be tested in isolation with pytest
3. **Reusability**: Modules can be imported and used independently
4. **Scalability**: Easy to add new features without affecting existing code
5. **Readability**: Clear separation makes code easier to understand
6. **Single Responsibility**: Each function/class has one clear purpose
7. **Reliability**: IRR metrics ensure consistent COPUS coding across observers
### Adding a New Scenario
1. Add scenario method to `ScenarioExecutor` in `scenarios.py`
2. Create observation recording method
3. Update `COPUSSimulation` in `main.py` to run new scenario

###Development Status

### Completed (Phase 1)
- Core simulation engine with Teacher and Student agents
- Two baseline scenarios (Lec-only, PQ-only)
- COPUS observation recording and classification
- Inter-rater reliability metrics (Jaccard, Cohen's kappa)
- Comprehensive test suite with pytest
- Observer comparison functionality

### In Progress (Phase 2)
- Manual coding tool for human COPUS coding
- Validation experiments comparing Agent Observer vs Human Coder
- Disagreement analysis and Observer prompt refinement

### Planned (Phase 3+)
- Additional teaching scenarios (mixed methods, group work)
- Real-time observation dashboard
- Automated report generation with visualizations
- Multi-language support expansion
- Configuration file system (YAML/JSON)
- Database storage for longitudinal analysis

## Future Improvements

1. **Manual Coding Tool**: CLI/GUI for human COPUS coding to validate Agent Observer
2. **Validation Framework**: Systematic comparison of Agent vs Human coding
3. **Configuration File**: Move constants to YAML/JSON config file
4. **Plugin System**: Allow dynamic scenario loading
5. **Async Execution**: Run scenarios in parallel
6. **Web Interface**: Add Flask/FastAPI web UI with real-time observation
7. **Database Storage**: Store results in database instead of files
8. **Advanced Analytics**: Interactive visualizations with confusion matrices
9. **Report Generation**: Automated PDF/HTML reports with IRR metric
3. Add new

The project uses **pytest** for automated testing with comprehensive test coverage for reliability metrics.

### Test Structure

```
tests/
├── __init__.py                      # Test package
└── test_reliability_metrics.py     # IRR metrics tests (80+ test cases)
```

### Running Tests

```powershell
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_reliability_metrics.py::TestCOPUSReliabilityAnalyzer -v

# Run with coverage report
pytest tests/ --cov=multiagent_classroom --cov-report=html

# Run tests matching pattern
pytest tests/ -k "jaccard" -v
```

### Test Coverage

**`test_reliability_metrics.py`** includes:

1. **TestCOPUSReliabilityAnalyzer**: Initialization and configuration tests
2. **TestJaccardSimilarity**: Jaccard coefficient calculation tests
3. **TestCohensKappa**: Cohen's kappa calculation and interpretation tests
4. **TestPercentAgreement**: Perfect match percentage tests
5. **TestDisagreementAnalysis**: Disagreement identification and analysis tests
6. **TestCalculateAllMetrics**: Comprehensive metrics calculation tests
7. **TestConfusionMatrixBuilder**: Confusion matrix generation tests
8. **TestEvaluatorIntegration**: Integration tests with COPUSObserver
9. **TestConvenienceFunction**: Module-level convenience function tests

### Test Scenarios

Tests cover:
- Perfect agreement (kappa = 1.0)
- Partial agreement (0 < kappa < 1)
- No agreement (kappa = 0)
- Disagreement identification
- Edge cases (empty observations, mismatched lengths)
- Integration with COPUSObserver and TeachingEvaluator

### Future Tests

Planned test modules:
- `test_api_client.py`: API initialization and provider selection
- `test_agent.py`: LLM response generation and context management
- `test_observer.py`: COPUS code recording and summarization
- `test_scenarios.py`: Scenario execution and dialogue generation
- `test_evaluator.py`: Teaching method classification
- `test_data_loader.py`: Data loading and validation
- `test_integration.py`: End-to-end simulation workflowization and exports
- `constants.py`: 80 lines - Configuration constants
- `api_client.py`: 105 lines - API management
- `agent.py`: 210 lines - LLM agent implementation
- `observer.py`: 185 lines - COPUS observation
- `scenarios.py`: 390 lines - Scenario execution
- `evaluator.py`: 245 lines - Teaching evaluation
- `data_loader.py`: 190 lines - Data loading/validation
- `result_saver.py`: 175 lines - Results persistence

**Entry Point**:
- `main.py`: 255 lines - Simulation orchestration

## Testing Recommendations

1. **Unit Tests**: Test each module independently
   - `test_api_client.py`: Test API initialization
   - `test_agent.py`: Test response generation
   - `test_observer.py`: Test observation recording
   - `test_evaluator.py`: Test evaluation logic

2. **Integration Tests**: Test module interactions
   - Test scenario execution with mock agents
   - Test data loading and validation
   - Test results saving

3. **End-to-End Tests**: Test complete simulation workflow
   - Run full simulation with test data
   - Verify output files are created
   - Validate evaluation results

## Future Improvements

1. **Configuration File**: Move constants to YAML/JSON config file
2. **Plugin System**: Allow dynamic scenario loading
3. **Async Execution**: Run scenarios in parallel
4. **Web Interface**: Add Flask/FastAPI web UI
5. **Database Storage**: Store results in database instead of files
6. **Advanced Analytics**: Add visualization and statistical analysis

## References

- **COPUS Paper**: Smith et al. (2013) - "The Classroom Observation Protocol for Undergraduate STEM"
- **Original COPUS**: https://www.physport.org/methods/method.cfm?I=42

## License

See LICENSE file in the root directory.
