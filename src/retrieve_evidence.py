import argparse
import json
import math
import re

from load_evidence import PROJECT_ROOT


def tokenize(text: str) -> set[str]:
    # Split error codes such as SCHEMA_MISSING_COLUMN into words.
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def retrieve(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    results = []

    for chunk in chunks:
        chunk_tokens = tokenize(chunk["text"])
        shared_tokens = query_tokens & chunk_tokens

        if not shared_tokens:
            continue

        # Cosine similarity between binary word-presence vectors.
        score = len(shared_tokens) / math.sqrt(
            len(query_tokens) * len(chunk_tokens)
        )

        results.append({
            **chunk,
            "score": score,
            "matched_terms": sorted(shared_tokens),
        })

    results.sort(key=lambda item: (-item["score"], item["chunk_id"]))
    return results[:top_k]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Incident description or error message")
    args = parser.parse_args()

    path = PROJECT_ROOT / "data" / "runbook_chunks.json"

    if not path.is_file():
        raise FileNotFoundError("Run chunk_runbooks.py first.")

    chunks = json.loads(path.read_text(encoding="utf-8"))
    results = retrieve(args.query, chunks)

    if not results:
        print("No matching evidence found.")
        return

    for rank, result in enumerate(results, start=1):
        citation = (
            f"{result['source']}:"
            f"L{result['start_line']}-L{result['end_line']}"
        )

        print(f"\nRESULT {rank}: {result['heading']}")
        print(f"Retrieval score: {result['score']:.3f}")
        print(f"Citation: [{citation}]")
        print(f"Matched terms: {', '.join(result['matched_terms'])}")
        print(result["text"])


if __name__ == "__main__":
    main()