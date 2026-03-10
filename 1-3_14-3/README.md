# COPUS Classroom Simulation

AI-powered multi-agent classroom simulation based on COPUS (Classroom Observation Protocol for Undergraduate STEM) to compare different teaching methods.

## Project Overview

This project simulates two distinct teaching scenarios using LLM agents (teacher + students), records COPUS codes in 2-minute intervals, and evaluates teaching effectiveness using inter-rater reliability (IRR) metrics.

### Scenario 1: Lec-only (Lecture-based)
- **Instructor**: Lecturing (`Lec`)
- **Students**: Listening and note-taking (`L`)
- **Characteristics**: Traditional, one-way instruction

### Scenario 2: PQ-only (Question-driven)
- **Instructor**: Posing questions (`PQ`), answering student questions (`AnQ`)
- **Students**: Answering questions (`AnQ`), asking questions (`SQ`)
- **Characteristics**: High interaction, two-way engagement

---

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

---

## Run Simulation

```powershell
python main.py
```

The simulation will:
1. Run **Scenario 1 (Lec-only)** — pauses for user confirmation when done
2. Run **Scenario 2 (PQ-only)**
3. Save results and display a scenario comparison

---

## Run Tests

```powershell
# Run all tests with pytest
pytest tests/ -v

# Run specific test file
pytest tests/test_reliability_metrics.py -v

# Run with coverage
pytest tests/ --cov=multiagent_classroom --cov-report=html

# Run tests matching pattern
pytest tests/ -k "jaccard" -v
```

---

## Project Structure

```
1-3_14-3/
├── main.py                          # Entry point — COPUSSimulation orchestrator
├── multiagent_classroom/
│   ├── __init__.py
│   ├── constants.py                 # Centralized config
│   ├── api_client.py                # API client management
│   ├── agent.py                     # SimpleAgent (LLM wrapper)
│   ├── observer.py                  # COPUSObserver
│   ├── scenarios.py                 # ScenarioExecutor
│   ├── evaluator.py                 # TeachingEvaluator
│   ├── reliability_metrics.py       # IRR metrics
│   ├── data_loader.py               # DataLoader
│   └── result_saver.py              # ResultSaver
├── data/
│   ├── agent_prompts_vi.py          # Agent prompts (Vietnamese)
│   └── linear_regression_slides.json
├── tests/
│   └── test_reliability_metrics.py  # 80+ test cases
├── results/                         # JSON output files
└── logs/                            # Log files
```

---

## Module Responsibilities

### 1. `constants.py`
Centralized configuration for the entire project.

**Key values:**
```python
# API
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL    = "deepseek-chat"
GOOGLE_MODEL      = "gemini-1.5-flash"

# Simulation
TURNS_PER_SESSION = 15      # 15 × 2 min = 30-minute simulated class
TEMPERATURE       = 0.7
MAX_TOKENS        = 500
MAX_RETRIES       = 3
BRIEF_PAUSE       = 0.5     # seconds between segments

# Context windows
MAX_CONTEXT_TEACHER = 15
MAX_CONTEXT_STUDENT = 10

# Classification thresholds
DIDACTIC_THRESHOLD   = 80.0  # Lec > 80% and L > 80%
INTERACTIVE_THRESHOLD = 50.0  # PQ > 50% and (AnQ + SQ) > 50%

# File paths
AGENT_PROMPTS_MODULE = "data.agent_prompts_vi"
SLIDES_DATA_PATH     = "data/linear_regression_slides.json"
RESULTS_DIR          = "results"
LOGS_DIR             = "logs"
```

**Slide-to-segment mapping** (30-min class, 10 slides):
```python
SLIDE_SEGMENT_MAPPING = {
    1: 0,  2: 0,   # Slide 1 (Intro): 4 min
    3: 1,  4: 1,   # Slide 2 (Problem): 4 min
    5: 2,  6: 2,   # Slide 3 (Concept): 4 min
    7: 3,          # Slide 4 (Equation): 2 min
    8: 4,  9: 4,   # Slide 5 (Finding w,b): 4 min
    10: 5, 11: 5,  # Slide 6 (Gradient Descent): 4 min
    12: 6,         # Slide 7 (Code Demo): 2 min
    13: 7,         # Slide 8 (Applications): 2 min
    14: 8,         # Slide 9 (Limitations): 2 min
    15: 9          # Slide 10 (Summary): 2 min
}
```

