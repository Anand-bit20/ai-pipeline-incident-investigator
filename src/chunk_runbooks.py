import json

from load_evidence import PROJECT_ROOT, load_evidence


def chunk_runbook(evidence: dict) -> list[dict]:
    chunks = []
    current_lines = []
    current_heading = "Document overview"

    def save_chunk() -> None:
        if not any(line["text"].strip() for line in current_lines):
            return

        start = current_lines[0]["line_number"]
        end = current_lines[-1]["line_number"]

        chunks.append({
            "chunk_id": f"{evidence['source']}#L{start}-L{end}",
            "source": evidence["source"],
            "heading": current_heading,
            "start_line": start,
            "end_line": end,
            "text": "\n".join(line["text"] for line in current_lines),
        })

    for line in evidence["lines"]:
        if line["text"].startswith("## "):
            save_chunk()
            current_lines = []
            current_heading = line["text"][3:].strip()

        current_lines.append(line)

    save_chunk()
    return chunks


def main() -> None:
    runbook_dir = PROJECT_ROOT / "knowledge_base" / "runbooks"
    paths = sorted(runbook_dir.glob("*.md"))

    if not paths:
        raise FileNotFoundError(f"No Markdown runbooks found: {runbook_dir}")

    chunks = []

    for path in paths:
        relative_path = path.relative_to(PROJECT_ROOT).as_posix()
        chunks.extend(chunk_runbook(load_evidence(relative_path)))

    output = PROJECT_ROOT / "data" / "runbook_chunks.json"
    output.write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Created {len(chunks)} chunks")
    print(f"Saved to: {output}")

    for chunk in chunks:
        print(
            f"- {chunk['heading']}: "
            f"lines {chunk['start_line']}-{chunk['end_line']}"
        )


if __name__ == "__main__":
    main()
    