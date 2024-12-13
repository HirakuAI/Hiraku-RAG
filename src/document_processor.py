import os
from typing import List, Dict, Any
from llamaparse import LlamaParse
import magic
import pandas as pd

class DocumentProcessor:
    """Handles document ingestion and processing using LlamaParse."""

    def __init__(self, parse_config: Dict[str, Any] = None):
        self.parser = LlamaParse()
        self.supported_formats = {
            'application/pdf': self._process_pdf,
            'text/plain': self._process_text,
            'text/csv': self._process_csv,
            'image/jpeg': self._process_image,
            'image/png': self._process_image
        }

    def process_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """Process all supported files in a directory."""
        processed_documents = []

        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path):
                    doc = self.process_file(file_path)
                    if doc:
                        processed_documents.append(doc)
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

        return processed_documents

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single file and return its content and metadata."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Detect file type using python-magic
        file_type = magic.from_file(file_path, mime=True)

        if file_type in self.supported_formats:
            processor = self.supported_formats[file_type]
            return processor(file_path)
        else:
            print(f"Unsupported file type: {file_type} for file: {file_path}")
            return None

    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process PDF files using LlamaParse."""
        parsed_content = self.parser.parse_file(file_path)
        return {
            'content': parsed_content.text,
            'metadata': {
                'file_path': file_path,
                'file_type': 'pdf',
                'title': os.path.basename(file_path)
            }
        }

    def _process_text(self, file_path: str) -> Dict[str, Any]:
        """Process text files."""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return {
            'content': content,
            'metadata': {
                'file_path': file_path,
                'file_type': 'text',
                'title': os.path.basename(file_path)
            }
        }

    def _process_csv(self, file_path: str) -> Dict[str, Any]:
        """Process CSV files."""
        df = pd.read_csv(file_path)
        content = df.to_string()
        return {
            'content': content,
            'metadata': {
                'file_path': file_path,
                'file_type': 'csv',
                'title': os.path.basename(file_path),
                'rows': len(df),
                'columns': list(df.columns)
            }
        }

    def _process_image(self, file_path: str) -> Dict[str, Any]:
        """Process images using LlamaParse's OCR capabilities."""
        parsed_content = self.parser.parse_file(file_path)
        return {
            'content': parsed_content.text,
            'metadata': {
                'file_path': file_path,
                'file_type': 'image',
                'title': os.path.basename(file_path)
            }
        }
