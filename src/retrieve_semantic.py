import argparse
import hashlib
import json
import math

from load_evidence import PROJECT_ROOT
from ollama_embeddings import EMBEDDING_MODEL, embed_texts
from retrieve_evidence import (
    APPLICABLE_ERROR_PATTERN,
    ERROR_CODE_PATTERN,
)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Query and index vector dimensions differ.")

    if not left or any(
        not math.isfinite(value) for value in left + right
    ):
        raise ValueError("Invalid embedding vector.")

    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0 or right_norm == 0:
        raise ValueError("Cannot compare zero vectors.")

    return sum(
        a * b for a, b in zip(left, right)
    ) / (left_norm * right_norm)


def load_index() -> dict:
    index_path = PROJECT_ROOT / "data" / "semantic_index.json"
    chunks_path = PROJECT_ROOT / "data" / "runbook_chunks.json"

    if not index_path.is_file():
        raise FileNotFoundError("Run build_semantic_index.py first.")

    index = json.loads(index_path.read_text(encoding="utf-8"))

    if index.get("format_version") != 1:
        raise ValueError("Unsupported semantic index format.")

    if index["model"] != EMBEDDING_MODEL:
        raise ValueError("Embedding model changed. Rebuild the index.")

    current_hash = hashlib.sha256(chunks_path.read_bytes()).hexdigest()

    if current_hash != index["chunks_sha256"]:
        raise ValueError(
            "Runbook chunks changed. Run build_semantic_index.py again."
        )

    entries = index["entries"]

    if not entries or len(entries) != index["chunk_count"]:
        raise ValueError("Index entry count is invalid. Rebuild the index.")

    if any(
        len(entry["vector"]) != index["dimensions"]
        for entry in entries
    ):
        raise ValueError("Index dimensions are invalid. Rebuild the index.")

    return index


def retrieve_semantic(
    query: str,
    index: dict,
    top_k: int = 3,
) -> list[dict]:
    if top_k <= 0 or not query.strip():
        return []

    entries = index["entries"]
    requested_codes = set(ERROR_CODE_PATTERN.findall(query))

    # Preserve the existing documented-applicability restriction.
    if requested_codes:
        sources_by_code = {}

        for entry in entries:
            chunk = entry["chunk"]

            for code in APPLICABLE_ERROR_PATTERN.findall(chunk["text"]):
                sources_by_code.setdefault(code, set()).add(chunk["source"])

        if any(code not in sources_by_code for code in requested_codes):
            return []

        applicable_sources = set()

        for code in requested_codes:
            applicable_sources.update(sources_by_code[code])

        entries = [
            entry for entry in entries
            if entry["chunk"]["source"] in applicable_sources
        ]

    query_vector = embed_texts(
        [query],
        model=index["model"],
    )[0]

    if len(query_vector) != index["dimensions"]:
        raise ValueError("Query dimensions differ from the saved index.")

    results = []

    for entry in entries:
        results.append({
            **entry["chunk"],
            "score": cosine_similarity(query_vector, entry["vector"]),
        })

    results.sort(key=lambda item: (-item["score"], item["chunk_id"]))
    return results[:top_k]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Incident description or error code")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    index = load_index()
    results = retrieve_semantic(args.query, index, args.top_k)

    if not results:
        print("No matching evidence found.")
        return

    for rank, result in enumerate(results, start=1):
        citation = (
            f"{result['source']}:"
            f"L{result['start_line']}-L{result['end_line']}"
        )

        print(f"\nRESULT {rank}: {result['heading']}")
        print(f"Cosine similarity: {result['score']:.3f}")
        print(f"Citation: [{citation}]")
        print(result["text"])


if __name__ == "__main__":
    main()