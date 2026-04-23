from __future__ import annotations

from src.ollama_client import generate_text


def run_batch_prediction(records: list[dict]) -> tuple[list[dict], dict]:
    results: list[dict] = []

    for row in records:
        prompt = row["prompt"]
        response_text = generate_text(prompt)

        results.append(
            {
                "input": {
                    "prompt": prompt,
                },
                "response": response_text,
            }
        )

    summary = {
        "processed_count": len(results),
        "backend": "ollama",
        "response_type": "text",
    }
    return results, summary