"""
rag_system.py:  Main RAG system implementation.

Author:         Min Thu Khaing
Date:           December 15, 2024
Description:    Core RAG system implementation integrating document 
                processing, vector storage, and querying capabilities.
"""

import os
import torch
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import sqlite3

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from document_processor import DocumentProcessor
from database import DatabaseManager
from vector_store import VectorStoreManager
import ollama

# logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HirakuRAG:
    """Main RAG system implementation."""

    def __init__(
        self,
        model_name: str = "llama3.2",
        db_path: str = "private/rag.db",
        vector_dir: str = "private/vectordb",
    ):
        """Initialize RAG system components."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        # Initialize components
        self.doc_processor = DocumentProcessor(
            num_workers=4,
            exclude_hidden=True,
            required_exts=[".txt", ".pdf", ".md", ".json", ".csv"],
        )
        self.db_manager = DatabaseManager(db_path)
        self.vector_store = VectorStoreManager(vector_dir)

        # Initialize Ollama client
        self.model_name = model_name
        self.client = ollama.Client(host='http://localhost:11434')

        try:
            # Test if model exists
            self.client.show(model_name)
            logger.info(f"Model {model_name} is available")
        except ollama.ResponseError as e:
            if e.status_code == 404:
                logger.info(f"Model {model_name} not found. Pulling model...")
                self.client.pull(model_name)
                logger.info(f"Successfully pulled model {model_name}")
            else:
                raise

    def add_documents(self, file_paths: List[str]):
        """Process and add documents to the system."""
        docs_dir = Path("private/uploads")
        docs_dir.mkdir(exist_ok=True)

        total_chunks = 0
        successful_files = 0
        processed_paths = set()

        for file_path in file_paths:
            try:
                file_path = str(Path(file_path).resolve())
                if file_path in processed_paths:
                    logger.info(f"Skipping already processed file: {file_path}")
                    continue
                processed_paths.add(file_path)

                target_path = docs_dir / Path(file_path).name

                existing_doc = self.db_manager.get_document_by_path(str(target_path))
                if existing_doc and self.vector_store.has_document(existing_doc["id"]):
                    logger.info(f"Document {target_path} already exists in both database and vector store, skipping")
                    continue

                if not target_path.exists():
                    import shutil
                    shutil.copy2(file_path, target_path)

                # Process single file
                processed_docs = self.doc_processor.process_file(str(target_path))

                for doc in processed_docs:
                    if Path(doc["metadata"]["file_path"]).name != target_path.name:
                        continue

                    if doc["metadata"]["processing_status"] == "success":
                        doc_id = doc["metadata"]["doc_id"]

                        # Store document metadata
                        self.db_manager.add_document(
                            doc_id=doc_id,
                            filepath=doc["metadata"]["file_path"],
                            file_type=doc["metadata"]["file_type"],
                        )

                        # Prepare chunks for batch addition
                        chunk_ids = []
                        chunk_texts = []
                        chunk_metadatas = []

                        for i, chunk in enumerate(doc["chunks"]):
                            chunk_id = f"{doc_id}_chunk_{i}"

                            # Check if chunk already exists
                            existing_chunk = self.db_manager.get_chunk_metadata(chunk_id)
                            if existing_chunk:
                                logger.warning(f"Chunk {chunk_id} already exists, skipping")
                                continue

                            # Try to add chunk to database first
                            try:
                                self.db_manager.add_chunk(chunk_id, doc_id, chunk, i)
                                # Only add to vectors if database insertion succeeded
                                chunk_ids.append(chunk_id)
                                chunk_texts.append(chunk)
                                chunk_metadatas.append({
                                    "document_id": doc_id,
                                    "chunk_index": i,
                                    "source": doc["metadata"]["file_path"],
                                })
                            except sqlite3.IntegrityError:
                                logger.warning(f"Chunk {chunk_id} already exists, skipping")
                                continue
                            except Exception as e:
                                logger.error(f"Error adding chunk {chunk_id}: {e}")
                                continue

                        # Add chunks to vector store in batch if we have any
                        if chunk_texts:
                            try:
                                self.vector_store.collection.add(
                                    documents=chunk_texts,
                                    ids=chunk_ids,
                                    metadatas=chunk_metadatas
                                )
                                total_chunks += len(chunk_texts)
                                logger.info(f"Added {len(chunk_texts)} chunks from {target_path}")
                            except Exception as e:
                                logger.error(f"Error adding chunks to vector store: {e}")

                        successful_files += 1
                    else:
                        logger.error(
                            f"Failed to process {file_path}: {doc['metadata'].get('error_message', 'Unknown error')}"
                        )

            except Exception as e:
                logger.error(f"Error adding document {file_path}: {e}")

        logger.info(
            f"Successfully processed {successful_files}/{len(file_paths)} files, added {total_chunks} total chunks"
        )

    def query(self, question: str, k: int = 3) -> Dict[str, Any]:
        """Query the system with a question."""
        try:
            # Perform similarity search
            results = self.vector_store.similarity_search(question, k)

            # Prepare context from retrieved documents
            context = "\n".join(results["documents"][0])

            # Generate prompt with better system message
            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful AI assistant powered by Llama 3.2. 
                    Answer questions based only on the provided context. If you cannot find 
                    the exact information in the context, say 'I don't have enough information 
                    to answer that question accurately.' Always cite your sources when possible."""
                },
                {
                    "role": "user",
                    "content": f"Context: {context}\n\nQuestion: {question}\n\nProvide a detailed answer using only the information from the context above."
                }
            ]

            # Generate response using Ollama with streaming
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                stream=False,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_ctx": 4096
                }
            )

            # Extract answer
            answer = response.message.content.strip()

            # Prepare sources with metadata
            sources = [
                {
                    "content": doc[:200] + "..." if len(doc) > 200 else doc,
                    "source": meta.get("source", "Unknown"),
                    "similarity": 1 - dist,
                }
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ]

            return {"answer": answer, "sources": sources}

        except Exception as e:
            logger.error(f"Error in query: {e}")
            return {
                "answer": "An error occurred while processing your query.",
                "sources": [],
            }

    @property
    def vector_store_has_documents(self) -> bool:
        """Check if vector store has documents."""
        return self.vector_store.has_documents

    def reset(self):
        """Reset the entire system by clearing both database and vector store."""
        try:
            self.vector_store.reset()
            self.db_manager.reset()
            logger.info("System reset successfully")
        except Exception as e:
            logger.error(f"Error resetting system: {e}")
            raise


def main():
    """Main function for testing the RAG system."""
    rag = HirakuRAG()

    test_file = "data/sample/test.txt"
    if os.path.exists(test_file):
        rag.add_documents([test_file])

    while True:
        question = input("\nEnter question (or 'quit' to exit): ")
        if question.lower() == "quit":
            break

        response = rag.query(question)
        print("\nAnswer:", response["answer"])

        if response.get("sources"):
            print("\nSources:")
            for i, source in enumerate(response["sources"], 1):
                print(
                    f"\n{i}. From {source['source']} (similarity: {source['similarity']:.2f}):"
                )
                print(source["content"])
                if source.get("metadata"):
                    print("Document metadata:", source["metadata"])


if __name__ == "__main__":
    main()
