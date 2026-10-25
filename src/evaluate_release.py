import argparse
import json

from load_evidence import PROJECT_ROOT


REQUIRED_CHECKS = (
    "automated_tests",
    "data_validation",
    "release_checklist",
)

VALID_STATUSES = {"PASS", "FAIL", "UNKNOWN"}


def evaluate_release(release: dict) -> dict:
    if not isinstance(release, dict):
        raise ValueError("Release evidence must be a JSON object.")

    blockers = []
    review_reasons = []
    check_results = []

    if release.get("schema_version") != 1:
        review_reasons.append("Missing or unsupported schema_version.")

    for field in ("release_id", "release_name", "environment"):
        value = release.get(field)
        if not isinstance(value, str) or not value.strip():
            review_reasons.append(f"Missing or invalid {field}.")

    checks = release.get("checks")

    if not isinstance(checks, dict):
        review_reasons.append("Missing or invalid checks object.")
        checks = {}

    for name in REQUIRED_CHECKS:
        check = checks.get(name)

        if not isinstance(check, dict):
            review_reasons.append(f"{name}: required check is missing or invalid.")
            check_results.append({
                "check": name,
                "status": "UNKNOWN",
                "evidence": None,
            })
            continue

        status = check.get("status")
        evidence = check.get("evidence")

        if not isinstance(status, str) or status not in VALID_STATUSES:
            review_reasons.append(f"{name}: missing or invalid status.")
            status = "UNKNOWN"
        elif status == "FAIL":
            blockers.append(f"{name}: required check failed.")
        elif status == "UNKNOWN":
            review_reasons.append(f"{name}: result is unknown.")

        if not isinstance(evidence, str) or not evidence.strip():
            review_reasons.append(f"{name}: evidence description is missing.")
            evidence = None

        check_results.append({
            "check": name,
            "status": status,
            "evidence": evidence,
        })

    # Unexpected checks need review so failures are not silently ignored.
    for name in sorted(set(checks) - set(REQUIRED_CHECKS)):
        review_reasons.append(f"{name}: check is not defined in this policy.")

    incidents = release.get("unresolved_incidents")

    if not isinstance(incidents, list):
        review_reasons.append(
            "unresolved_incidents must be an explicit list; use [] if none."
        )
        incident_count = None
    else:
        incident_count = len(incidents)

        if incidents:
            review_reasons.append(
                f"{incident_count} unresolved incident(s) require review."
            )

    # A known blocking failure takes priority over incomplete evidence.
    if blockers:
        recommendation = "NO-GO"
    elif review_reasons:
        recommendation = "REVIEW"
    else:
        recommendation = "GO"

    return {
        "release_id": release.get("release_id"),
        "release_name": release.get("release_name"),
        "environment": release.get("environment"),
        "synthetic_demo": release.get("synthetic_demo"),
        "policy_version": "1.0",
        "recommendation": recommendation,
        "blocking_reasons": blockers,
        "review_reasons": review_reasons,
        "check_results": check_results,
        "unresolved_incident_count": incident_count,
        "assessment_basis": "Declared check statuses and evidence descriptions",
        "source_evidence_verified": False,
        "human_approval_required": True,
        "deployment_performed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate release readiness using explicit rules."
    )
    parser.add_argument(
        "release_path",
        help="Release JSON path relative to the project folder",
    )
    args = parser.parse_args()

    path = PROJECT_ROOT / args.release_path

    try:
        release = json.loads(path.read_text(encoding="utf-8"))
        assessment = evaluate_release(release)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Could not assess release: {error}\n")

    print(json.dumps(assessment, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()