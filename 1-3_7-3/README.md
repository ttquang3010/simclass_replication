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

## Architecture

```
1-3_7-3/
├── multiagent_classroom/   # Main package
│   ├── __init__.py         # Package initialization
│   ├── constants.py        # Configuration constants
│   ├── api_client.py       # API initialization and management
│   ├── agent.py            # LLM agent implementation
│   ├── observer.py         # COPUS observation recording
│   ├── scenarios.py        # Teaching scenario execution
│   ├── evaluator.py        # Teaching effectiveness evaluation
│   ├── data_loader.py      # Data loading and validation
│   └── result_saver.py     # Results persistence
├── legacy/                 # Archived code
│   └── copus_simulation.py # Original monolithic version
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .env.template           # Template for API keys
├── README.md               # This file
├── data/
│   ├── linear_regression_slides.json   # Lecture content (10 slides)
│   └── agent_prompts_vi.json           # Agent prompts (Vietnamese)
├── results/
│   └── copus_simulation_*.json         # Simulation results
└── copus/
    └── ...                              # COPUS documentation
```

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
- `_get_slide_metadata()`: Extract topic and key terms
- `_generate_lecture()`: Generate teacher lecture
- `_generate_question()`: Generate teacher question
- `_get_student_response()`: Coordinate student responses

### 6. `evaluator.py`
**Responsibility**: Teaching effectiveness evaluation

**Classes**:
- `TeachingEvaluator`: Evaluates teaching methods using COPUS metrics

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
TEMPERATURE = 0.7         # AI creativity level
MAX_TOKENS = 500          # Response length
DIDACTIC_THRESHOLD = 80.0    # Threshold for didactic classification
INTERACTIVE_THRESHOLD = 50.0  # Threshold for interactive classification
```

## Extending the System

### Adding a New Scenario
1. Add scenario method to `ScenarioExecutor` in `scenarios.py`
2. Create observation recording method
3. Update `COPUSSimulation` in `main.py` to run new scenario

### Adding a New Agent Type
1. Add prompt to `data/agent_prompts_vi.json`
2. Update `_validate_prompts()` in `data_loader.py`
3. Create agent in `_create_agents()` in `main.py`

### Customizing Evaluation
1. Modify classification logic in `TeachingEvaluator._classify_classroom()`
2. Update thresholds in `constants.py`
3. Add new metrics in `_calculate_metrics()`

## Benefits of Modular Architecture

1. **Maintainability**: Each module has clear boundaries and responsibilities
2. **Testability**: Individual modules can be tested in isolation
3. **Reusability**: Modules can be imported and used independently
4. **Scalability**: Easy to add new features without affecting existing code
5. **Readability**: Clear separation makes code easier to understand
6. **Single Responsibility**: Each function/class has one clear purpose

## Migration from Legacy Version

The legacy `copus_simulation.py` (664 lines, monolithic) has been refactored into a professional Python package:

**Package Structure** (`multiagent_classroom/`):
- `__init__.py`: Package initialization and exports
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
