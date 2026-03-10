"""
COPUS Manual Coding Tool
========================
A CLI tool for human COPUS coding of simulation transcripts.

Usage (run from project root OR from manual_coder/ folder):
    python manual_coder/manual_coder.py --file results/copus_simulation_20260309_234010.json
    python manual_coder/manual_coder.py --file results/... --scenario 1
    python manual_coder/manual_coder.py --file results/... --resume results/human_coded_...json
"""

# _path_setup must be the very first import so project root is on sys.path
import _path_setup  # noqa: F401

import json
import argparse
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

import questionary
from questionary import Style


# ── Styling ─────────────────────────────────────────────────────────────────

STYLE = Style(
    [
        ("qmark", "fg:#5f87d7 bold"),
        ("question", "fg:#ffffff bold"),
        ("answer", "fg:#5fffaf bold"),
        ("pointer", "fg:#5f87d7 bold"),
        ("highlighted", "fg:#5f87d7 bold"),
        ("selected", "fg:#5fffaf"),
        ("separator", "fg:#6c6c6c"),
        ("instruction", "fg:#858585 italic"),
        ("text", ""),
    ]
)

# ── COPUS Code Definitions ───────────────────────────────────────────────────

INSTRUCTOR_CODE_CHOICES = [
    questionary.Choice("Lec  — Lecturing (presenting content)", value="Lec"),
    questionary.Choice("RtW  — Real-time writing (board/projector)", value="RtW"),
    questionary.Choice(
        "FUp  — Follow-up/feedback on question or activity", value="FUp"
    ),
    questionary.Choice(
        "PQ   — Posing non-clicker question (non-rhetorical)", value="PQ"
    ),
    questionary.Choice("CQ   — Asking clicker question", value="CQ"),
    questionary.Choice("AnQ  — Answering student questions", value="AnQ"),
    questionary.Choice("MG   — Moving & guiding student work", value="MG"),
    questionary.Choice("D/V  — Demo / video / simulation", value="D/V"),
    questionary.Choice(
        "Adm  — Administration (homework, returning tests)", value="Adm"
    ),
    questionary.Choice("W    — Waiting (could interact but is not)", value="W"),
    questionary.Choice("O    — Other (explain in notes)", value="O"),
]

STUDENT_CODE_CHOICES = [
    questionary.Choice("L    — Listening / taking notes", value="L"),
    questionary.Choice("Ind  — Individual thinking (only when prompted)", value="Ind"),
    questionary.Choice("CG   — Discussing clicker question in groups", value="CG"),
    questionary.Choice("WG   — Working in groups on worksheet", value="WG"),
    questionary.Choice("OG   — Other group activity", value="OG"),
    questionary.Choice("AnQ  — Answering instructor question", value="AnQ"),
    questionary.Choice("SQ   — Student asks question", value="SQ"),
    questionary.Choice("WC   — Whole-class discussion", value="WC"),
    questionary.Choice("Prd  — Making a prediction (demo/experiment)", value="Prd"),
    questionary.Choice("SP   — Student presentation", value="SP"),
    questionary.Choice("TQ   — Test or quiz", value="TQ"),
    questionary.Choice("W    — Waiting", value="W"),
    questionary.Choice("O    — Other (explain in notes)", value="O"),
]

# ── Helpers ──────────────────────────────────────────────────────────────────


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_header() -> None:
    print("\033[1;34m" + "=" * 64 + "\033[0m")
    print("\033[1;34m   COPUS MANUAL CODING TOOL   (Phase 2 Validation)\033[0m")
    print("\033[1;34m" + "=" * 64 + "\033[0m")
    print()


def print_divider() -> None:
    print("\033[90m" + "─" * 64 + "\033[0m")


def print_reference_card() -> None:
    """Print a compact COPUS reference card."""
    print("\033[33mQUICK REFERENCE — COPUS CODES\033[0m")
    print("\033[33mINSTRUCTOR:\033[0m Lec  RtW  FUp  PQ  CQ  AnQ  MG  D/V  Adm  W  O")
    print(
        "\033[33mSTUDENT:   \033[0m L    Ind  CG   WG  OG  AnQ  SQ  WC   Prd  SP TQ W O"
    )
    print()


