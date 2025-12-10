# SimClass Replication

This repository contains code and data for reproducing and analyzing simulations related to the SimClass replication project.

## Project

- Purpose: reproduce and analyze the SimClass simulation experiments used for the thesis. The codebase includes simulation drivers, agent definitions, utilities, and analysis scripts.

## Repository structure (important paths)

- `1-12_7-12/` — primary experiment scripts, drivers, and per-experiment data.
- `24-11_30-11/` — earlier experiment runs and archived results.
- `src/` — library modules used by the simulations (`agents.py`, `simulation.py`, `utils.py`, etc.).
- `results/` and `logs/` — generated outputs and simulation logs.

## Requirements

- Python 3.8+ is recommended.
- Project dependencies are listed in `1-12_7-12/requirements.txt` for the main experiment scripts.

Example (PowerShell):

```powershell
# create and activate a virtual environment
python -m venv .venv
.\venv\Scripts\Activate.ps1

# install dependencies
pip install -r 1-12_7-12/requirements.txt
```

## Usage

- Run the main simulation driver (example):

```powershell
python 1-12_7-12/main.py
```

- Some experiments include dedicated scripts such as `simclass_replication.py` in the experiment folders. Adjust paths if you run scripts from the repository root.

## Analysis

- Scripts such as `fias_analyzer.py` (present in experiment folders) process `*.jsonl` logs and produce labeled or aggregated results. Use those scripts to reproduce analysis steps from experiments.

## Results and logs

- Check `results/` and `logs/` for generated outputs. There are archived experiment runs under `results/archive/` with timestamped directories.


## License

- See top-level `LICENSE` file for licensing details.
