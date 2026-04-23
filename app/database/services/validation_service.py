from __future__ import annotations

import csv
import io


class ValidationService:
    def validate_form(self, x1: float, x2: float) -> tuple[list[dict], list[dict]]:
        return ([{"x1": float(x1), "x2": float(x2)}], [])

    def validate_csv_bytes(self, content: bytes) -> tuple[list[dict], list[dict]]:
        decoded = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))

        valid_records: list[dict] = []
        invalid_records: list[dict] = []

        for index, row in enumerate(reader, start=1):
            try:
                x1 = float(row["x1"])
                x2 = float(row["x2"])
                valid_records.append({"x1": x1, "x2": x2})
            except Exception:
                invalid_records.append(
                    {
                        "row_number": index,
                        "raw_data": row,
                        "error_message": "Invalid row. Expected numeric x1 and x2.",
                    }
                )

        return valid_records, invalid_records