"""
Module: json_loader.py

Purpose:
Loads JSON files from disk.
"""

import json


class JSONLoader:
    def load(self, file_path: str):
        with open(file_path, "r", encoding="utf-8-sig") as file:
            return json.load(file)