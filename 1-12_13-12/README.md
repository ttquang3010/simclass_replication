# SimClass Multi-Agent Classroom Simulation

Multi-agent AI classroom simulation system with shy student psychology modeling.

## Directory Structure

```
📁 1-12_7-12/
├── main.py                      # Entry point - chạy simulation
├── .env                         # API keys (DEEPSEEK_API_KEY, GOOGLE_API_KEY)
├── requirements.txt             # Python dependencies
│
├── 📁 src/                      # Source code
│   ├── __init__.py
│   ├── config.py                # Configuration & constants
│   ├── agents.py                # SimAgent & SimulatedUser classes
│   ├── utils.py                 # Utility functions
│   ├── simulation.py            # Core simulation logic
│   └── simclass_replication_old.py  # Backup (monolithic version)
│
├── 📁 data/                     # Input data
│   ├── course_script_lecture_1.json  # Lecture 1: ML Foundations & Workflow (25 slides)
│   ├── course_script_lecture_2.json  # Lecture 2: Supervised Learning (25 slides)
│   ├── course_script_lecture_3.json  # Lecture 3: Advanced Models (25 slides)
│   ├── course_script_lecture_4.json  # Lecture 4: Unsupervised Learning (25 slides)
│   ├── course_script_lecture_5.json  # Lecture 5: RL & Deep Learning (25 slides)
│   ├── course_script.json            # Original lecture (kept as reference)
│   └── agent_prompts.json            # System prompts for 7 agents
│
├── 📁 logs/                     # Simulation output logs
│   └── simulation_log_multi_agent_YYYYMMDD_HHMMSS.jsonl
│
└── 📁 results/                  # Analysis results
    └── archive/                 # Previous results
```

## Installation

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup .env file
# Add: DEEPSEEK_API_KEY=your_key_here
# Or:  GOOGLE_API_KEY=your_key_here
```

## Run Simulation

```bash
python main.py
```

## Configuration

Edit `src/config.py`:
- `CURRENT_LECTURE_ID`: Select lecture (1-5) to run simulation
  - 1: ML Foundations & Workflow
  - 2: Supervised Learning (Regression & Classification)
  - 3: Advanced Supervised Models (SVM, Trees, Ensembles)
  - 4: Unsupervised Learning (Clustering, PCA)
  - 5: Reinforcement Learning & Deep Learning
- `N_SESSIONS`: Number of simulation runs (default: 2)
- `MAX_CONTEXT_TEACHER`: Context window for teacher (60 messages)
- `MAX_CONTEXT_SUMMARY_SEEKER`: Context for Note Taker (None = unlimited)
- `MAX_CONTEXT_PEERS`: Context for peers (40 messages)

Edit system prompts: `data/agent_prompts.json`

## Agents

1. **Prof. X** - AI Teacher
2. **Clarity Guide** - Teaching Assistant
3. **Deep Thinker** - Student asking complex questions
4. **Summary Seeker** - Student taking notes and summarizing
5. **Mr. Clown** - Student making humorous analogies
6. **Curious Baby** - Student asking basic questions
7. **Student** - Simulated User (shy student - target learner)

## Output

Logs are saved to: `logs/simulation_log_multi_agent_YYYYMMDD_HHMMSS.jsonl`

Each entry contains:
- `session_id`: Session ID
- `turn`: Interaction turn
- `speaker`: Agent name
- `text`: Utterance content
- `type`: FIAS code (Lecture_5, Question_9, etc.)
- `timestamp`: Timestamp

## FIAS Analysis

Analyze simulation results:

```bash
python fias_analyzer.py
```

## Context Window Strategy

- **DeepSeek**: 131K tokens limit
- **Sliding window** for Prof. X, peers (60/40 messages)
- **Unlimited** for Summary Seeker (records entire lecture)
- **Reset** between sessions (each session = 1 independent lecture)
