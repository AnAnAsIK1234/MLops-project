from __future__ import annotations


def run_batch_prediction(records: list[dict]) -> tuple[list[dict], dict]:
    results: list[dict] = []

    for row in records:
        x1 = row["x1"]
        x2 = row["x2"]
        prediction = round((x1 * 0.4) + (x2 * 0.6), 4)

        results.append(
            {
                "input": {"x1": x1, "x2": x2},
                "prediction": prediction,
            }
        )

    avg_prediction = round(sum(item["prediction"] for item in results) / len(results), 4) if results else 0.0

    summary = {
        "processed_count": len(results),
        "avg_prediction": avg_prediction,
    }
    return results, summary