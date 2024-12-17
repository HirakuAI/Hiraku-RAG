"""
Document Processor Module

A module for processing various document types using LlamaIndex.

██╗  ██╗██╗██████╗  █████╗ ██╗  ██╗██╗   ██╗    
██║  ██║██║██╔══██╗██╔══██╗██║ ██╔╝██║   ██║    
███████║██║██████╔╝███████║█████╔╝ ██║   ██║    
██╔══██║██║██╔══██╗██╔══██║██╔═██╗ ██║   ██║    
██║  ██║██║██║  ██║██║  ██║██║  ██╗╚██████╔╝    
╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝     

Author: Yiyuan Li
Date: December 15, 2024
Description: Document processor implementation
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.readers.base import BaseReader
from llama_index.core.node_parser import SimpleNodeParser
import mimetypes

class CustomJSONReader(BaseReader):
    """Custom reader for JSON files with structured output."""
    def load_data(self, file: str, extra_info: Optional[Dict] = None) -> List[Document]:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            content = json.dumps(data, indent=2)
            metadata = extra_info or {}
            metadata.update({
                'json_keys': list(data.keys()) if isinstance(data, dict) else None,
                'json_length': len(data) if isinstance(data, (dict, list)) else None
            })
            return [Document(text=content, extra_info=metadata)]

class DocumentProcessor:
    """
    Document processor focusing on text-based formats using LlamaIndex's SimpleDirectoryReader.
    Handles common document types like PDFs, text files, and structured data.
    """

    def __init__(
        self,
        num_workers: int = 4,
        exclude_hidden: bool = True,
        required_exts: Optional[List[str]] = None
    ):
        # Initialize basic configuration
        self.num_workers = num_workers
        self.exclude_hidden = exclude_hidden
        # Default to common text-based formats if none specified
        self.required_exts = required_exts or ['.txt', '.pdf', '.md', '.json', '.csv']

        # Setup logging for tracking processing status
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize node parser for text chunking
        self.node_parser = SimpleNodeParser.from_defaults(
            chunk_size=1024,
            chunk_overlap=200
        )

        # Setup custom handlers for specific file types
        self.file_extractors = {
            ".json": CustomJSONReader()
        }

        # Initialize MIME type detection
        mimetypes.init()

    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract basic metadata from file, focusing on essential information.

        Args:
            file_path: Path to the file
        Returns:
            Dictionary containing file metadata
        """
        path = Path(file_path)
        stats = path.stat()

        # Get basic MIME type information
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

        return {
            "file_path": str(path.absolute()),
            "file_type": mime_type,
            "title": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": stats.st_size,
            "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "processed_at": datetime.now().isoformat()
        }

    def _should_process_file(self, file_path: str) -> bool:
        """
        Determine if a file should be processed based on configuration.

        Args:
            file_path: Path to the file
        Returns:
            Boolean indicating whether to process the file
        """
        path = Path(file_path)

        # Skip hidden files if configured
        if self.exclude_hidden and path.name.startswith('.'):
            return False

        # Check if file extension is in allowed list
        if self.required_exts:
            return path.suffix.lower() in self.required_exts

        return True

    def process_directory(
        self,
        directory_path: str,
        exclude_patterns: Optional[List[str]] = None,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process all supported files in a directory.

        Args:
            directory_path: Path to the directory containing documents
            exclude_patterns: List of glob patterns to exclude
            recursive: Whether to process subdirectories

        Returns:
            List of processed documents with their content and metadata
        """
        try:
            directory = Path(directory_path)
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")

            # Initialize the directory reader with our configuration
            reader = SimpleDirectoryReader(
                input_dir=str(directory),
                recursive=recursive,
                exclude_hidden=self.exclude_hidden,
                required_exts=self.required_exts,
                exclude=exclude_patterns,
                file_extractor=self.file_extractors,
                file_metadata=self._extract_metadata,
                filename_as_id=True
            )

            # Load and process documents
            self.logger.info(f"Processing directory: {directory_path}")
            documents = reader.load_data(num_workers=self.num_workers)

            # Process each document
            processed_documents = []
            for doc in documents:
                try:
                    # Create nodes (chunks) from the document
                    nodes = self.node_parser.get_nodes_from_documents([doc])

                    # Create processed document with enhanced metadata
                    processed_doc = {
                        'content': doc.text,
                        'chunks': [node.text for node in nodes],
                        'metadata': {
                            **doc.extra_info,
                            'doc_id': doc.doc_id,
                            'num_chunks': len(nodes),
                            'processing_status': 'success'
                        }
                    }
                    processed_documents.append(processed_doc)

                except Exception as e:
                    self.logger.error(f"Error processing document {doc.doc_id}: {str(e)}")
                    # Include failed document with error information
                    processed_documents.append({
                        'content': doc.text,
                        'chunks': [],
                        'metadata': {
                            **doc.extra_info,
                            'doc_id': doc.doc_id,
                            'processing_status': 'error',
                            'error_message': str(e)
                        }
                    })

            return processed_documents

        except Exception as e:
            self.logger.error(f"Error processing directory {directory_path}: {str(e)}")
            raise

    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a single file.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            List of processed documents with their content and metadata
        """
        try:
            if not self._should_process_file(file_path):
                return []

            # Use SimpleDirectoryReader to process single file
            reader = SimpleDirectoryReader(
                input_files=[file_path],
                exclude_hidden=self.exclude_hidden,
                file_extractor=self.file_extractors,
                file_metadata=self._extract_metadata,
                filename_as_id=True
            )

            # Load and process document
            documents = reader.load_data()
            
            # Process each document
            processed_documents = []
            for doc in documents:
                try:
                    # Create nodes (chunks) from the document
                    nodes = self.node_parser.get_nodes_from_documents([doc])

                    # Create processed document with enhanced metadata
                    processed_doc = {
                        'content': doc.text,
                        'chunks': [node.text for node in nodes],
                        'metadata': {
                            **doc.extra_info,
                            'doc_id': doc.doc_id,
                            'num_chunks': len(nodes),
                            'processing_status': 'success'
                        }
                    }
                    processed_documents.append(processed_doc)

                except Exception as e:
                    self.logger.error(f"Error processing document {doc.doc_id}: {str(e)}")
                    processed_documents.append({
                        'content': doc.text,
                        'chunks': [],
                        'metadata': {
                            **doc.extra_info,
                            'doc_id': doc.doc_id,
                            'processing_status': 'error',
                            'error_message': str(e)
                        }
                    })

            return processed_documents

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            raise