---

### 2. `api_client.py`
**Class**: `APIClient`

Detects available API keys from environment and initializes the appropriate client.

| Method | Description |
|--------|-------------|
| `initialize()` | Returns `(provider, client, model_name, google_client)` |
| `get_provider()` | Current provider (`"deepseek"` or `"google"`) |
| `get_client()` | OpenAI-compatible client |
| `get_model_name()` | Model name string |

---

### 3. `agent.py`
**Class**: `SimpleAgent`

LLM-powered agent for classroom roles (teacher, active student, passive student).

| Method | Description |
|--------|-------------|
| `generate_response(prompt, temperature, max_tokens)` | Generate response with retry logic (exponential backoff) |
| `_generate_google_response(prompt)` | Handle Google Gemini chat API |
| `_generate_deepseek_response(prompt, temperature, max_tokens)` | Handle DeepSeek/OpenAI API with message history |
| `_apply_context_window()` | Sliding window: keep system prompt + last `max_context` messages |
| `_handle_retry(attempt, error)` | Exponential backoff (2^attempt seconds) |
| `get_context_size()` | Number of messages in history (DeepSeek only; 0 for Google) |
| `clear_context()` | Reset conversation history while preserving system prompt |

**Note**: Google Gemini manages history internally via a persistent chat session; DeepSeek/OpenAI uses an explicit `messages` list.

---

### 4. `observer.py`
**Class**: `COPUSObserver`

Records teaching activities using COPUS protocol in 2-minute intervals.

| Method | Description |
|--------|-------------|
| `observe_segment(segment_number, teacher_action, student_actions, description)` | Record one 2-min observation segment |
| `get_summary()` | Returns `{total_segments, instructor_frequency, student_frequency, instructor_counts, student_counts}` |
| `get_observation_count()` | Total recorded segments |
| `clear_observations()` | Reset all observations |

Frequencies are formatted as `"count/total (pct%)"`.

---

### 5. `scenarios.py`
**Class**: `ScenarioExecutor`

Executes teaching scenarios, driving the agents and calling the observer.

| Method | Description |
|--------|-------------|
| `execute_lec_only(teacher, slides)` | Run Scenario 1: teacher lectures each segment (`Lec`/`L`) |
| `execute_pq_only(teacher, student_active, student_passive, slides)` | Run Scenario 2: teacher poses questions; students alternate answering (`AnQ`) and asking (`SQ`) |
| `_get_slide_content(slides, turn)` | Look up slide content via `SLIDE_SEGMENT_MAPPING` |
| `_get_slide_metadata(slides, turn)` | Return `(topic, key_terms)` for current slide |

**Student turn alternation in PQ-only:**
- Even turns → `student_active` answers (`AnQ`)
- Odd turn 1 → `student_passive` asks a clarifying question (`SQ`)
- Other odd turns → `student_passive` gives an uncertain answer (`AnQ`)

**Class**: `TeachingEvaluator` *(lives in `evaluator.py`)*

---

### 6. `evaluator.py`
**Class**: `TeachingEvaluator`

Evaluates COPUS summary data and compares observers.

| Method | Description |
|--------|-------------|
| `evaluate(copus_summary, scenario_name)` | Compute metrics and classify classroom; returns evaluation dict |
| `compare_observers(observer1, observer2, coder1_name, coder2_name)` | Run full IRR analysis between two `COPUSObserver` instances |
| `_calculate_metrics(instructor_counts, student_counts, total)` | Returns `{lec_pct, pq_pct, l_pct, anq_pct, sq_pct}` |
| `_classify_classroom(metrics)` | Returns `"DIDACTIC"`, `"INTERACTIVE"`, or `"MIXED"` |
| `_build_evaluation_result(...)` | Constructs and returns final evaluation dict |
| `_log_irr_interpretation(kappa)` | Logs guidance text based on Landis & Koch (1977) |

**Classification rules:**
- **DIDACTIC**: `Lec > 80%` AND `L > 80%`
- **INTERACTIVE**: `PQ > 50%` AND `(AnQ + SQ) > 50%`
- **MIXED**: everything else

---

### 7. `reliability_metrics.py`
**Classes**: `COPUSReliabilityAnalyzer`, `ConfusionMatrixBuilder`

**`COPUSReliabilityAnalyzer`** — IRR between two coders:

