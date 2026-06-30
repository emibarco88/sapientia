"""
Module: pdf_connector.py

Purpose:
Loads PDF documents and converts them into Sapientia document chunks
for the Knowledge Acquisition Engine.
"""

import hashlib
from pathlib import Path
from types import SimpleNamespace

from pypdf import PdfReader


class PDFKnowledgeConnector:
    def load_document(self, file_path: str):
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        reader = PdfReader(str(path))

        full_text_parts = []
        page_texts = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()

            if text:
                page_texts.append(
                    {
                        "page_number": page_number,
                        "text": text,
                    }
                )
                full_text_parts.append(text)

        full_text = "\n\n".join(full_text_parts)
        content_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

        chunks = self._create_chunks(page_texts)

        return SimpleNamespace(
            title=path.name,
            document_type="PDF",
            source_type="LOCAL_FILE",
            source_location=file_path,
            content_hash=content_hash,
            chunks=chunks,
            knowledge_items=[],
        )

    def _create_chunks(self, page_texts: list[dict]) -> list:
        chunks = []

        for page in page_texts:
            page_number = page["page_number"]
            text = page["text"]

            paragraphs = [
                paragraph.strip()
                for paragraph in text.split("\n\n")
                if paragraph.strip()
            ]

            if not paragraphs:
                paragraphs = [text]

            for paragraph in paragraphs:
                chunks.append(
                    SimpleNamespace(
                        chunk_number=len(chunks) + 1,
                        heading=f"Page {page_number}",
                        content=paragraph,
                        start_line_number=None,
                        end_line_number=None,
                    )
                )

        return chunks