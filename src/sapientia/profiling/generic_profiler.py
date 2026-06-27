"""
Module: generic_profiler.py

Purpose:
Profiles any tabular dataset represented as a list of dictionaries.
"""

import json
import math
from collections import Counter
from datetime import datetime

from sapientia.models.profile import DatasetProfile, ColumnProfile


class GenericProfiler:
    def profile_records(self, records: list[dict]) -> DatasetProfile:
        safe_records = [self._normalise_record(record) for record in records]
        column_names = self._get_column_names(safe_records)

        column_profiles = [
            self._profile_column(
                column_name=column_name,
                values=[record.get(column_name) for record in safe_records],
                row_count=len(safe_records),
            )
            for column_name in column_names
        ]

        return DatasetProfile(
            row_count=len(safe_records),
            column_count=len(column_names),
            duplicate_rows=self._count_duplicate_rows(safe_records),
            column_profiles=column_profiles,
            sample_rows=safe_records[:10],
            profile_json={
                "profiler": "GenericProfiler",
                "engine": "pure_python",
            },
        )

    def _profile_column(self, column_name: str, values: list, row_count: int) -> ColumnProfile:
        null_count = sum(1 for value in values if value is None)
        non_null_values = [value for value in values if value is not None]

        distinct_values = {self._serialise_value(value) for value in non_null_values}
        string_values = [self._to_string(value) for value in non_null_values]

        inferred_type = self._infer_value_type(non_null_values)

        completeness_score = self._percentage(row_count - null_count, row_count)
        uniqueness_score = self._percentage(len(distinct_values), row_count)
        validity_score = 100.0
        consistency_score = self._consistency_score(non_null_values)
        quality_score = round(
            (completeness_score + uniqueness_score + validity_score + consistency_score) / 4,
            4,
        )

        return ColumnProfile(
            column_name=column_name,
            null_count=null_count,
            null_percentage=self._percentage(null_count, row_count),
            distinct_count=len(distinct_values),
            unique_percentage=uniqueness_score,
            min_value=self._typed_min(non_null_values, inferred_type),
            max_value=self._typed_max(non_null_values, inferred_type),
            min_length=self._safe_min_length(string_values),
            max_length=self._safe_max_length(string_values),
            avg_length=self._safe_avg_length(string_values),
            inferred_data_type=inferred_type,
            completeness_score=completeness_score,
            validity_score=validity_score,
            consistency_score=consistency_score,
            uniqueness_score=uniqueness_score,
            quality_score=quality_score,
            sample_values=self._sample_values(non_null_values),
            top_values=self._top_values(non_null_values),
            pattern_summary=self._pattern_summary(non_null_values),
            numeric_summary=self._numeric_summary(non_null_values, inferred_type),
            date_summary=self._date_summary(non_null_values, inferred_type),
            boolean_summary=self._boolean_summary(non_null_values, inferred_type),
            structure_summary=self._structure_summary(non_null_values),
            anomaly_summary={},
            profile_json={
                "raw_python_types": self._raw_python_types(non_null_values),
            },
        )

    def _normalise_record(self, record: dict) -> dict:
        return {str(key): self._normalise_value(value) for key, value in record.items()}

    def _normalise_value(self, value):
        if self._is_null_like(value):
            return None

        if isinstance(value, dict):
            return {str(k): self._normalise_value(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._normalise_value(item) for item in value]

        return value

    def _is_null_like(self, value) -> bool:
        if value is None:
            return True

        if isinstance(value, float):
            return math.isnan(value) or math.isinf(value)

        return False

    def _get_column_names(self, records: list[dict]) -> list[str]:
        column_names = []

        for record in records:
            for key in record.keys():
                if key not in column_names:
                    column_names.append(key)

        return column_names

    def _count_duplicate_rows(self, records: list[dict]) -> int:
        serialised_rows = [self._serialise_value(record) for record in records]
        return len(serialised_rows) - len(set(serialised_rows))

    def _serialise_value(self, value) -> str:
        return json.dumps(
            self._normalise_value(value),
            sort_keys=True,
            default=str,
            ensure_ascii=False,
            allow_nan=False,
        )

    def _to_string(self, value) -> str:
        if isinstance(value, (dict, list)):
            return self._serialise_value(value)

        return str(value)

    def _percentage(self, value: int, total: int) -> float:
        if total == 0:
            return 0.0

        return round((value / total) * 100, 4)

    def _infer_value_type(self, values: list) -> str:
        if not values:
            return "NULL_ONLY"

        if all(isinstance(value, bool) for value in values):
            return "BOOLEAN"

        if all(isinstance(value, int) and not isinstance(value, bool) for value in values):
            return "INTEGER"

        if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
            return "NUMERIC"

        if all(self._parse_date(value) is not None for value in values):
            return "DATE_OR_TIMESTAMP"

        if all(isinstance(value, list) for value in values):
            return "ARRAY"

        if all(isinstance(value, dict) for value in values):
            return "OBJECT"

        type_names = {type(value).__name__ for value in values}

        if len(type_names) > 1:
            return "MIXED"

        return "STRING"

    def _consistency_score(self, values: list) -> float:
        if not values:
            return 100.0

        type_counts = Counter(type(value).__name__ for value in values)
        most_common_count = type_counts.most_common(1)[0][1]

        return self._percentage(most_common_count, len(values))

    def _typed_min(self, values: list, inferred_type: str):
        if not values:
            return None

        try:
            if inferred_type in ("INTEGER", "NUMERIC"):
                return str(min(values))

            if inferred_type == "DATE_OR_TIMESTAMP":
                parsed = [self._parse_date(value) for value in values]
                return min(parsed).isoformat()

            return None
        except Exception:
            return None

    def _typed_max(self, values: list, inferred_type: str):
        if not values:
            return None

        try:
            if inferred_type in ("INTEGER", "NUMERIC"):
                return str(max(values))

            if inferred_type == "DATE_OR_TIMESTAMP":
                parsed = [self._parse_date(value) for value in values]
                return max(parsed).isoformat()

            return None
        except Exception:
            return None

    def _numeric_summary(self, values: list, inferred_type: str) -> dict:
        if inferred_type not in ("INTEGER", "NUMERIC") or not values:
            return {}

        numeric_values = [float(value) for value in values]

        return {
            "min": min(numeric_values),
            "max": max(numeric_values),
            "sum": sum(numeric_values),
            "average": round(sum(numeric_values) / len(numeric_values), 4),
            "zero_count": sum(1 for value in numeric_values if value == 0),
            "negative_count": sum(1 for value in numeric_values if value < 0),
            "positive_count": sum(1 for value in numeric_values if value > 0),
        }

    def _date_summary(self, values: list, inferred_type: str) -> dict:
        if inferred_type != "DATE_OR_TIMESTAMP" or not values:
            return {}

        parsed_dates = [self._parse_date(value) for value in values]
        min_date = min(parsed_dates)
        max_date = max(parsed_dates)

        return {
            "min_date": min_date.isoformat(),
            "max_date": max_date.isoformat(),
            "days_span": (max_date - min_date).days,
        }

    def _boolean_summary(self, values: list, inferred_type: str) -> dict:
        if inferred_type != "BOOLEAN" or not values:
            return {}

        true_count = sum(1 for value in values if value is True)
        false_count = sum(1 for value in values if value is False)

        return {
            "true_count": true_count,
            "false_count": false_count,
            "true_percentage": self._percentage(true_count, len(values)),
            "false_percentage": self._percentage(false_count, len(values)),
        }

    def _structure_summary(self, values: list) -> dict:
        if not values:
            return {}

        array_values = [value for value in values if isinstance(value, list)]
        object_values = [value for value in values if isinstance(value, dict)]

        summary = {}

        if array_values:
            lengths = [len(value) for value in array_values]
            summary["array_count"] = len(array_values)
            summary["min_array_length"] = min(lengths)
            summary["max_array_length"] = max(lengths)
            summary["avg_array_length"] = round(sum(lengths) / len(lengths), 4)

        if object_values:
            key_counts = [len(value.keys()) for value in object_values]
            summary["object_count"] = len(object_values)
            summary["min_key_count"] = min(key_counts)
            summary["max_key_count"] = max(key_counts)
            summary["avg_key_count"] = round(sum(key_counts) / len(key_counts), 4)

        return summary

    def _pattern_summary(self, values: list) -> dict:
        string_values = [self._to_string(value) for value in values if value is not None]

        if not string_values:
            return {}

        return {
            "all_uppercase_count": sum(1 for value in string_values if value.isupper()),
            "all_lowercase_count": sum(1 for value in string_values if value.islower()),
            "contains_digit_count": sum(1 for value in string_values if any(ch.isdigit() for ch in value)),
            "contains_at_symbol_count": sum(1 for value in string_values if "@" in value),
        }

    def _safe_min_length(self, values: list[str]):
        if not values:
            return None

        return min(len(value) for value in values)

    def _safe_max_length(self, values: list[str]):
        if not values:
            return None

        return max(len(value) for value in values)

    def _safe_avg_length(self, values: list[str]):
        if not values:
            return None

        return round(sum(len(value) for value in values) / len(values), 4)

    def _sample_values(self, values: list) -> list[str]:
        sample_values = []
        seen = set()

        for value in values:
            serialised = self._serialise_value(value)

            if serialised not in seen:
                sample_values.append(self._to_string(value))
                seen.add(serialised)

            if len(sample_values) >= 10:
                break

        return sample_values

    def _top_values(self, values: list) -> list[dict]:
        serialised_values = [self._serialise_value(value) for value in values]
        counter = Counter(serialised_values)

        return [
            {"value": value, "count": count}
            for value, count in counter.most_common(10)
        ]

    def _raw_python_types(self, values: list) -> dict:
        return dict(Counter(type(value).__name__ for value in values))

    def _parse_date(self, value):
        if not isinstance(value, str):
            return None

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        return None