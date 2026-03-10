"""
COPUS Validation Script
========================
Compares agent-coded and human-coded COPUS observations using IRR metrics.

Usage (run from project root OR from manual_coder/ folder):
    python manual_coder/validate_results.py \\
        --agent results/copus_simulation_20260309_234010.json \\
        --human results/human_coded_20260309_234010_s1_XXXXXX.json

Output:
    - IRR metrics in console (Jaccard, Cohen's κ, % Agreement)
    - Disagreement report printed per segment
    - Optional: saves report to results/irr_report_YYYYMMDD_HHMMSS.json
"""

# _path_setup must be the very first import so project root is on sys.path
import _path_setup  # noqa: F401

import json
import argparse
import os
from datetime import datetime
from typing import Dict, List, Any

from multiagent_classroom.evaluator import TeachingEvaluator
from multiagent_classroom.observer import COPUSObserver


# ── Loaders ──────────────────────────────────────────────────────────────────

def load_agent_observations(
    agent_file: str,
    scenario_key: str
) -> List[Dict[str, Any]]:
    """
    Load agent observations from a simulation results JSON.

    Args:
        agent_file: Path to copus_simulation_*.json
        scenario_key: 'scenario1_lec_only' or 'scenario2_pq_only'

    Returns:
        List of observation dicts (with instructor_codes, student_codes)
    """
    with open(agent_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if scenario_key not in data:
        available = list(data.keys())
        raise ValueError(
            f"Scenario '{scenario_key}' not found in {agent_file}.\n"
            f"Available: {available}"
        )

    segments = data[scenario_key]["log"]
    return [seg["copus"] for seg in segments]


def load_human_observations(human_file: str) -> List[Dict[str, Any]]:
    """
    Load human-coded observations from a human_coded_*.json file.

    Args:
        human_file: Path to human_coded_*.json

    Returns:
        List of observation dicts
    """
    with open(human_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["observations"]


def infer_scenario_key(human_file: str) -> str:
    """Infer scenario key from the human-coded filename."""
    basename = os.path.basename(human_file)
    if "_s1_" in basename:
        return "scenario1_lec_only"
    elif "_s2_" in basename:
        return "scenario2_pq_only"
    return "scenario1_lec_only"  # Fallback


# ── Display Helpers ───────────────────────────────────────────────────────────

SEP = "=" * 64
DIV = "─" * 64


def print_header() -> None:
    print("\033[1;34m" + SEP + "\033[0m")
    print("\033[1;34m   COPUS IRR VALIDATION REPORT\033[0m")
    print("\033[1;34m" + SEP + "\033[0m")
    print()


def print_summary(metrics: Dict[str, Any]) -> None:
    """Print a formatted summary of IRR metrics."""
    k = metrics["cohens_kappa"]
    j = metrics["jaccard_similarity"]
    pa = metrics["percent_agreement"]
    interp = metrics["kappa_interpretation"]
    n = metrics["n_segments"]

    # Determine color by kappa value
    if k >= 0.81:
        color = "\033[1;32m"   # Green – Almost Perfect
    elif k >= 0.61:
        color = "\033[1;32m"   # Green – Substantial
    elif k >= 0.41:
        color = "\033[1;33m"   # Yellow – Moderate
    else:
        color = "\033[1;31m"   # Red – Poor/Fair

    reset = "\033[0m"
    target_met = "✅ TARGET MET" if k >= 0.60 else "❌ BELOW TARGET (κ > 0.60 required)"

    print(f"\033[1mSEGMENTS COMPARED:\033[0m {n}")
    print(f"\033[1mCOMPARISON:\033[0m  {metrics['coder1_name']}  vs  {metrics['coder2_name']}")
    print()
    print(DIV)
    print(f"  Jaccard Similarity  :  {j:.3f}  (target: > 0.75)")
    print(f"  Cohen's Kappa (κ)   :  {color}{k:.3f}  [{interp}]{reset}")
    print(f"  Percent Agreement   :  {pa:.1f}%")
    print()
    print(f"  {color}{target_met}{reset}")
    print(DIV)
    print()


def print_disagreements(metrics: Dict[str, Any]) -> None:
    """Print per-segment disagreement details."""
    disagreements = metrics["disagreements"]
    count = disagreements["disagreement_count"]

    if count == 0:
        print("\033[1;32m  ✅ No disagreements found — perfect agreement!\033[0m\n")
        return

    print(f"\033[1;33m  ⚠ {count} segment(s) with disagreements:\033[0m\n")

    for detail in disagreements["disagreement_details"]:
        seg = detail["segment"]
        j_seg = detail.get("jaccard", 0)

        agent_codes = detail.get(f"{metrics['coder1_name']}_codes", [])
        human_codes = detail.get(f"{metrics['coder2_name']}_codes", [])
        agreed      = detail.get("agreement", [])
        only_agent  = detail.get(f"only_{metrics['coder1_name']}", [])
        only_human  = detail.get(f"only_{metrics['coder2_name']}", [])

        print(f"  \033[1mSegment {seg}\033[0m  (Jaccard: {j_seg:.2f})")
        print(f"    Agent  codes : {sorted(agent_codes)}")
        print(f"    Human  codes : {sorted(human_codes)}")
        if agreed:
            print(f"    ✓ Agreed     : {sorted(agreed)}")
        if only_agent:
            print(f"    \033[33m+ Only Agent  : {sorted(only_agent)}\033[0m")
        if only_human:
            print(f"    \033[36m+ Only Human  : {sorted(only_human)}\033[0m")
        print()

    # Common confusions
    confusions = disagreements.get("common_confusions", [])
    if confusions:
        print(f"  \033[1;31mTop Code Confusions:\033[0m")
        for (c1, c2), cnt in confusions[:5]:
            print(
                f"    Agent=\033[33m{c1}\033[0m  vs  Human=\033[36m{c2}\033[0m"
                f"  ({cnt} time{'s' if cnt > 1 else ''})"
            )
        print()

    print("  \033[90m💡 Tip: Review these segments to refine the Agent Observer's prompt.\033[0m")
    print()


def print_prompt_suggestions(metrics: Dict[str, Any]) -> None:
    """Print actionable suggestions for prompt refinement."""
    k = metrics["cohens_kappa"]
    confusions = metrics["disagreements"].get("common_confusions", [])

    if k >= 0.60:
        return

    print(DIV)
    print("\033[1;31m  PROMPT REFINEMENT SUGGESTIONS\033[0m")
    print(DIV)
    print("  κ < 0.60 — Agent Observer needs prompt refinement.")
    print()

    if confusions:
        print("  Based on confusion patterns, consider clarifying:")
        for (c1, c2), cnt in confusions[:3]:
            print(f"   • Why the agent coded '{c1}' when you coded '{c2}' ({cnt}×)")
            print(f"     → Add explicit examples to the observer system prompt")
    else:
        print("   • Review segment-by-segment disagreements above")
        print("   • Add concrete coding examples to the observer prompt")

    print()
    print("  After refining the prompt, re-run the simulation and validate again.")
    print()


# ── Save Report ───────────────────────────────────────────────────────────────

def save_report(
    metrics: Dict[str, Any],
    agent_file: str,
    human_file: str,
    output_dir: str
) -> str:
    """Save the IRR report to a JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"irr_report_{timestamp}.json")

    report = {
        "generated_at": datetime.now().isoformat(),
        "agent_file": os.path.basename(agent_file),
        "human_file": os.path.basename(human_file),
        "irr_metrics": {
            "jaccard_similarity": metrics["jaccard_similarity"],
            "cohens_kappa": metrics["cohens_kappa"],
            "kappa_interpretation": metrics["kappa_interpretation"],
            "percent_agreement": metrics["percent_agreement"],
            "n_segments": metrics["n_segments"],
            "coder1_name": metrics["coder1_name"],
            "coder2_name": metrics["coder2_name"],
        },
        "disagreements": metrics["disagreements"]
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report_path


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="COPUS IRR Validation — Compare Agent vs. Human coding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_results.py \\
      --agent results/copus_simulation_20260309_234010.json \\
      --human results/human_coded_20260309_234010_s2_202603100030.json

  # Also save a report:
  python validate_results.py --agent ... --human ... --save-report
"""
    )
    parser.add_argument("--agent", required=True, help="Path to simulation results JSON (agent codes)")
    parser.add_argument("--human", required=True, help="Path to human_coded_*.json file")
    parser.add_argument(
        "--scenario", choices=["1", "2"], default=None,
        help="Scenario to validate: 1 (Lec-only) or 2 (PQ-only). Auto-detected from filename if omitted."
    )
    parser.add_argument(
        "--save-report", action="store_true",
        help="Save IRR report to results/ directory as JSON"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Validate files
    for fpath, label in [(args.agent, "--agent"), (args.human, "--human")]:
        if not os.path.exists(fpath):
            print(f"\033[31m  ✗ File not found ({label}): {fpath}\033[0m")
            return

    # Determine scenario key
    if args.scenario == "1":
        scenario_key = "scenario1_lec_only"
    elif args.scenario == "2":
        scenario_key = "scenario2_pq_only"
    else:
        scenario_key = infer_scenario_key(args.human)

    print_header()
    print(f"  Agent file : {os.path.basename(args.agent)}")
    print(f"  Human file : {os.path.basename(args.human)}")
    print(f"  Scenario   : {scenario_key}")
    print()

    # Load observations
    try:
        agent_obs = load_agent_observations(args.agent, scenario_key)
        human_obs = load_human_observations(args.human)
    except (ValueError, KeyError) as e:
        print(f"\033[31m  ✗ Error loading files: {e}\033[0m")
        return

    n_agent = len(agent_obs)
    n_human = len(human_obs)

    if n_agent != n_human:
        print(
            f"\033[33m  ⚠ Segment count mismatch: "
            f"Agent={n_agent}, Human={n_human}.\033[0m"
        )
        print(f"  Comparing first {min(n_agent, n_human)} segments.")
        n = min(n_agent, n_human)
        agent_obs = agent_obs[:n]
        human_obs = human_obs[:n]

    # Create COPUSObserver containers
    agent_observer = COPUSObserver()
    agent_observer.observations = agent_obs

    human_observer = COPUSObserver()
    human_observer.observations = human_obs

    # Run IRR comparison
    evaluator = TeachingEvaluator()
    metrics = evaluator.compare_observers(
        agent_observer,
        human_observer,
        coder1_name="Agent",
        coder2_name="Human"
    )

    # Display results
    print(SEP)
    print("\033[1m  IRR METRICS SUMMARY\033[0m")
    print(SEP)
    print()
    print_summary(metrics)

    print(SEP)
    print("\033[1m  DISAGREEMENT ANALYSIS\033[0m")
    print(SEP)
    print()
    print_disagreements(metrics)

    print_prompt_suggestions(metrics)

    # Save report
    if args.save_report:
        out_dir = os.path.dirname(args.agent)
        report_path = save_report(metrics, args.agent, args.human, out_dir)
        print(f"  \033[32m✓ IRR report saved to:\033[0m")
        print(f"    \033[36m{report_path}\033[0m")
        print()


if __name__ == "__main__":
    main()
