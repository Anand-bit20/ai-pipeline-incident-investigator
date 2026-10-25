import argparse
import json
import time
from datetime import datetime, timezone

from evaluate_release import evaluate_release
from generate_investigation import generate_investigation
from load_evidence import PROJECT_ROOT


def assess_release(
    release: dict,
    model: str = "gemma3:4b",
    retriever: str = "semantic",
) -> dict:
    readiness = evaluate_release(release)
    investigations = []

    incidents = release.get("unresolved_incidents")

    if isinstance(incidents, list):
        for incident in incidents:
            incident_id = (
                incident.get("incident_id")
                if isinstance(incident, dict)
                else None
            )
            log_path = (
                incident.get("log_path")
                if isinstance(incident, dict)
                else None
            )

            if not isinstance(log_path, str) or not log_path.strip():
                outcome = {
                    "status": "needs_review",
                    "reason": "Incident has no valid log_path.",
                }
            else:
                try:
                    # Only read incident files inside this project.
                    resolved_path = (PROJECT_ROOT / log_path).resolve()
                    resolved_path.relative_to(PROJECT_ROOT.resolve())

                    if not resolved_path.is_file():
                        raise FileNotFoundError(
                            f"Incident log does not exist: {log_path}"
                        )

                    outcome = generate_investigation(
                        log_path=log_path,
                        model=model,
                        retriever=retriever,
                    )

                    valid_statuses = {
                        "generated",
                        "unsupported",
                        "needs_review",
                        "error",
                    }

                    if (
                        not isinstance(outcome, dict)
                        or outcome.get("status") not in valid_statuses
                    ):
                        outcome = {
                            "status": "error",
                            "reason": "Generator returned an unexpected outcome.",
                        }

                except Exception as error:
                    # Preserve the release assessment if investigation fails.
                    outcome = {
                        "status": "error",
                        "reason": f"{type(error).__name__}: {error}",
                    }

            investigations.append({
                "incident_id": incident_id,
                "log_path": log_path,
                **outcome,
            })

    # Investigation results never override the rule-based decision.
    return {
        "assessment_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "release_evidence": release,
        "readiness": readiness,
        "investigations": investigations,
        "investigation_summary": {
            "attempted": len(investigations),
            "generated": sum(
                item["status"] == "generated"
                for item in investigations
            ),
            "not_generated": sum(
                item["status"] != "generated"
                for item in investigations
            ),
        },
        "human_review_status": "pending",
        "deployment_performed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Combine release readiness and incident investigations."
    )
    parser.add_argument("release_path")
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument(
        "--retriever",
        choices=["keyword", "semantic"],
        default="semantic",
    )
    args = parser.parse_args()

    release_path = PROJECT_ROOT / args.release_path

    try:
        release = json.loads(release_path.read_text(encoding="utf-8"))
        assessment = assess_release(
            release,
            model=args.model,
            retriever=args.retriever,
        )
    except (OSError, ValueError) as error:
        parser.exit(1, f"Could not assess release: {error}\n")

    output_dir = PROJECT_ROOT / "evaluation" / "release_assessments"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"release_assessment_{time.time_ns()}.json"
    output_path.write_text(
        json.dumps(assessment, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    readiness = assessment["readiness"]

    print("\nRELEASEGUARD ASSESSMENT")
    print(f"Release: {readiness['release_id']}")
    print(f"Recommendation: {readiness['recommendation']}")

    for reason in readiness["blocking_reasons"]:
        print(f"Blocker: {reason}")

    for reason in readiness["review_reasons"]:
        print(f"Review: {reason}")

    for investigation in assessment["investigations"]:
        print(
            f"Incident {investigation['incident_id']}: "
            f"{investigation['status']}"
        )
        if investigation.get("reason"):
            print(f"  Reason: {investigation['reason']}")

    print("Human review: pending")
    print(f"Saved combined assessment: {output_path}")


if __name__ == "__main__":
    main()