def load_simulation(file_path: str) -> Dict[str, Any]:
    """Load and return simulation results JSON."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_segments(data: Dict[str, Any], scenario_key: str) -> List[Dict[str, Any]]:
    """Extract segment logs from a scenario."""
    return data[scenario_key]["log"]


def build_save_path(sim_file: str, scenario_key: str) -> str:
    """Generate the output path for human-coded results.

    Always saves into the project-root results/ directory, regardless of
    where the script is invoked from.
    """
    base = (
        os.path.basename(sim_file).replace("copus_simulation_", "").replace(".json", "")
    )
    scenario_tag = "s1" if "scenario1" in scenario_key else "s2"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Save next to the original simulation file (project root results/)
    sim_abs = os.path.abspath(sim_file)
    out_dir = os.path.dirname(sim_abs)
    return os.path.join(out_dir, f"human_coded_{base}_{scenario_tag}_{timestamp}.json")


def save_progress(
    save_path: str,
    coded_segments: List[Dict[str, Any]],
    scenario_key: str,
    sim_file: str,
) -> None:
    """Persist partial/complete coding results to JSON."""
    output = {
        "meta": {
            "source_simulation": os.path.basename(sim_file),
            "scenario": scenario_key,
            "coder": "human",
            "coded_at": datetime.now().isoformat(),
            "total_coded": len(coded_segments),
        },
        "observations": coded_segments,
    }
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def display_segment(segment: Dict[str, Any], seg_num: int, total: int) -> None:
    """Print a single 2-minute segment for the coder to review."""
    clear_screen()
    print_header()
    print_reference_card()

    # Progress
    progress_pct = (seg_num - 1) / total * 100
    bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
    print(f"  Segment {seg_num}/{total}  [{bar}]  {progress_pct:.0f}%")
    print()

    # Time range
    time_range = segment.get("copus", {}).get("time_range", "? min")
    print(f"\033[1;36m {time_range}\033[0m")
    print_divider()

    # Teacher dialogue
    teacher_text = segment.get("teacher", "")
    print("\033[1;33m  INSTRUCTOR:\033[0m")
    # Word-wrap at ~60 chars
    words = teacher_text.replace("\\n", "\n").split(" ")
    line = "  "
    for word in words:
        if "\n" in word:
            parts = word.split("\n")
            line += parts[0]
            print(f"\033[93m{line}\033[0m")
            line = f"  {parts[-1]} " if len(parts) > 1 else "  "
        elif len(line) + len(word) > 62:
            print(f"\033[93m{line}\033[0m")
            line = f"  {word} "
        else:
            line += f"{word} "
    if line.strip():
        print(f"\033[93m{line}\033[0m")
    print()

    # Student dialogue (if present)
    student_text = segment.get("student", segment.get("students", ""))
    if student_text and student_text != "Listening and taking notes":
        print("\033[1;32m  STUDENT:\033[0m")
        words = student_text.replace("\\n", "\n").split(" ")
        line = "  "
        for word in words:
            if "\n" in word:
                parts = word.split("\n")
                line += parts[0]
                print(f"\033[92m{line}\033[0m")
                line = f"  {parts[-1]} " if len(parts) > 1 else "  "
            elif len(line) + len(word) > 62:
                print(f"\033[92m{line}\033[0m")
                line = f"  {word} "
            else:
                line += f"{word} "
        if line.strip():
            print(f"\033[92m{line}\033[0m")
        print()

    print_divider()
    print("\033[90m  Code what YOU observe in the dialogue above.\033[0m")
    print("\033[90m  You can select MULTIPLE codes. Agent codes are hidden.\033[0m")
    print()


def code_segment(segment: Dict[str, Any], seg_num: int) -> Optional[Dict[str, Any]]:
    """
    Prompt the coder for instructor and student COPUS codes.

    Returns:
        Dict with coded observation, or None if user quit.
    """
    # ── Instructor codes ──────────────────────────────────────────────────
    print("\033[1;33m  Step 1/2 — INSTRUCTOR codes:\033[0m")
    instructor_codes = questionary.checkbox(
        "Select all that apply:",
        choices=INSTRUCTOR_CODE_CHOICES,
        style=STYLE,
        instruction="(Space to select, Enter to confirm)",
    ).ask()

    if instructor_codes is None:  # Ctrl+C
        return None

    print()

    # ── Student codes ─────────────────────────────────────────────────────
    print("\033[1;32m  Step 2/2 — STUDENT codes:\033[0m")
    student_codes = questionary.checkbox(
        "Select all that apply:",
        choices=STUDENT_CODE_CHOICES,
        style=STYLE,
        instruction="(Space to select, Enter to confirm)",
    ).ask()

    if student_codes is None:
        return None

    # ── Optional note ─────────────────────────────────────────────────────
    note = questionary.text("  Optional note [Enter to skip]:", style=STYLE).ask()

    time_range = segment.get("copus", {}).get("time_range", "")

    return {
        "segment": seg_num,
        "time_range": time_range,
        "instructor_codes": instructor_codes,
        "student_codes": student_codes,
        "note": note or "",
    }


def choose_scenario(data: Dict[str, Any]) -> Optional[str]:
    """Let user select which scenario to code."""
    available = list(data.keys())
    labels = {
        "scenario1_lec_only": "Scenario 1: Lec-only (Lecture-based)",
        "scenario2_pq_only": "Scenario 2: PQ-only (Question-driven)",
    }
    choices = [questionary.Choice(labels.get(k, k), value=k) for k in available]
    return questionary.select(
        "Which scenario do you want to code?", choices=choices, style=STYLE
    ).ask()


# ── Main Workflow ────────────────────────────────────────────────────────────


def run_coding_session(
    sim_file: str, scenario_key: Optional[str], resume_file: Optional[str]
) -> None:
    """Execute a full manual coding session."""

    # Load simulation
    print(f"\n  Loading: \033[36m{sim_file}\033[0m")
    data = load_simulation(sim_file)

    # Choose scenario
    if scenario_key is None:
        scenario_key = choose_scenario(data)
    if scenario_key is None:
        print("Session cancelled.")
        return

    segments = extract_segments(data, scenario_key)
    total = len(segments)

    # Handle resume
    coded_segments: List[Dict[str, Any]] = []
    start_from = 0
    save_path: str

    if resume_file and os.path.exists(resume_file):
        with open(resume_file, "r", encoding="utf-8") as f:
            prev = json.load(f)
        coded_segments = prev.get("observations", [])
        start_from = len(coded_segments)
        save_path = resume_file
        print(f"  Resuming from segment {start_from + 1}/{total}")
    else:
        save_path = build_save_path(sim_file, scenario_key)
        print(f"  Output will be saved to: \033[36m{save_path}\033[0m")

    input("\n  Press Enter to start coding... (Ctrl+C to quit at any time)\n")

    # ── Coding loop ───────────────────────────────────────────────────────
    for i, segment in enumerate(segments[start_from:], start=start_from + 1):
        display_segment(segment, i, total)

        result = code_segment(segment, i)

        if result is None:
            # User pressed Ctrl+C
            print("\n\033[33m  Session interrupted. Saving progress...\033[0m")
            save_progress(save_path, coded_segments, scenario_key, sim_file)
            print(
                f"  Saved {len(coded_segments)} segment(s) to:\n    \033[36m{save_path}\033[0m"
            )
            print("\n  Resume with:")
            print(
                f'    python manual_coder.py --file "{sim_file}" --resume "{save_path}"'
            )
            return

        coded_segments.append(result)

        # Auto-save every 5 segments
        if i % 5 == 0 or i == total:
            save_progress(save_path, coded_segments, scenario_key, sim_file)
            print(f"\n  \033[32mAuto-saved ({i}/{total} segments)\033[0m")

        # Confirm continue (except last)
        if i < total:
            cont = questionary.confirm(
                f"  Continue to segment {i + 1}?", default=True, style=STYLE
            ).ask()
            if not cont:
                print("\n\033[33m  Pausing. Progress saved.\033[0m")
                save_progress(save_path, coded_segments, scenario_key, sim_file)
                print(
                    f"  Saved {len(coded_segments)} segment(s) to:\n    \033[36m{save_path}\033[0m"
                )
                return

    # ── Completed ─────────────────────────────────────────────────────────
    clear_screen()
    print_header()
    print("\033[1;32m  All segments coded!\033[0m")
    print(f"\n  Total segments:  {total}")
    print(f"  Coded by:        human")
    print(f"  Saved to:\n    \033[36m{save_path}\033[0m")
    print()
    print("  ► Run validation:")
    print(f"    python validate_results.py \\")
    print(f'      --agent "{sim_file}" \\')
    print(f'      --human "{save_path}"')
    print()


# ── Entry Point ──────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="COPUS Manual Coding Tool — Phase 2 Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Code Scenario 1:
    python manual_coder.py --file results/copus_simulation_20260309_234010.json --scenario 1

  Code Scenario 2:
    python manual_coder.py --file results/copus_simulation_20260309_234010.json --scenario 2

  Resume a previous session:
    python manual_coder.py --file results/... --resume results/human_coded_...json
""",
    )
    parser.add_argument(
        "--file", required=True, help="Path to simulation results JSON file"
    )
    parser.add_argument(
        "--scenario",
        type=int,
        choices=[1, 2],
        default=None,
        help="Scenario to code: 1 (Lec-only) or 2 (PQ-only). Prompts if omitted.",
    )
    parser.add_argument(
        "--resume",
        default=None,
        help="Path to a previous human-coded JSON to resume from",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    scenario_key: Optional[str] = None
    if args.scenario == 1:
        scenario_key = "scenario1_lec_only"
    elif args.scenario == 2:
        scenario_key = "scenario2_pq_only"

    clear_screen()
    print_header()

    if not os.path.exists(args.file):
        print(f"\033[31m  File not found: {args.file}\033[0m")
        return

    run_coding_session(args.file, scenario_key, args.resume)


if __name__ == "__main__":
    main()
