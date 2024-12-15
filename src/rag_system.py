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

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from document_processor import DocumentProcessor
from database import DatabaseManager
from vector_store import VectorStoreManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HirakuRAG:
    """Main RAG system implementation."""

    def __init__(
        self,
        model_name: str = "microsoft/phi-2",
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

        # Initialize model
        logger.info(f"Loading model {model_name}...")
        try:
            model_kwargs = {
                "device_map": "auto",
                "torch_dtype": torch.float16,
                "low_cpu_mem_usage": True,
            }

            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, **model_kwargs
            )
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
            logger.info("Model loaded successfully!")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def add_documents(self, file_paths: List[str]):
        """Process and add documents to the system."""
        docs_dir = Path("private/uploads")
        docs_dir.mkdir(exist_ok=True)

        total_chunks = 0
        successful_files = 0

        for file_path in file_paths:
            try:
                # Copy file to uploads directory
                target_path = docs_dir / Path(file_path).name
                if not target_path.exists():
                    import shutil

                    shutil.copy2(file_path, target_path)

                # Process document
                processed_docs = self.doc_processor.process_directory(
                    str(target_path.parent), recursive=False
                )

                # Handle each processed document
                for doc in processed_docs:
                    if doc["metadata"]["processing_status"] == "success":
                        doc_id = doc["metadata"]["doc_id"]

                        # Store document metadata
                        self.db_manager.add_document(
                            doc_id=doc_id,
                            filepath=doc["metadata"]["file_path"],
                            file_type=doc["metadata"]["file_type"],
                        )

                        # Prepare chunks
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

                        # Add chunks to vector store
                        self.vector_store.add_texts(
                            chunk_texts, chunk_metadatas, chunk_ids
                        )

                        total_chunks += len(doc["chunks"])
                        successful_files += 1
                        logger.info(
                            f"Added {len(doc['chunks'])} chunks from {file_path}"
                        )
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
        """
        Query the system with a question.

        Args:
            question: Question to be answered
            k: Number of similar documents to retrieve

        Returns:
            Dictionary containing answer and source information
        """
        try:
            # Perform similarity search
            results = self.vector_store.similarity_search(question, k)
            if not results["documents"]:
                return {"answer": "No relevant information found.", "sources": []}

            # Prepare context from retrieved documents
            context = "\n".join(results["documents"][0])

            # Generate prompt
            prompt = f"""Based only on the following context, answer the question. If you cannot find the exact information in the context, say "I don't have enough information to answer that."

Context: {context}

Question: {question}

Give a precise, factual answer using only the information provided above.

Answer: """

            # Generate response
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

            # Prepare sources with metadata
            sources = [
                {
                    "content": doc[:200] + "..." if len(doc) > 200 else doc,
                    "source": meta.get("source", "Unknown"),
                    "similarity": 1 - dist,
                    "metadata": self.db_manager.get_document_metadata(
                        meta.get("document_id", "")
                    ),
                }
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ]

            return {"answer": answer, "sources": sources}

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "answer": "Error processing your query. Please try again.",
                "error": str(e),
            }
        finally:
            # Clean up CUDA memory
            torch.cuda.empty_cache()

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
    # Initialize RAG system
    rag = HirakuRAG()

    # Test document addition
    test_file = "data/sample/test.txt"
    if os.path.exists(test_file):
        rag.add_documents([test_file])

    # Interactive query loop
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
