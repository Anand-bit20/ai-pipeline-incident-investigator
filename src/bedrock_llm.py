
import boto3
from botocore.exceptions import BotoCoreError, ClientError

AWS_REGION = "ap-south-1"
MODEL_ID = "global.amazon.nova-2-lite-v1:0"


def generate_text(system_prompt: str, user_prompt: str) -> str:
    """Generate an AI response using Amazon Nova 2 Lite."""

    client = boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
    )

    try:
        response = client.converse(
            modelId=MODEL_ID,
            system=[
                {"text": system_prompt}
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"text": user_prompt}
                    ],
                }
            ],
            inferenceConfig={
                "maxTokens": 1500,
                "temperature": 0,
            },
        )

    except (ClientError, BotoCoreError) as error:
        raise RuntimeError(
            f"Amazon Bedrock request failed: {error}"
        ) from error

    if response.get("stopReason") != "end_turn":
        raise RuntimeError(
            f"Unexpected model stop reason: "
            f"{response.get('stopReason')}"
        )

    content = response["output"]["message"]["content"]

    text = "".join(
        item["text"]
        for item in content
        if "text" in item
    ).strip()

    if not text:
        raise ValueError("Amazon Nova 2 Lite returned an empty response.")

    return text


if __name__ == "__main__":
    print(
        generate_text(
            "You are a data pipeline incident investigator.",
            "Explain briefly why a missing trip_id can block a release."
        )
    )