| Method | Description |
|--------|-------------|
| `calculate_jaccard_similarity()` | `\|A∩B\| / \|A∪B\|` averaged over all segments (0–1) |
| `calculate_cohens_kappa()` | Via `sklearn.metrics.cohen_kappa_score` on binary presence vectors |
| `calculate_percent_agreement()` | % segments with identical instructor + student code sets |
| `analyze_disagreements()` | Per-segment breakdown; top confusions via `Counter` |
| `calculate_all_metrics()` | All of the above in one call |
| `interpret_kappa(kappa)` | Static method; Landis & Koch (1977) text labels |

**`ConfusionMatrixBuilder`** — `{code_coder1: {code_coder2: count}}` matrix including an `"absent"` category.

**Module-level convenience function:**
```python
calculate_all_metrics(observations1, observations2, coder1_name, coder2_name)
```

---

### 8. `data_loader.py`
**Class**: `DataLoader`

| Method | Description |
|--------|-------------|
| `load_prompts(module_name)` | Dynamically imports Python module and calls `get_all_agents()` |
| `load_slides(file_path, max_slides)` | Loads JSON; optionally limits number of slides |
| `load_all()` | Returns `(prompts, slides)` |
| `get_prompt(agent_name)` | Retrieve prompt for `"teacher"`, `"student_active"`, or `"student_passive"` |
| `get_slide(index)` | Retrieve slide by index |
| `get_slides_count()` | Number of loaded slides |

**Validations:**
- Prompts: requires `teacher`, `student_active`, `student_passive` keys, each with `system_prompt`
- Slides: each slide requires `title` and `content` fields

---

### 9. `result_saver.py`
**Class**: `ResultSaver`

| Method | Description |
|--------|-------------|
| `save_results(results, timestamp)` | Write full results dict to `results/copus_simulation_YYYYMMDD_HHMMSS.json` |
| `save_comparison(eval1, eval2, timestamp)` | Write text comparison to `results/comparison_YYYYMMDD_HHMMSS.txt` |
| `get_output_dir()` | Return output directory path |

---

### 10. `main.py`
**Class**: `COPUSSimulation`

Top-level orchestrator.

| Method | Description |
|--------|-------------|
| `run()` | Full simulation: header → init → agents → scenario 1 → pause → scenario 2 → save |
| `_initialize_components()` | API init + data loading |
| `_create_agents()` | Creates `teacher`, `student_active`, `student_passive` agents |
| `_run_scenario_1(results)` | Lec-only execution and evaluation |
| `_run_scenario_2(results)` | PQ-only execution and evaluation |
| `_save_and_display_results(results, eval1, eval2)` | Save JSON + log comparison |
| `_display_comparison(eval1, eval2)` | Log side-by-side comparison |
| `_pause_between_scenarios()` | `input("Press Enter to continue...")` |

**Module-level function**: `setup_logging()` — configures dual handlers (console + file in `logs/`).

---

## Agents

Three agents are created per simulation run:

| Agent | Role | Context Window |
|-------|------|---------------|
| `teacher` | Lectures or poses questions depending on scenario | `MAX_CONTEXT_TEACHER = 15` |
| `student_active` | Engaged student; provides answers | `MAX_CONTEXT_STUDENT = 10` |
| `student_passive` | Less engaged; asks questions or gives uncertain answers | `MAX_CONTEXT_STUDENT = 10` |

Prompts are loaded from `data/agent_prompts_vi.py` (Vietnamese language).

---

## COPUS Codes Used

### Instructor (11 codes)
| Code | Description |
|------|-------------|
| `Lec` | Lecturing (presenting content) |
| `RtW` | Real-time writing |
| `FUp` | Follow-up/feedback |
| `PQ` | Posing non-clicker question |
| `CQ` | Asking clicker question |
| `AnQ` | Answering student questions |
| `MG` | Moving & guiding |
| `D/V` | Demo/video |
| `Adm` | Administration |
| `W` | Waiting |
| `O` | Other |

### Student (13 codes)
| Code | Description |
|------|-------------|
| `L` | Listening/taking notes |
| `Ind` | Individual thinking |
| `CG` | Discussing clicker question |
| `WG` | Working in groups |
| `OG` | Other group activity |
| `AnQ` | Answering question |
| `SQ` | Asking question |
| `WC` | Whole class discussion |
| `Prd` | Making prediction |
| `SP` | Student presentation |
| `TQ` | Test/quiz |
| `W` | Waiting |
| `O` | Other |

