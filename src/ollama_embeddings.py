import json
import math
import time
import urllib.error
import urllib.request


EMBEDDING_MODEL = "embeddinggemma:latest"


def embed_texts(
    texts: list[str],
    model: str = EMBEDDING_MODEL,
) -> list[list[float]]:
    if not texts or any(
        not isinstance(text, str) or not text.strip()
        for text in texts
    ):
        raise ValueError("Provide a non-empty list of non-empty texts.")

    payload = {
        "model": model,
        "input": texts,
        "truncate": False,
    }

    request = urllib.request.Request(
        "http://localhost:11434/api/embed",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Ollama embedding error {error.code}: {details}"
        ) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(
            f"Could not complete the local embedding request: {error}"
        ) from error

    vectors = result.get("embeddings")

    if not isinstance(vectors, list) or len(vectors) != len(texts):
        raise ValueError("Ollama returned an unexpected embedding count.")

    dimensions = None

    for vector in vectors:
        if not isinstance(vector, list) or not vector:
            raise ValueError("Ollama returned an empty or invalid vector.")

        if any(
            not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in vector
        ):
            raise ValueError("Embedding contains invalid numeric values.")

        if dimensions is None:
            dimensions = len(vector)
        elif len(vector) != dimensions:
            raise ValueError("Embedding dimensions are inconsistent.")

        if not any(value != 0 for value in vector):
            raise ValueError("Ollama returned a zero vector.")

    return vectors


def main() -> None:
    text = "An API request timed out during pipeline extraction."

    start = time.perf_counter()
    vectors = embed_texts([text])

    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Embeddings returned: {len(vectors)}")
    print(f"Vector dimensions: {len(vectors[0])}")
    print(f"Request time: {time.perf_counter() - start:.1f} seconds")


if __name__ == "__main__":
    main()