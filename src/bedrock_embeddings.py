
import json
import math
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError


EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
AWS_REGION = "ap-south-1"
EMBEDDING_DIMENSIONS = 1024


def embed_texts(
    texts: list[str],
    model: str = EMBEDDING_MODEL,
) -> list[list[float]]:
    """Generate and validate Titan V2 embeddings."""

    if not texts or any(
        not isinstance(text, str) or not text.strip()
        for text in texts
    ):
        raise ValueError(
            "Provide a non-empty list of non-empty texts."
        )

    client = boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
    )

    vectors = []

    for text in texts:
        payload = {
            "inputText": text,
            "dimensions": EMBEDDING_DIMENSIONS,
            "normalize": True,
        }

        try:
            response = client.invoke_model(
                modelId=model,
                body=json.dumps(payload),
                contentType="application/json",
                accept="application/json",
            )

            result = json.loads(
                response["body"].read()
            )

        except (ClientError, BotoCoreError) as error:
            raise RuntimeError(
                f"Bedrock embedding request failed: {error}"
            ) from error

        vector = result.get("embedding")

        if not isinstance(vector, list):
            raise ValueError("Invalid embedding response.")

        if len(vector) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
                f"received {len(vector)}."
            )

        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in vector
        ):
            raise ValueError(
                "Embedding contains invalid numeric values."
            )

        if not any(value != 0 for value in vector):
            raise ValueError("Bedrock returned a zero vector.")

        vectors.append(vector)

    return vectors


def main():
    text = "Data pipeline failed due to missing trip_id."

    start = time.perf_counter()
    vectors = embed_texts([text])

    print("Model:", EMBEDDING_MODEL)
    print("Embeddings returned:", len(vectors))
    print("Vector dimensions:", len(vectors[0]))
    print(
        "Request time:",
        round(time.perf_counter() - start, 2),
        "seconds",
    )


if __name__ == "__main__":
    main()
