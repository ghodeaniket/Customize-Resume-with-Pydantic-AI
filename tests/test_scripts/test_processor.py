"""Simple test script for the DocumentProcessor.

This script tests the basic functionality of the DocumentProcessor.
"""

import asyncio
import os
from pathlib import Path

from resume_customizer.services.document.processor import DocumentProcessor, DocumentFormat


async def main():
    """Run a simple test of the DocumentProcessor."""
    # Create a test text file
    test_dir = Path("./test_data")
    os.makedirs(test_dir, exist_ok=True)
    
    test_file = test_dir / "test_resume.txt"
    with open(test_file, "w") as f:
        f.write("Sample resume content for testing.\n")
        f.write("Professional experience in Python, FastAPI, and document processing.\n")
        f.write("Skills: Python, FastAPI, Document Processing\n")
    
    # Extract text from the file
    print(f"Extracting text from {test_file}...")
    text = await DocumentProcessor.extract_text(test_file)
    print(f"Extracted text:\n{text}")
    
    # Clean up
    os.remove(test_file)
    os.rmdir(test_dir)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
