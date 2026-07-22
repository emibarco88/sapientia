"""
Module: pdf_connector.py

Purpose:
Represents a PDF document as an Enterprise Asset so that it can
participate in the standard Sapientia connector lifecycle.

This connector performs structure-aware PDF extraction.

It extracts:

- Document page text
- Detected headings
- PDF tables
- Table headers
- Individual table rows
- Structured JSON representations of table rows
- Fallback knowledge chunks

The Knowledge Acquisition PDF connector may still persist the PDF into
ekr_knowledge.document and ekr_knowledge.document_chunk.

This connector creates the structured dataset representation required by:

- Connector discovery scope
- Enterprise profiling
- Enterprise Understanding
- Connector lifecycle reporting
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sapientia.connectors.base_connector import (
    BaseConnector,
)
from sapientia.engines.knowledge_acquisition.connectors.pdf_connector import (
    PDFKnowledgeConnector,
)
from sapientia.models.metadata import (
    ColumnMetadata,
    DatasetMetadata,
)

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


class PDFConnector(BaseConnector):
    """
    Convert an uploaded PDF into the shared DatasetMetadata model.

    A PDF is represented as one enterprise dataset containing different
    record types.

    Supported record types:

    PAGE_TEXT
        One record containing the extracted text for a PDF page.

    TABLE_ROW
        One record for every row extracted from a PDF table.

    KNOWLEDGE_CHUNK
        Fallback record created from the existing knowledge connector
        when layout-aware extraction cannot retrieve usable content.

    Every record follows the same schema:

    - record_type
    - page_number
    - table_number
    - row_number
    - heading
    - content
    - structured_data
    """

    RECORD_TYPE_PAGE_TEXT = "PAGE_TEXT"
    RECORD_TYPE_TABLE_ROW = "TABLE_ROW"
    RECORD_TYPE_KNOWLEDGE_CHUNK = "KNOWLEDGE_CHUNK"

    def __init__(self) -> None:
        self.knowledge_connector = PDFKnowledgeConnector()

    def extract_schema(
        self,
        source: str,
    ) -> DatasetMetadata:
        """
        Extract the technical dataset representation of the PDF.

        The schema is designed to support both narrative document
        content and structured PDF tables.
        """

        file_path = self._validate_file(
            source
        )

        records = self._extract_records_internal(
            file_path=file_path,
        )

        columns = [
            ColumnMetadata(
                name="record_type",
                ordinal_position=1,
                data_type="VARCHAR",
                nullable=False,
                length=self._maximum_length(
                    [
                        record.get("record_type")
                        for record in records
                    ]
                ),
            ),
            ColumnMetadata(
                name="page_number",
                ordinal_position=2,
                data_type="INTEGER",
                nullable=True,
                length=None,
            ),
            ColumnMetadata(
                name="table_number",
                ordinal_position=3,
                data_type="INTEGER",
                nullable=True,
                length=None,
            ),
            ColumnMetadata(
                name="row_number",
                ordinal_position=4,
                data_type="INTEGER",
                nullable=True,
                length=None,
            ),
            ColumnMetadata(
                name="heading",
                ordinal_position=5,
                data_type="VARCHAR",
                nullable=True,
                length=self._maximum_length(
                    [
                        record.get("heading")
                        for record in records
                    ]
                ),
            ),
            ColumnMetadata(
                name="content",
                ordinal_position=6,
                data_type="TEXT",
                nullable=False,
                length=self._maximum_length(
                    [
                        record.get("content")
                        for record in records
                    ]
                ),
            ),
            ColumnMetadata(
                name="structured_data",
                ordinal_position=7,
                data_type="JSON",
                nullable=True,
                length=self._maximum_length(
                    [
                        record.get(
                            "structured_data"
                        )
                        for record in records
                    ]
                ),
            ),
        ]

        return DatasetMetadata(
            name=file_path.name,
            object_type="PDF_DOCUMENT",
            location=str(file_path),
            row_count=len(records),
            column_count=len(columns),
            file_size_bytes=(
                file_path.stat().st_size
            ),
            columns=columns,

            # The current discovery engine retrieves records separately
            # through extract_records(). Keeping this empty preserves the
            # behaviour used by CSV, JSON and the previous PDF connector.
            records=[],
        )

    def extract_records(
        self,
        source: str,
        limit: int | None = None,
    ) -> list[dict]:
        """
        Return PDF page content and table rows as representative records.
        """

        file_path = self._validate_file(
            source
        )

        records = self._extract_records_internal(
            file_path=file_path,
        )

        if limit is not None:
            safe_limit = int(limit)

            if safe_limit <= 0:
                return []

            return records[:safe_limit]

        return records

    def extract_metadata(
        self,
        source: str,
    ) -> DatasetMetadata:
        """
        Backward-compatible alias.
        """

        return self.extract_schema(
            source
        )

    def extract_document_summary(
        self,
        source: str,
    ) -> dict:
        """
        Return a summary of the extracted PDF content.

        This method is optional and does not affect the BaseConnector
        interface. It can be used later by the connector API or UI.
        """

        file_path = self._validate_file(
            source
        )

        records = self._extract_records_internal(
            file_path=file_path,
        )

        page_records = [
            record
            for record in records
            if record.get("record_type")
            == self.RECORD_TYPE_PAGE_TEXT
        ]

        table_records = [
            record
            for record in records
            if record.get("record_type")
            == self.RECORD_TYPE_TABLE_ROW
        ]

        fallback_records = [
            record
            for record in records
            if record.get("record_type")
            == self.RECORD_TYPE_KNOWLEDGE_CHUNK
        ]

        unique_tables = {
            (
                record.get("page_number"),
                record.get("table_number"),
            )
            for record in table_records
        }

        return {
            "document_name": file_path.name,
            "location": str(file_path),
            "file_size_bytes": (
                file_path.stat().st_size
            ),
            "pages_with_text": len(
                page_records
            ),
            "tables_discovered": len(
                unique_tables
            ),
            "table_rows_discovered": len(
                table_records
            ),
            "fallback_chunks": len(
                fallback_records
            ),
            "records_discovered": len(
                records
            ),
        }

    def _extract_records_internal(
        self,
        file_path: Path,
    ) -> list[dict]:
        """
        Perform structure-aware PDF extraction.

        pdfplumber is used first because it can retain page boundaries and
        extract tabular structures.

        The existing PDFKnowledgeConnector is used as a fallback when no
        meaningful page text or table data can be extracted.
        """

        if pdfplumber is None:
            raise RuntimeError(
                "PDF layout extraction requires "
                "the 'pdfplumber' package. "
                "Install it with: "
                "pip install pdfplumber"
            )

        records: list[dict] = []

        with pdfplumber.open(
            str(file_path)
        ) as pdf:
            for page_index, page in enumerate(
                pdf.pages,
                start=1,
            ):
                page_text = self._clean_text(
                    page.extract_text() or ""
                )

                heading = self._detect_heading(
                    page_text
                )

                if page_text:
                    records.append(
                        {
                            "record_type":
                                self.RECORD_TYPE_PAGE_TEXT,

                            "page_number":
                                page_index,

                            "table_number":
                                None,

                            "row_number":
                                None,

                            "heading":
                                heading,

                            "content":
                                page_text,

                            "structured_data":
                                self._json_dumps(
                                    {
                                        "source_type":
                                            "PDF_PAGE",

                                        "page_number":
                                            page_index,

                                        "heading":
                                            heading,
                                    }
                                ),
                        }
                    )

                extracted_tables = (
                    page.extract_tables() or []
                )

                for table_index, raw_table in enumerate(
                    extracted_tables,
                    start=1,
                ):
                    table_records = (
                        self._convert_table_to_records(
                            raw_table=raw_table,
                            page_number=page_index,
                            table_number=table_index,
                            page_heading=heading,
                        )
                    )

                    records.extend(
                        table_records
                    )

        if not records:
            records = self._extract_fallback_chunks(
                file_path=file_path,
            )

        return records

    def _convert_table_to_records(
        self,
        raw_table: list[list[Any]] | None,
        page_number: int,
        table_number: int,
        page_heading: str | None,
    ) -> list[dict]:
        """
        Convert a pdfplumber table into structured TABLE_ROW records.
        """

        if not raw_table:
            return []

        normalized_rows = [
            [
                self._clean_cell(cell)
                for cell in row
            ]
            for row in raw_table
            if row
        ]

        normalized_rows = [
            row
            for row in normalized_rows
            if any(
                value
                for value in row
            )
        ]

        if not normalized_rows:
            return []

        maximum_column_count = max(
            len(row)
            for row in normalized_rows
        )

        padded_rows = [
            row + (
                [""] * (
                    maximum_column_count
                    - len(row)
                )
            )
            for row in normalized_rows
        ]

        first_row = padded_rows[0]

        has_header = self._looks_like_header(
            first_row=first_row,
            remaining_rows=padded_rows[1:],
        )

        if has_header:
            headers = self._normalise_headers(
                first_row
            )

            data_rows = padded_rows[1:]
        else:
            headers = [
                f"column_{index}"
                for index in range(
                    1,
                    maximum_column_count + 1,
                )
            ]

            data_rows = padded_rows

        table_records: list[dict] = []

        for row_index, row in enumerate(
            data_rows,
            start=1,
        ):
            row_values = {
                headers[column_index]:
                    (
                        row[column_index]
                        if column_index
                        < len(row)
                        else ""
                    )
                for column_index
                in range(len(headers))
            }

            if not any(
                str(value).strip()
                for value in row_values.values()
            ):
                continue

            readable_content = (
                self._create_readable_table_content(
                    row_values
                )
            )

            structured_payload = {
                "source_type":
                    "PDF_TABLE_ROW",

                "page_number":
                    page_number,

                "table_number":
                    table_number,

                "row_number":
                    row_index,

                "heading":
                    page_heading,

                "columns":
                    headers,

                "values":
                    row_values,
            }

            table_records.append(
                {
                    "record_type":
                        self.RECORD_TYPE_TABLE_ROW,

                    "page_number":
                        page_number,

                    "table_number":
                        table_number,

                    "row_number":
                        row_index,

                    "heading":
                        page_heading,

                    "content":
                        readable_content,

                    "structured_data":
                        self._json_dumps(
                            structured_payload
                        ),
                }
            )

        return table_records

    def _extract_fallback_chunks(
        self,
        file_path: Path,
    ) -> list[dict]:
        """
        Use the existing Knowledge Acquisition connector as fallback.
        """

        document = (
            self.knowledge_connector
            .load_document(
                str(file_path)
            )
        )

        records: list[dict] = []

        for index, chunk in enumerate(
            document.chunks or [],
            start=1,
        ):
            chunk_number = int(
                getattr(
                    chunk,
                    "chunk_number",
                    index,
                )
                or index
            )

            heading = getattr(
                chunk,
                "heading",
                None,
            )

            content = self._clean_text(
                str(
                    getattr(
                        chunk,
                        "content",
                        "",
                    )
                    or ""
                )
            )

            if not content:
                continue

            page_number = getattr(
                chunk,
                "page_number",
                None,
            )

            records.append(
                {
                    "record_type":
                        self.RECORD_TYPE_KNOWLEDGE_CHUNK,

                    "page_number":
                        (
                            int(page_number)
                            if page_number is not None
                            else None
                        ),

                    "table_number":
                        None,

                    "row_number":
                        chunk_number,

                    "heading":
                        heading,

                    "content":
                        content,

                    "structured_data":
                        self._json_dumps(
                            {
                                "source_type":
                                    "PDF_KNOWLEDGE_CHUNK",

                                "chunk_number":
                                    chunk_number,

                                "page_number":
                                    page_number,

                                "heading":
                                    heading,
                            }
                        ),
                }
            )

        return records

    def _looks_like_header(
        self,
        first_row: list[str],
        remaining_rows: list[list[str]],
    ) -> bool:
        """
        Estimate whether the first table row contains column headers.

        This is intentionally deterministic and conservative.
        """

        populated_values = [
            value
            for value in first_row
            if value
        ]

        if not populated_values:
            return False

        unique_values = {
            value.lower()
            for value in populated_values
        }

        if (
            len(unique_values)
            != len(populated_values)
        ):
            return False

        alphabetic_values = sum(
            1
            for value in populated_values
            if any(
                character.isalpha()
                for character in value
            )
        )

        numeric_values = sum(
            1
            for value in populated_values
            if self._looks_numeric(
                value
            )
        )

        # A row containing mostly descriptive labels is likely a header.
        if (
            alphabetic_values
            >= max(
                1,
                len(populated_values) // 2,
            )
            and numeric_values
            <= len(populated_values) // 2
        ):
            return True

        # Compare first-row data types with subsequent rows. A first row
        # containing text labels followed by numeric or date values is
        # also likely to be a header.
        if remaining_rows:
            first_data_row = remaining_rows[0]

            different_type_count = 0

            for index, first_value in enumerate(
                first_row
            ):
                if index >= len(
                    first_data_row
                ):
                    continue

                second_value = (
                    first_data_row[index]
                )

                if (
                    self._value_type(first_value)
                    != self._value_type(
                        second_value
                    )
                ):
                    different_type_count += 1

            if (
                different_type_count
                >= max(
                    1,
                    len(populated_values) // 2,
                )
            ):
                return True

        return False

    def _normalise_headers(
        self,
        raw_headers: list[str],
    ) -> list[str]:
        """
        Produce unique, stable table column names.
        """

        headers: list[str] = []
        used_names: dict[str, int] = {}

        for index, raw_header in enumerate(
            raw_headers,
            start=1,
        ):
            header = self._normalise_identifier(
                raw_header
            )

            if not header:
                header = f"column_{index}"

            count = used_names.get(
                header,
                0,
            )

            used_names[header] = (
                count + 1
            )

            if count:
                header = (
                    f"{header}_{count + 1}"
                )

            headers.append(
                header
            )

        return headers

    def _normalise_identifier(
        self,
        value: str | None,
    ) -> str:
        """
        Convert a table header to a stable field name.
        """

        text = self._clean_cell(
            value
        ).lower()

        text = re.sub(
            r"[^a-z0-9]+",
            "_",
            text,
        )

        return text.strip("_")

    def _detect_heading(
        self,
        page_text: str,
    ) -> str | None:
        """
        Detect a likely page or section heading.

        The first short meaningful line is treated as the heading.
        """

        if not page_text:
            return None

        lines = [
            line.strip()
            for line in page_text.splitlines()
            if line.strip()
        ]

        for line in lines[:8]:
            if (
                len(line) <= 160
                and not self._looks_numeric(
                    line
                )
            ):
                return line

        return None

    def _create_readable_table_content(
        self,
        row_values: dict[str, Any],
    ) -> str:
        """
        Produce searchable narrative content for a table row.
        """

        parts = [
            f"{column}: {value}"
            for column, value
            in row_values.items()
            if value is not None
            and str(value).strip()
        ]

        return " | ".join(parts)

    def _clean_text(
        self,
        value: str | None,
    ) -> str:
        """
        Clean extracted narrative text while preserving line boundaries.
        """

        if value is None:
            return ""

        text = str(value).replace(
            "\x00",
            "",
        )

        lines = [
            re.sub(
                r"[ \t]+",
                " ",
                line,
            ).strip()
            for line in text.splitlines()
        ]

        lines = [
            line
            for line in lines
            if line
        ]

        return "\n".join(
            lines
        ).strip()

    def _clean_cell(
        self,
        value: Any,
    ) -> str:
        """
        Clean an extracted PDF table cell.
        """

        if value is None:
            return ""

        text = str(value).replace(
            "\x00",
            "",
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def _looks_numeric(
        self,
        value: str,
    ) -> bool:
        """
        Identify numeric, currency, percentage and accounting values.
        """

        text = str(value).strip()

        if not text:
            return False

        normalized = (
            text.replace(",", "")
            .replace("$", "")
            .replace("€", "")
            .replace("£", "")
            .replace("%", "")
            .strip()
        )

        if (
            normalized.startswith("(")
            and normalized.endswith(")")
        ):
            normalized = (
                normalized[1:-1]
            )

        try:
            float(normalized)
            return True
        except ValueError:
            return False

    def _value_type(
        self,
        value: str,
    ) -> str:
        """
        Return a simple deterministic value type.
        """

        if not value:
            return "EMPTY"

        if self._looks_numeric(
            value
        ):
            return "NUMBER"

        if re.fullmatch(
            r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}",
            value.strip(),
        ):
            return "DATE"

        return "TEXT"

    def _json_dumps(
        self,
        value: dict,
    ) -> str:
        """
        Serialize structured data consistently.
        """

        return json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        )

    def _validate_file(
        self,
        source: str,
    ) -> Path:
        file_path = Path(
            source
        ).expanduser().resolve()

        if not file_path.exists():
            raise FileNotFoundError(
                "PDF file not found: "
                f"{file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                "PDF source is not a file: "
                f"{file_path}"
            )

        if (
            file_path.suffix.lower()
            != ".pdf"
        ):
            raise ValueError(
                "PDFConnector only supports "
                ".pdf files."
            )

        return file_path

    def _maximum_length(
        self,
        values: list,
    ) -> int | None:
        lengths = [
            len(str(value))
            for value in values
            if value is not None
            and str(value)
        ]

        if not lengths:
            return None

        return max(lengths)