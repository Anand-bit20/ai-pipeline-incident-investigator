from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_evidence(relative_path: str) -> dict:
    path = PROJECT_ROOT / relative_path

    if not path.is_file():
        raise FileNotFoundError(f"Evidence file not found: {path}")

    # utf-8-sig also handles files saved with a UTF-8 byte-order mark.
    lines = path.read_text(encoding="utf-8-sig").splitlines()

    if not any(line.strip() for line in lines):
        raise ValueError(f"Evidence file is empty: {path}")

    return {
        "source": path.relative_to(PROJECT_ROOT).as_posix(),
        "lines": [
            {"line_number": number, "text": text}
            for number, text in enumerate(lines, start=1)
        ],
    }


def display_evidence(evidence: dict) -> None:
    print(f"\nSOURCE: {evidence['source']}")
    print(f"Total lines: {len(evidence['lines'])}\n")

    for line in evidence["lines"]:
        print(f"{line['line_number']:03d} | {line['text']}")


def main() -> None:
    sources = [
        "data/sample_logs/incident_001_missing_trip_id.log",
        "knowledge_base/runbooks/schema_missing_column.md",
    ]

    for source in sources:
        display_evidence(load_evidence(source))


if __name__ == "__main__":
    main()