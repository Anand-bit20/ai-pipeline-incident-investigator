import argparse
import json
import re

from load_evidence import load_evidence


# Supports the key=value format used by our sample logs:
# plain values, quoted strings, and flat JSON arrays.
FIELD_PATTERN = re.compile(
    r'\b([A-Za-z_][A-Za-z0-9_]*)='
    r'(\[[^\]\n]*\]|"(?:\\.|[^"\\])*"|[^\s]+)'
)


def parse_fields(text: str) -> dict:
    fields = {}

    for key, raw_value in FIELD_PATTERN.findall(text):
        try:
            fields[key] = json.loads(raw_value)
        except json.JSONDecodeError:
            fields[key] = raw_value

    return fields


def extract_facts(log: dict) -> dict:
    result = {
        "source": log["source"],
        "explicit_errors": [],
        "schema_evidence": [],
        "pipeline_events": [],
        "underlying_cause_verification": "NOT_PERFORMED",
    }

    for line in log["lines"]:
        fields = parse_fields(line["text"])
        entry = {
            "fields": fields,
            "citation": f"{log['source']}:L{line['line_number']}",
        }

        if "error_code" in fields:
            result["explicit_errors"].append(entry)

        if "required_columns" in fields or "observed_columns" in fields:
            result["schema_evidence"].append(entry)

        if any(
            key in fields
            for key in ("pipeline_status", "status", "output_written", "message")
        ):
            result["pipeline_events"].append(entry)

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path")
    args = parser.parse_args()

    log = load_evidence(args.log_path)
    facts = extract_facts(log)

    print(json.dumps(facts, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()