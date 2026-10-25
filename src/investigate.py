import argparse
import json
import re

from load_evidence import PROJECT_ROOT, load_evidence
from retrieve_evidence import retrieve
from retrieve_evidence import APPLICABLE_ERROR_PATTERN
from retrieve_semantic import load_index, retrieve_semantic


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", help="Log path relative to the project folder")
    parser.add_argument(
        "--retriever",
        choices=["keyword", "semantic"],
        default="keyword",
    )
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
    if args.retriever == "semantic":
        index = load_index()
        results = retrieve_semantic(query, index, top_k=3)
    else:
        results = retrieve(query, chunks, top_k=3)

    # Expand only when retrieval succeeded and every explicit code
    # has documented runbook applicability.
    supplemental_sections = []

    if results and error_codes:
        sources_by_code = {}

        for chunk in chunks:
            for code in APPLICABLE_ERROR_PATTERN.findall(chunk["text"]):
                sources_by_code.setdefault(code, set()).add(chunk["source"])

        if all(code in sources_by_code for code in error_codes):
            applicable_sources = set()

            for code in error_codes:
                applicable_sources.update(sources_by_code[code])

            selected_ids = {result["chunk_id"] for result in results}
            required_headings = {
                "evidence to inspect",
                "troubleshooting steps",
            }

            for chunk in chunks:
                heading = chunk["heading"].lstrip("#").strip().casefold()

                if (
                    chunk["source"] in applicable_sources
                    and heading in required_headings
                    and chunk["chunk_id"] not in selected_ids
                ):
                    supplemental_sections.append(chunk)
                    selected_ids.add(chunk["chunk_id"])

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

    if supplemental_sections:
        print("\nADDITIONAL SECTIONS FROM APPLICABLE RUNBOOKS")

        for chunk in supplemental_sections:
            citation = (
                f"{chunk['source']}:"
                f"L{chunk['start_line']}-L{chunk['end_line']}"
            )

            print(f"\n[{citation}]")
            print(f"Section: {chunk['heading']}")
            print("Selection: documented applicability + section heading")
            print(chunk["text"])


if __name__ == "__main__":
    main()