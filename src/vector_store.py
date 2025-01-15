"""
vector_store.py:    Vector store management using ChromaDB.

Author:             Min Thu Khaing
Date:               December 15, 2024
Description:        Manages vector storage and retrieval operations
                    using ChromaDB.
"""

import os
import logging
from typing import List, Dict

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import ollama
from chromadb import Documents, EmbeddingFunction, Embeddings

logger = logging.getLogger(__name__)


class OllamaEmbeddingFunction:
    """Embedding function using Ollama's nomic-embed-text model."""

    def __init__(self, model_name: str = "nomic-embed-text"):
        """Initialize with Ollama client."""
        self.client = ollama.Client(host="http://localhost:11434")
        self.model_name = model_name

        # Test if model exists and pull if needed
        try:
            self.client.show(self.model_name)
        except ollama.ResponseError as e:
            if e.status_code == 404:
                logger.info(f"Model {model_name} not found. Pulling model...")
                self.client.pull(model_name)
                logger.info(f"Successfully pulled model {model_name}")
            else:
                raise

    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for input texts.

        Args:
            input: Single string or list of strings to embed

        Returns:
            List of embeddings, one per input text
        """
        if isinstance(input, str):
            input = [input]

        try:
            embeddings = []
            for text in input:
                response = self.client.embeddings(model=self.model_name, prompt=text)
                embeddings.append(response["embedding"])
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise


class VectorStoreManager:
    """Manages vector storage and retrieval using ChromaDB."""

    def __init__(self, persist_directory: str, username: str):
        """Initialize vector store with ChromaDB."""
        if not username:
            raise ValueError(
                "Username is required for VectorStoreManager initialization"
            )

        os.makedirs(persist_directory, exist_ok=True)
        self.persist_directory = persist_directory
        self.username = username

        self.client = chromadb.Client(
            Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False,
                is_persistent=True,
            )
        )

        self.embedding_function = OllamaEmbeddingFunction()

        # Create or get user-specific collection
        self.collection = self.client.get_or_create_collection(
            name=f"{username}_documents",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine", "username": username},
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

    def has_document(self, doc_id: str) -> bool:
        """Check if a document exists in the vector store."""
        try:
            result = self.collection.get(ids=[doc_id])
            return len(result["ids"]) > 0
        except Exception:
            return False
