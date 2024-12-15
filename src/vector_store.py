"""
vector_store.py:    Vector store management using ChromaDB.

Author:             Min Thu Khaing
Date:               December 15, 2024
Description:        Manages vector storage and retrieval operations
                    using ChromaDB.
"""

import os
import torch
import logging
from typing import List, Dict

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages vector storage and retrieval using ChromaDB."""

    def __init__(self, persist_directory: str = "private/vectordb"):
        """Initialize vector store with ChromaDB."""
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.Client(
            Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False,
                is_persistent=True,
            )
        )

        # Initialize embedding function
        self.embedding_function = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cuda" if torch.cuda.is_available() else "cpu",
            )
        )

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="document_store",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def add_texts(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """
        Add texts with metadata to vector store.

        Args:
            texts: List of text content to add
            metadatas: List of metadata dictionaries for each text
            ids: List of unique identifiers for each text
        """
        try:
            self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {e}")
            raise

    def similarity_search(self, query: str, k: int = 3) -> Dict:
        """
        Search for similar texts in vector store.

        Args:
            query: Text to search for
            k: Number of results to return

        Returns:
            Dictionary containing search results
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                include=["documents", "metadatas", "distances"],
            )
            return results
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            raise

    @property
    def has_documents(self) -> bool:
        """Check if vector store has documents."""
        return len(self.collection.get()["ids"]) > 0

    def reset(self):
        """Reset the vector store by deleting all documents."""
        try:
            self.collection.delete(ids=self.collection.get()["ids"])
            logger.info("Vector store reset successfully")
        except Exception as e:
            logger.error(f"Error resetting vector store: {e}")
            raise
