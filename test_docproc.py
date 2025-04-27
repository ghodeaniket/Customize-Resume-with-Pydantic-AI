#!/usr/bin/env python3
"""Test the document processor."""
import asyncio
from infrastructure.document_processor import DocumentProcessor


async def test_processor():
    """Test basic text extraction."""
    processor = DocumentProcessor()
    text = await processor.extract_text_from_bytes(b'Some text content', 'text/plain')
    print("Extracted text:", text)


if __name__ == "__main__":
    asyncio.run(test_processor())
