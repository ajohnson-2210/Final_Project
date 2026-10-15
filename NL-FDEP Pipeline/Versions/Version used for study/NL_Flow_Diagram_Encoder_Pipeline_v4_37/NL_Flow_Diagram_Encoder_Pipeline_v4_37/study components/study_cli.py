"""Command-line interface for NL-FDEP study batch processing and adjudication."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _component_name in (
    "parser components",
    "compiler components",
    "flow diagram components",
    "pipeline components",
    "study components",
    "cli components",
):
    _component_path = str(PROJECT_ROOT / _component_name)
    if _component_path not in sys.path:
        sys.path.insert(0, _component_path)
import argparse
import json

from adjudication import adjudicate_files
from pseudocode_profiles import PseudocodeProfile
from study_analysis import aggregate_algorithm_folders, aggregate_study_root
from study_batch import StudyBatchProcessor
from study_provenance import validate_baseline, validate_llm_results, write_preflight
from study_review import launch_review_dashboard


def _profile(value: str) -> PseudocodeProfile:
    aliases = {
        "strict": PseudocodeProfile.AJ_DIALECT_STRICT,
        "generic": PseudocodeProfile.GENERIC_COMPATIBILITY,
        "general": PseudocodeProfile.GENERAL_NO_CONVERSION,
    }
    try:
        return aliases[value.lower()]
    except KeyError as exc:
        raise argparse.ArgumentTypeError("profile must be strict, generic, or general") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="NL-FDEP v4.29 study tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    llm = sub.add_parser("process-llm", help="Process an LLM results folder")
    llm.add_argument("results", type=Path)
    llm.add_argument("--profile", type=_profile, default=PseudocodeProfile.GENERIC_COMPATIBILITY)
    llm.add_argument("--baseline-root", type=Path)
    llm.add_argument("--force", action="store_true", help="Reprocess even when current artefacts exist; reviewed outputs are archived first")
    llm.add_argument("--no-resume", action="store_true", help="Do not skip current unreviewed artefacts")

    baseline = sub.add_parser("process-baseline", help="Process a Baseline folder")
    baseline.add_argument("baseline", type=Path)
    baseline.add_argument("--profile", type=_profile, default=PseudocodeProfile.AJ_DIALECT_STRICT)
    baseline.add_argument("--force", action="store_true")
    baseline.add_argument("--no-resume", action="store_true")

    aggregate = sub.add_parser("aggregate", help="Rebuild CSV/JSON analysis tables")
    aggregate.add_argument("algorithm_parent", type=Path)
    aggregate.add_argument("--output", type=Path)

    whole = sub.add_parser("aggregate-study", help="Aggregate Baseline plus all model result folders")
    whole.add_argument("study_root", type=Path)
    whole.add_argument("--output", type=Path)

    adjudicate = sub.add_parser("adjudicate", help="Apply completed human_review.json files")
    adjudicate.add_argument("algorithm_parent", type=Path)

    pre_llm = sub.add_parser("preflight-llm", help="Validate an LLM results folder without processing it")
    pre_llm.add_argument("results", type=Path)
    pre_llm.add_argument("--baseline-root", type=Path)
    pre_llm.add_argument("--output", type=Path)

    pre_base = sub.add_parser("preflight-baseline", help="Validate a Baseline folder without processing it")
    pre_base.add_argument("baseline", type=Path)
    pre_base.add_argument("--output", type=Path)

    review = sub.add_parser("review", help="Open the integrated human-review dashboard")
    review.add_argument("algorithm_parent", type=Path)

    args = parser.parse_args()
    if args.command == "process-llm":
        result = StudyBatchProcessor().process_llm_results(
            args.results,
            profile=args.profile,
            baseline_root=args.baseline_root,
            resume=not args.no_resume,
            force=args.force,
        )
    elif args.command == "process-baseline":
        result = StudyBatchProcessor().process_baseline(args.baseline, profile=args.profile, resume=not args.no_resume, force=args.force)
    elif args.command == "aggregate":
        result = aggregate_algorithm_folders(args.algorithm_parent, args.output)
    elif args.command == "aggregate-study":
        result = aggregate_study_root(args.study_root, args.output)
    elif args.command == "preflight-llm":
        report = validate_llm_results(args.results, args.baseline_root)
        result = {"report": report, "outputs": write_preflight(report, args.output or (args.results / "study_analysis"))}
    elif args.command == "preflight-baseline":
        report = validate_baseline(args.baseline)
        result = {"report": report, "outputs": write_preflight(report, args.output or (args.baseline / "study_analysis"))}
    elif args.command == "review":
        launch_review_dashboard(args.algorithm_parent)
        result = {"status": "REVIEW_SESSION_CLOSED", "review_root": str(args.algorithm_parent.resolve())}
    else:
        updated = []
        for scoring_dir in sorted(args.algorithm_parent.glob("Algorithm - */pipeline_artifacts/scoring")):
            path = adjudicate_files(scoring_dir)
            if path:
                updated.append(str(path.resolve()))
        analysis = aggregate_algorithm_folders(args.algorithm_parent)
        result = {"adjudicated": updated, "analysis_outputs": analysis}

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