---

## Output

After running, you will see:

1. **Console + log output** (`logs/simulation_YYYYMMDD_HHMMSS.log`):
   - Dialogue between instructor and students for each 2-min interval
   - COPUS codes per segment
   - Statistics and evaluation per scenario
   - Side-by-side comparison

2. **JSON file** (`results/copus_simulation_YYYYMMDD_HHMMSS.json`):
   - Full dialogue log per scenario
   - COPUS code frequency counts and percentages
   - Classroom type classification (DIDACTIC / INTERACTIVE / MIXED)

---

## Validation and Reliability

### Observer Comparison

```python
from multiagent_classroom.evaluator import TeachingEvaluator
from multiagent_classroom.observer import COPUSObserver

observer_human = COPUSObserver()
observer_agent = COPUSObserver()

# ... perform coding ...

evaluator = TeachingEvaluator()
metrics = evaluator.compare_observers(
    observer_human,
    observer_agent,
    coder1_name="Human",
    coder2_name="Agent"
)

print(f"Jaccard Similarity: {metrics['jaccard_similarity']}")
print(f"Cohen's Kappa: {metrics['cohens_kappa']}")
print(f"Interpretation: {metrics['kappa_interpretation']}")
print(f"Percent Agreement: {metrics['percent_agreement']}%")
```

### Reliability Metrics

Based on Smith et al. (2013) COPUS paper methodology:

| Metric | Target | Description |
|--------|--------|-------------|
| Jaccard Similarity | > 0.75 | Code set overlap per segment |
| Cohen's Kappa | > 0.70 | Agreement adjusted for chance |
| Percent Agreement | — | Informative, not primary metric |

### Kappa Interpretation (Landis & Koch, 1977)

| Range | Interpretation |
|-------|----------------|
| < 0.00 | Poor |
| 0.00–0.20 | Slight |
| 0.21–0.40 | Fair |
| 0.41–0.60 | Moderate |
| 0.61–0.80 | Substantial |
| 0.81–1.00 | Almost Perfect |

---

## Test Suite

```
tests/
├── __init__.py
└── test_reliability_metrics.py    # 80+ test cases for IRR metrics
```

### Test Classes

| Class | Coverage |
|-------|----------|
| `TestCOPUSReliabilityAnalyzer` | Initialization and configuration |
| `TestJaccardSimilarity` | Jaccard coefficient calculations |
| `TestCohensKappa` | Kappa calculation and interpretation |
| `TestPercentAgreement` | Perfect match percentage |
| `TestDisagreementAnalysis` | Disagreement identification |
| `TestCalculateAllMetrics` | Comprehensive metrics bundled |
| `TestConfusionMatrixBuilder` | Confusion matrix generation |
| `TestEvaluatorIntegration` | Integration with `COPUSObserver` |
| `TestConvenienceFunction` | Module-level `calculate_all_metrics()` |

### Test Scenarios

- Perfect agreement (kappa = 1.0)
- Partial agreement (0 < kappa < 1)
- No agreement (kappa ≈ 0)
- Disagreement identification
- Edge cases: empty observations, mismatched lengths

---

## Development Status

### Completed (Phase 1)
- [x] Core simulation engine: `teacher`, `student_active`, `student_passive` agents
- [x] Two baseline scenarios: Lec-only, PQ-only
- [x] COPUS observation recording and classification
- [x] IRR metrics: Jaccard similarity, Cohen's kappa, percent agreement
- [x] Disagreement analysis and confusion matrix
- [x] Comprehensive test suite (pytest)

### In Progress (Phase 2)
- [ ] Manual coding tool for human COPUS coding
- [ ] Validation experiments: Agent Observer vs. Human Coder
- [ ] Disagreement analysis and observer prompt refinement

### Planned (Phase 3+)
- [ ] Additional teaching scenarios (mixed methods, group work)
- [ ] Real-time observation dashboard
- [ ] Automated report generation with visualizations
- [ ] Configuration file system (YAML/JSON)
- [ ] Database storage for longitudinal analysis

---

---

## Phase 2: Human Validation

> **Goal**: Achieve **Cohen's κ > 0.60** between the Human coder and the Agent Observer — the "substantial agreement" threshold from Smith et al. (2013).

