"""
database.py:    SQLite database management for document metadata.

Author:         Min Thu Khaing
Date:           December 15, 2024
Description:    Handles SQLite database operations for document 
                and chunk metadata.
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles SQLite database operations for document and chunk metadata."""

    def __init__(self, db_path: str = "private/rag.db"):
        """
        Initialize database manager and create necessary tables.

        Args:
            db_path: Path to SQLite database file
        """
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()

            # Create documents table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filepath TEXT,
                    filename TEXT,
                    file_type TEXT,
                    created_at TIMESTAMP,
                    last_updated TIMESTAMP
                )
            """
            )

            # Create chunks table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT,
                    content TEXT,
                    chunk_index INTEGER,
                    created_at TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            """
            )
            conn.commit()

    def add_document(self, doc_id: str, filepath: str, file_type: str):
        """
        Add document metadata to the database.

        Args:
            doc_id: Unique identifier for the document
            filepath: Path to the document file
            file_type: MIME type of the document
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    """
                    INSERT OR REPLACE INTO documents 
                    (id, filepath, filename, file_type, created_at, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        doc_id,
                        filepath,
                        Path(filepath).name,
                        file_type,
                        datetime.now(),
                        datetime.now(),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error adding document to database: {e}")
            raise

    def add_chunk(self, chunk_id: str, doc_id: str, content: str, chunk_index: int):
        """
        Add chunk metadata to the database.

        Args:
            chunk_id: Unique identifier for the chunk
            doc_id: ID of the parent document
            content: Text content of the chunk
            chunk_index: Index of the chunk within the document
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO chunks 
                    (id, document_id, content, chunk_index, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (chunk_id, doc_id, content, chunk_index, datetime.now()),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error adding chunk to database: {e}")
            raise

    def get_document_metadata(self, doc_id: str) -> Optional[Dict]:
        """
        Retrieve document metadata by ID.

        Args:
            doc_id: Document identifier

        Returns:
            Dictionary containing document metadata or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
                row = c.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "filepath": row[1],
                        "filename": row[2],
                        "file_type": row[3],
                        "created_at": row[4],
                        "last_updated": row[5],
                    }
                return None
        except Exception as e:
            logger.error(f"Error retrieving document metadata: {e}")
            raise

    def get_chunk_metadata(self, chunk_id: str) -> Optional[Dict]:
        """
        Retrieve chunk metadata by ID.

        Args:
            chunk_id: Chunk identifier

        Returns:
            Dictionary containing chunk metadata or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,))
                row = c.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "document_id": row[1],
                        "content": row[2],
                        "chunk_index": row[3],
                        "created_at": row[4],
                    }
                return None
        except Exception as e:
            logger.error(f"Error retrieving chunk metadata: {e}")
            raise

    def list_documents(self) -> List[Dict]:
        """
        List all documents in the database.

        Returns:
            List of dictionaries containing document metadata
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM documents ORDER BY created_at DESC")
                return [
                    {
                        "id": row[0],
                        "filepath": row[1],
                        "filename": row[2],
                        "file_type": row[3],
                        "created_at": row[4],
                        "last_updated": row[5],
                    }
                    for row in c.fetchall()
                ]
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise

    def reset(self):
        """Reset the database by dropping and recreating all tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("DROP TABLE IF EXISTS chunks")
                c.execute("DROP TABLE IF EXISTS documents")
                conn.commit()
            self.init_database()
            logger.info("Database reset successfully")
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            raise

    def get_document_by_path(self, filepath: str) -> Optional[Dict]:
        """
        Get document metadata by filepath.
        
        Args:
            filepath: Path to the document file
        
        Returns:
            Dictionary containing document metadata or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM documents WHERE filepath = ?", (filepath,))
                row = c.fetchone()
                if row:
                    return {
                        "doc_id": row[0],
                        "filepath": row[1],
                        "filename": row[2],
                        "file_type": row[3],
                        "created_at": row[4],
                        "last_updated": row[5],
                    }
                return None
        except Exception as e:
            logger.error(f"Error retrieving document by path: {e}")
            raise
