import argparse
import json
import time
from pathlib import Path

from load_evidence import PROJECT_ROOT


CRITERIA = [
    "failure_identification",
    "pipeline_impact",
    "root_cause_uncertainty",
    "supported_troubleshooting",
    "supported_evidence_requests",
]

REQUIRED_SECTIONS = {
    "observed_failure",
    "pipeline_impact",
    "root_cause_status",
    "troubleshooting",
    "additional_evidence",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record manual review alongside automatic checks."
    )
    parser.add_argument("report_path")
    parser.add_argument(
        "--case",
        default="evaluation/cases/incident_001.json",
    )
    parser.add_argument(
        "--decisions",
        nargs=5,
        choices=["pass", "fail"],
        required=True,
        help="Decisions in the order defined by CRITERIA.",
    )
    args = parser.parse_args()

    report_path = PROJECT_ROOT / args.report_path
    case_path = PROJECT_ROOT / args.case

    record = json.loads(report_path.read_text(encoding="utf-8"))
    case = json.loads(case_path.read_text(encoding="utf-8"))

    if record["incident_source"] != case["incident_source"]:
        raise ValueError("Report and evaluation case refer to different logs.")

    report = json.loads(record["report"])
    if not isinstance(report, dict):
        raise ValueError("Expected a structured report object.")

    sections_complete = (
        set(report) == REQUIRED_SECTIONS
        and all(
            isinstance(report[section], list) and report[section]
            for section in REQUIRED_SECTIONS
        )
    )

    # Recheck citation labels from the saved report.
    labels = [
        label
        for findings in report.values()
        for finding in findings
        for label in finding["citations"]
    ]
    allowed = set(record["allowed_citations"])
    citations_valid = bool(labels) and all(
        label in allowed for label in labels
    )

    decisions = dict(zip(CRITERIA, args.decisions))
    passed = sum(value == "pass" for value in decisions.values())

    review = {
        "case_id": case["case_id"],
        "source_report": Path(args.report_path).as_posix(),
        "model": record["model"],
        "response_seconds": record["response_seconds"],
        "automatic_checks": {
            "required_sections_present": bool(sections_complete),
            "citation_labels_valid": citations_valid,
        },
        "manual_review": {
            "method": "Reviewer-supplied decisions; not automated semantics",
            "criteria": decisions,
            "passed": passed,
            "total": len(CRITERIA),
            "pass_rate": passed / len(CRITERIA),
        },
        "overall_pass": bool(
            sections_complete
            and citations_valid
            and passed == len(CRITERIA)
        ),
    }

    output_dir = PROJECT_ROOT / "evaluation" / "reviews"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{report_path.stem}_{time.time_ns()}.json"
    output.write_text(
        json.dumps(review, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(review, indent=2))
    print(f"\nSaved review: {output}")


if __name__ == "__main__":
    main()