### Tools (`manual_coder/`)

| File | Purpose |
|------|---------|
| `manual_coder.py` | CLI tool — shows dialogue segment-by-segment, collects your COPUS codes **without showing the agent's codes** (blind coding) |
| `validate_results.py` | Compares your codes vs. the agent's codes using Jaccard, Cohen's κ, and % Agreement via `TeachingEvaluator.compare_observers()` |
| `_path_setup.py` | Internal helper — adds project root to `sys.path` so scripts run from any directory |

### Install dependency

```powershell
pip install questionary
```

---

### Step-by-Step Workflow

#### Step 0 — COPUS Training (1.5 hours, Smith et al. standard)

Before coding, spend ~1.5 hours familiarising yourself with the protocol:
1. Read the 25 COPUS codes and their definitions (Figure 1 in the paper, or the quick-reference table printed during coding).
2. Watch 1-2 training videos from Table 2 in the paper (e.g., the Harvard interactive teaching demo).
3. Practice on the first 2-3 segments of the transcript before recording any official codes.

---

#### Step 1 — Run the Simulation (if not done)

```powershell
python main.py
# Results saved to: results/copus_simulation_YYYYMMDD_HHMMSS.json
```

---

#### Step 2 — Manual Coding (blind)

Code **Scenario 1 (Lec-only)**:
```powershell
python manual_coder/manual_coder.py `
  --file results/copus_simulation_20260309_234010.json `
  --scenario 1
```

Code **Scenario 2 (PQ-only)**:
```powershell
python manual_coder/manual_coder.py `
  --file results/copus_simulation_20260309_234010.json `
  --scenario 2
```

**What the tool does per segment:**
1. Clears the screen and shows the dialogue (instructor + student speech).
2. Displays a quick-reference code card.
3. Prompts you to select **Instructor codes** (checkbox, multi-select).
4. Prompts you to select **Student codes** (checkbox, multi-select).
5. Optionally accepts a free-text note.
6. Auto-saves every 5 segments to `results/human_coded_..._s1_HHMMSS.json`.

**Resume an interrupted session:**
```powershell
python manual_coder/manual_coder.py `
  --file results/copus_simulation_20260309_234010.json `
  --resume results/human_coded_20260309_234010_s2_XXXXXX.json
```

---

#### Step 3 — Compare with Agent Observer (IRR)

```powershell
python manual_coder/validate_results.py `
  --agent results/copus_simulation_20260309_234010.json `
  --human results/human_coded_20260309_234010_s2_XXXXXX.json `
  --save-report
```

**Output:**
```
================================================================
   COPUS IRR VALIDATION REPORT
================================================================
  Agent file : copus_simulation_20260309_234010.json
  Human file : human_coded_..._s2_XXXXXX.json
  Scenario   : scenario2_pq_only

  Jaccard Similarity  :  0.873  (target: > 0.75)
  Cohen's Kappa (κ)   :  0.821  [Almost Perfect]
  Percent Agreement   :  86.7%

  ✅ TARGET MET
```

If κ < 0.60, the tool automatically prints a **Prompt Refinement Suggestions** section listing which code confusions to address.

---

#### Step 4 — If κ < 0.60: Refine and Iterate

1. Read the disagreement report (segment-by-segment breakdown + top confusion pairs).
2. Edit the Observer Agent's system prompt in `data/agent_prompts_vi.py` to add clearer examples for the confusing codes.
3. Re-run the simulation:
   ```powershell
   python main.py
   ```
4. Re-run manual coding on the new results file (`--scenario 2`).
5. Re-run validation. Repeat until **κ ≥ 0.60**.

---

### IRR Target

| Metric | Target | Why |
|--------|--------|-----|
| Cohen's κ | ≥ 0.60 | "Substantial agreement" — Smith et al. (2013) COPUS validation standard |
| Jaccard Similarity | ≥ 0.75 | Code-set overlap per segment |

---

## References

- **COPUS Paper**: Smith et al. (2013) — "The Classroom Observation Protocol for Undergraduate STEM" — *CBE Life Sciences Education*
- **IRR Interpretation**: Landis & Koch (1977) — "The measurement of observer agreement for categorical data" — *Biometrics*
- **COPUS Official**: https://www.physport.org/methods/method.cfm?I=42

## License

See LICENSE file in the root directory.
