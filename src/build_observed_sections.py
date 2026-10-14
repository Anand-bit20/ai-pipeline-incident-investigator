import argparse
import json

from extract_incident_facts import extract_facts
from load_evidence import load_evidence


def build_observed_sections(facts: dict) -> dict:
    observed = []
    impact = []

    for entry in facts["explicit_errors"]:
        fields = entry["fields"]

        parts = [
            f"Recorded error: {fields['error_code']}.",
            f"Recorded stage: {fields.get('stage', 'not specified')}.",
        ]

        if "missing_columns" in fields:
            parts.append(
                "Recorded missing columns: "
                f"{json.dumps(fields['missing_columns'])}."
            )

        observed.append({
            "statement": " ".join(parts),
            "citations": [entry["citation"]],
        })

    for entry in facts["pipeline_events"]:
        fields = entry["fields"]
        statements = []

        if "message" in fields:
            statements.append(
                f"Log message: {json.dumps(fields['message'])}"
            )

        if "status" in fields:
            stage = fields.get("stage", "unspecified")
            statements.append(
                f"Recorded status for stage '{stage}': {fields['status']}."
            )

        if "output_written" in fields:
            statements.append(
                "Recorded output_written: "
                f"{json.dumps(fields['output_written'])}."
            )

        if "pipeline_status" in fields:
            statements.append(
                f"Recorded pipeline status: {fields['pipeline_status']}."
            )

        for statement in statements:
            impact.append({
                "statement": statement,
                "citations": [entry["citation"]],
            })

    return {
        "observed_failure": observed,
        "pipeline_impact": impact,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path")
    args = parser.parse_args()

    facts = extract_facts(load_evidence(args.log_path))
    sections = build_observed_sections(facts)

    print(json.dumps(sections, indent=2, ensure_ascii=False))
    print(
        "\nApplication verification status: "
        + facts["underlying_cause_verification"]
    )


if __name__ == "__main__":
    main()