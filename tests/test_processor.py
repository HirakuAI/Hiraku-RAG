"""FYP"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.document_processor import DocumentProcessor

def test_processor():
    processor = DocumentProcessor()

    test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "test")
    results = processor.process_directory(test_dir)

    for doc in results:
        print(f"Processed: {doc['metadata']['title']}")
        print(f"Content length: {len(doc['content'])} characters")
        print("-" * 50)

if __name__ == "__main__":
    test_processor()
