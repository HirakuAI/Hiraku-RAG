"""
Author:         Min Thu Khaing
Date:           December 15, 2024
Description:    RAG system basic implementation with document 
                processing and vector storage.
"""

import os
import torch
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Document processing
import fitz
import chardet
from bs4 import BeautifulSoup
import pandas as pd

# Vector database
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from document_processor import DocumentProcessor


class DatabaseManager:
    def __init__(self, db_path: str = "private/rag.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for metadata"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Create tables
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
        conn.close()

    def add_document(self, doc_id: str, filepath: str, file_type: str):
        """Add document metadata"""
        conn = sqlite3.connect(self.db_path)
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
        conn.close()

    def add_chunk(self, chunk_id: str, doc_id: str, content: str, chunk_index: int):
        """Add chunk metadata"""
        conn = sqlite3.connect(self.db_path)
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
        conn.close()


class VectorStoreManager:
    def __init__(self, persist_directory: str = "private/vectordb"):
        # Initialize ChromaDB with GPU acceleration
        self.client = chromadb.Client(
            Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False,
                is_persistent=True,
            )
        )

        # Use all-MiniLM-L6-v2 for embeddings
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
        """Add texts to vector store"""
        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)

    def similarity_search(self, query: str, k: int = 3):
        """Search for similar texts"""
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        return results


# HirakuRAG class
class HirakuRAG:
    def __init__(
        self,
        model_name: str = "microsoft/phi-2",
        db_path: str = "private/rag.db",
        vector_dir: str = "private/vectordb",
    ):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        # Initialize document processor
        self.doc_processor = DocumentProcessor(
            num_workers=4,
            exclude_hidden=True,
            required_exts=[".txt", ".pdf", ".md", ".json", ".csv"],
        )

        # Initialize databases
        self.db_manager = DatabaseManager(db_path)
        self.vector_store = VectorStoreManager(vector_dir)

        # Initialize model
        print(f"Loading model {model_name}...")
        model_kwargs = {
            "device_map": "auto",
            "torch_dtype": torch.float16,
            "low_cpu_mem_usage": True,
        }

        self.model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.config.pad_token_id = self.tokenizer.eos_token_id

        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.1,
            top_p=0.95,
            repetition_penalty=1.1,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            device_map="auto",
            truncation=True,
        )
        print("Model loaded successfully!")

    def add_documents(self, file_paths: List[str]):
        """Add multiple documents using DocumentProcessor"""
        # Create documents directory if it doesn't exist
        docs_dir = Path("private/uploads")
        docs_dir.mkdir(exist_ok=True)

        # Process each file
        for file_path in file_paths:
            try:
                # Copy file to documents directory if not already there
                target_path = docs_dir / Path(file_path).name
                if not target_path.exists():
                    import shutil

                    shutil.copy2(file_path, target_path)

                # Process the document
                processed_docs = self.doc_processor.process_directory(
                    str(target_path.parent), recursive=False
                )

                # Store each processed document
                for doc in processed_docs:
                    if doc["metadata"]["processing_status"] == "success":
                        # Generate document ID
                        doc_id = doc["metadata"]["doc_id"]

                        # Store document metadata
                        self.db_manager.add_document(
                            doc_id=doc_id,
                            filepath=doc["metadata"]["file_path"],
                            file_type=doc["metadata"]["file_type"],
                        )

                        # Store chunks
                        chunk_ids = []
                        chunk_texts = []
                        chunk_metadatas = []

                        for i, chunk in enumerate(doc["chunks"]):
                            chunk_id = f"{doc_id}_chunk_{i}"
                            chunk_ids.append(chunk_id)
                            chunk_texts.append(chunk)
                            chunk_metadatas.append(
                                {
                                    "document_id": doc_id,
                                    "chunk_index": i,
                                    "source": doc["metadata"]["file_path"],
                                }
                            )

                            # Store chunk metadata
                            self.db_manager.add_chunk(chunk_id, doc_id, chunk, i)

                        # Add to vector store
                        self.vector_store.add_texts(
                            chunk_texts, chunk_metadatas, chunk_ids
                        )
                        print(f"Added {len(doc['chunks'])} chunks from {file_path}")
                    else:
                        print(
                            f"Failed to process {file_path}: {doc['metadata'].get('error_message', 'Unknown error')}"
                        )

            except Exception as e:
                logging.error(f"Error adding document {file_path}: {e}")
                print(f"Failed to add {file_path}: {str(e)}")

    def query(self, question: str) -> Dict[str, Any]:
        """Query the system"""
        try:
            # Search vector store
            results = self.vector_store.similarity_search(question)
            if not results["documents"]:
                return {"answer": "No relevant information found.", "sources": []}

            # Prepare context
            context = "\n".join(results["documents"][0])

            # Generate response
            prompt = f"""Based only on the following context, answer the question. If you cannot find the exact information in the context, say "I don't have enough information to answer that."

Context: {context}

Question: {question}

Give a precise, factual answer using only the information provided above.

Answer: """

            with torch.inference_mode():
                response = self.pipe(
                    prompt,
                    max_new_tokens=512,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    truncation=True,
                    do_sample=True,
                )[0]["generated_text"]

            # Extract answer
            answer = response.split("Answer:")[-1].strip()

            # Prepare sources
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

            torch.cuda.empty_cache()
            return {"answer": answer, "sources": sources}

        except Exception as e:
            logging.error(f"Error processing query: {e}")
            torch.cuda.empty_cache()
            return {
                "answer": "Error processing your query. Please try again.",
                "error": str(e),
            }


def main():
    # Test functionality
    rag = HirakuRAG()

    # Test document addition
    test_file = "data/sample/test.txt"
    if os.path.exists(test_file):
        rag.add_documents([test_file])

    # Test query
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


if __name__ == "__main__":
    main()

# 365, party girl (Bumpin' that) #brat