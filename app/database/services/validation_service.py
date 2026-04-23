from __future__ import annotations

import csv
import io


class ValidationService:
    def validate_form(self, prompt: str) -> tuple[list[dict], list[dict]]:
        prompt = (prompt or "").strip()
        if not prompt:
            return [], [
                {
                    "row_number": 1,
                    "raw_data": {"prompt": prompt},
                    "error_message": "Prompt cannot be empty.",
                }
            ]
        return ([{"prompt": prompt}], [])

    def validate_csv_bytes(self, content: bytes) -> tuple[list[dict], list[dict]]:
        decoded = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))

        valid_records: list[dict] = []
        invalid_records: list[dict] = []

        if not reader.fieldnames or "prompt" not in reader.fieldnames:
            return [], [
                {
                    "row_number": 0,
                    "raw_data": {},
                    "error_message": "CSV must contain a 'prompt' column.",
                }
            ]

        for index, row in enumerate(reader, start=1):
            prompt = (row.get("prompt") or "").strip()
            if not prompt:
                invalid_records.append(
                    {
                        "row_number": index,
                        "raw_data": row,
                        "error_message": "Prompt cannot be empty.",
                    }
                )
                continue

            valid_records.append({"prompt": prompt})

        return valid_records, invalid_records