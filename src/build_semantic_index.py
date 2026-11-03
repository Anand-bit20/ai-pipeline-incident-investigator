import hashlib
import json
import time
import argparse

from bedrock_embeddings import (
    EMBEDDING_MODEL as TITAN_MODEL,
    embed_texts as titan_embed_texts,
)
from ollama_embeddings import (
    EMBEDDING_MODEL as OLLAMA_MODEL,
    embed_texts as ollama_embed_texts,
)
from datetime import datetime, timezone
from pathlib import Path

from load_evidence import PROJECT_ROOT



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=["ollama", "bedrock"],
        default="ollama",
    )
    args = parser.parse_args()

    if args.provider == "bedrock":
        embedding_model = TITAN_MODEL
        embedding_function = titan_embed_texts
    else:
        embedding_model = OLLAMA_MODEL
        embedding_function = ollama_embed_texts

    chunks_path = PROJECT_ROOT / "data" / "runbook_chunks.json"

    if not chunks_path.is_file():
        raise FileNotFoundError("Run chunk_runbooks.py first.")

    chunks_bytes = chunks_path.read_bytes()
    chunks = json.loads(chunks_bytes.decode("utf-8"))

    if not chunks:
        raise ValueError("No runbook chunks found.")

    # Find each runbook's title in its overview chunk.
    titles = {}

    for chunk in chunks:
        if chunk["heading"] == "Document overview":
            for line in chunk["text"].splitlines():
                if line.startswith("# "):
                    titles[chunk["source"]] = line[2:].strip()
                    break

    inputs = []

    for chunk in chunks:
        title = titles.get(
            chunk["source"],
            Path(chunk["source"]).stem,
        )
        inputs.append(
            f"title: {title} - {chunk['heading']} | "
            f"text: {chunk['text']}"
        )

    print(
        f"Embedding {len(chunks)} chunks with {embedding_model}...",
        flush=True,
    )
    start = time.perf_counter()
    vectors = []
    batch_size = 8

    for offset in range(0, len(inputs), batch_size):
        batch = inputs[offset:offset + batch_size]
        vectors.extend(embedding_function(batch))

        print(
            f"Embedded {len(vectors)}/{len(chunks)} chunks",
            flush=True,
        )

    dimensions = len(vectors[0])

    if any(len(vector) != dimensions for vector in vectors):
        raise ValueError("Vector dimensions differ across batches.")

    index = {
        "format_version": 1,
        "model": embedding_model,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "chunks_sha256": hashlib.sha256(chunks_bytes).hexdigest(),
        "dimensions": dimensions,
        "chunk_count": len(chunks),
        "document_prefix": "title: {title} | text: {content}",
        "entries": [
            {
                "chunk": chunk,
                "embedding_input": text,
                "vector": vector,
            }
            for chunk, text, vector in zip(chunks, inputs, vectors)
        ],
    }

    filename = (
        "titan_semantic_index.json"
        if args.provider == "bedrock"
        else "semantic_index.json"
    )

    output = PROJECT_ROOT / "data" / filename
    temporary_output = output.with_suffix(".tmp")

    temporary_output.write_text(
        json.dumps(index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_output.replace(output)

    print(f"\nSaved index: {output}")
    print(f"Indexed chunks: {len(chunks)}")
    print(f"Vector dimensions: {dimensions}")
    print(f"Build time: {time.perf_counter() - start:.1f} seconds")


if __name__ == "__main__":
    main()