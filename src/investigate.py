import argparse
import json
import re

from load_evidence import PROJECT_ROOT, load_evidence
from retrieve_evidence import retrieve


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", help="Log path relative to the project folder")
    args = parser.parse_args()

    evidence = load_evidence(args.log_path)

    error_lines = [
        line for line in evidence["lines"]
        if re.search(r"\bERROR\b", line["text"])
    ]

    print("\nINCIDENT EVIDENCE")

    if not error_lines:
        print("No ERROR-level entries found. Further investigation may be needed.")
        return

    for line in error_lines:
        citation = f"{evidence['source']}:L{line['line_number']}"
        print(f"\n[{citation}]")
        print(line["text"])

    # Prefer explicit error codes as the retrieval query.
    error_codes = sorted({
        code
        for line in error_lines
        for code in re.findall(r"\berror_code=([A-Za-z0-9_]+)", line["text"])
    })

    query = (
        " ".join(error_codes)
        if error_codes
        else " ".join(line["text"] for line in error_lines)
    )

    chunks_path = PROJECT_ROOT / "data" / "runbook_chunks.json"
    if not chunks_path.is_file():
        raise FileNotFoundError("Run chunk_runbooks.py first.")

    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    results = retrieve(query, chunks)

    print(f"\nRETRIEVAL QUERY: {query}")
    print("\nRELATED RUNBOOK EVIDENCE")

    if not results:
        print("No matching runbook evidence found.")
        return

    for result in results:
        citation = (
            f"{result['source']}:"
            f"L{result['start_line']}-L{result['end_line']}"
        )
        print(f"\n[{citation}]")
        print(f"Section: {result['heading']}")
        print(f"Retrieval score: {result['score']:.3f}")
        print(result["text"])


if __name__ == "__main__":
    main()