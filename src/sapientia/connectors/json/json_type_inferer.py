"""
Module: json_type_inferer.py

Purpose:
Infers generic data types from JSON values.
"""

from datetime import datetime


class JSONTypeInferer:
    def infer(self, values: list) -> str:
        non_null_values = [value for value in values if value is not None]

        if not non_null_values:
            return "VARCHAR"

        if all(isinstance(value, bool) for value in non_null_values):
            return "BOOLEAN"

        if all(isinstance(value, int) and not isinstance(value, bool) for value in non_null_values):
            return "INTEGER"

        if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in non_null_values):
            return "NUMERIC"

        if all(self._looks_like_timestamp(value) for value in non_null_values):
            return "TIMESTAMP"

        if all(self._looks_like_date(value) for value in non_null_values):
            return "DATE"

        if any(isinstance(value, (dict, list)) for value in non_null_values):
            return "JSONB"

        return "VARCHAR"

    def max_length(self, values: list):
        non_null_values = [value for value in values if value is not None]

        if not non_null_values:
            return None

        return max(len(str(value)) for value in non_null_values)

    def _looks_like_date(self, value) -> bool:
        if not isinstance(value, str):
            return False

        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue

        return False

    def _looks_like_timestamp(self, value) -> bool:
        if not isinstance(value, str):
            return False

        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue

        return False