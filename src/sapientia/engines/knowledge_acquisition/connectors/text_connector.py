"""
Module: text_connector.py

Purpose:
Loads local TXT and Markdown files for the Knowledge Acquisition Engine.
"""

import hashlib
import os

from sapientia.config.knowledge_config import KnowledgeConfig
from sapientia.models.knowledge import AcquiredDocument, DocumentChunk


class TextKnowledgeConnector:

    SUPPORTED_EXTENSIONS = [".txt", ".md", ".markdown"]

    def load_document(self, file_path: str) -> AcquiredDocument:
        extension = os.path.splitext(file_path)[1].lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported knowledge document type: {extension}")

        with open(file_path, "r", encoding="utf-8-sig") as file:
            content = file.read()

        title = os.path.basename(file_path)
        document_type = "MARKDOWN" if extension in [".md", ".markdown"] else "TXT"

        chunks = self._chunk_content(content)

        return AcquiredDocument(
            title=title,
            document_type=document_type,
            source_type="LOCAL_FILE",
            source_location=file_path,
            content_hash=self._hash_content(content),
            chunks=chunks,
        )

    def _chunk_content(self, content: str) -> list[DocumentChunk]:
        lines = content.splitlines()
        chunks = []
        current_lines = []
        current_heading = None
        chunk_number = 1
        start_line = 1

        for index, line in enumerate(lines, start=1):
            if line.strip().startswith("#"):
                current_heading = line.replace("#", "").strip()

            current_lines.append(line)

            current_text = "\n".join(current_lines)

            if len(current_text) >= KnowledgeConfig.CHUNK_SIZE:
                chunks.append(
                    DocumentChunk(
                        chunk_number=chunk_number,
                        heading=current_heading,
                        content=current_text.strip(),
                        start_line_number=start_line,
                        end_line_number=index,
                    )
                )

                chunk_number += 1
                current_lines = []
                start_line = index + 1

        if current_lines:
            chunks.append(
                DocumentChunk(
                    chunk_number=chunk_number,
                    heading=current_heading,
                    content="\n".join(current_lines).strip(),
                    start_line_number=start_line,
                    end_line_number=len(lines),
                )
            )

        return chunks

    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()