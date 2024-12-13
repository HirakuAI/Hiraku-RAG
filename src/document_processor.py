import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import magic
import json
from datetime import datetime
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.readers.base import BaseReader
from llama_index.core.node_parser import SimpleNodeParser

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
    Enhanced document processor using LlamaIndex's SimpleDirectoryReader with extended capabilities.
    Handles multiple file formats and provides detailed metadata extraction.
    """
    
    def __init__(
        self,
        num_workers: int = 4,
        exclude_hidden: bool = True,
        required_exts: Optional[List[str]] = None
    ):
        """
        Initialize the document processor.
        
        Args:
            num_workers: Number of workers for parallel processing
            exclude_hidden: Whether to exclude hidden files
            required_exts: List of file extensions to process (e.g., ['.pdf', '.txt'])
        """
        self.num_workers = num_workers
        self.exclude_hidden = exclude_hidden
        self.required_exts = required_exts
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize node parser for text chunking
        self.node_parser = SimpleNodeParser.from_defaults(
            chunk_size=1024,
            chunk_overlap=200
        )
        
        # Custom file extractors for formats needing special handling
        self.file_extractors = {
            ".json": CustomJSONReader()
        }

    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file metadata
        """
        path = Path(file_path)
        stats = path.stat()
        
        try:
            mime_type = magic.from_file(file_path, mime=True)
        except Exception as e:
            self.logger.warning(f"Could not detect MIME type for {file_path}: {e}")
            mime_type = "unknown"

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
        
        # Check for hidden files
        if self.exclude_hidden and path.name.startswith('.'):
            return False
            
        # Check file extension if required
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

    def process_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Process a single file and return its content and metadata.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Dictionary containing processed content and metadata
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if not self._should_process_file(file_path):
                self.logger.info(f"Skipping file {file_path} based on configuration")
                return None

            reader = SimpleDirectoryReader(
                input_files=[str(path)],
                file_extractor=self.file_extractors,
                file_metadata=self._extract_metadata,
                filename_as_id=True
            )
            
            documents = reader.load_data()
            if not documents:
                return None
                
            doc = documents[0]  # Single file processing
            nodes = self.node_parser.get_nodes_from_documents([doc])
            
            return {
                'content': doc.text,
                'chunks': [node.text for node in nodes],
                'metadata': {
                    **doc.extra_info,
                    'doc_id': doc.doc_id,
                    'num_chunks': len(nodes),
                    'processing_status': 'success'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            return {
                'content': '',
                'chunks': [],
                'metadata': {
                    'file_path': file_path,
                    'processing_status': 'error',
                    'error_message': str(e)
                }
            }

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        # Default formats supported by SimpleDirectoryReader
        default_formats = [
            '.txt', '.pdf', '.csv', '.md', '.markdown', 
            '.docx', '.doc', '.pptx', '.ppt',
            '.jpg', '.jpeg', '.png', '.epub'
        ]
        
        # Add custom formats
        custom_formats = list(self.file_extractors.keys())
        
        return sorted(default_formats + custom_formats)
