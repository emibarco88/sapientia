"""
Module: json_flattener.py

Purpose:
Flattens nested JSON objects and extracts array objects as child datasets.
"""

from collections import defaultdict


class JSONFlattener:
    def normalise_root(self, data):
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            list_values = [value for value in data.values() if isinstance(value, list)]

            if list_values:
                return max(list_values, key=len)

            return [data]

        raise ValueError("Unsupported JSON structure. Expected object or list.")

    def flatten_records(self, records: list, root_dataset_name: str):
        parent_records = []
        child_records_by_dataset = defaultdict(list)

        for parent_index, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                continue

            flattened_parent = {}

            self._flatten_object(
                obj=record,
                output=flattened_parent,
                child_records_by_dataset=child_records_by_dataset,
                root_dataset_name=root_dataset_name,
                parent_index=parent_index,
            )

            parent_records.append(flattened_parent)

        return parent_records, dict(child_records_by_dataset)

    def _flatten_object(
        self,
        obj: dict,
        output: dict,
        child_records_by_dataset: dict,
        root_dataset_name: str,
        parent_index: int,
        parent_key: str = "",
    ):
        for key, value in obj.items():
            clean_key = self._clean_key(key)
            full_key = f"{parent_key}.{clean_key}" if parent_key else clean_key

            if isinstance(value, dict):
                self._flatten_object(
                    obj=value,
                    output=output,
                    child_records_by_dataset=child_records_by_dataset,
                    root_dataset_name=root_dataset_name,
                    parent_index=parent_index,
                    parent_key=full_key,
                )

            elif isinstance(value, list):
                if value and all(isinstance(item, dict) for item in value):
                    child_dataset_name = f"{root_dataset_name}.{full_key}"

                    for child_index, item in enumerate(value, start=1):
                        child_record = {
                            "_parent_dataset": root_dataset_name,
                            "_parent_record_number": parent_index,
                            "_child_record_number": child_index,
                        }

                        self._flatten_simple_object(item, child_record)

                        child_records_by_dataset[child_dataset_name].append(child_record)

                    output[f"{full_key}._array_count"] = len(value)

                else:
                    output[full_key] = value

            else:
                output[full_key] = value

    def _flatten_simple_object(self, obj: dict, output: dict, parent_key: str = ""):
        for key, value in obj.items():
            clean_key = self._clean_key(key)
            full_key = f"{parent_key}.{clean_key}" if parent_key else clean_key

            if isinstance(value, dict):
                self._flatten_simple_object(value, output, full_key)
            else:
                output[full_key] = value

    def _clean_key(self, key) -> str:
        return (
            str(key)
            .strip()
            .replace(" ", "_")
            .replace("-", "_")
            .replace("/", "_")
        )