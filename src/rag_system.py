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

    def __init__(self, model_name: str = "llama3.2", username: str = None):
        """Initialize RAG system components."""
        if not username:
            raise ValueError("Username is required for initialization")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        # Setup user-specific paths
        self.user_dir = os.path.join("private", username)
        self.db_path = os.path.join(self.user_dir, "rag.db")
        self.vector_dir = os.path.join(self.user_dir, "vectordb")
        self.uploads_dir = os.path.join(self.user_dir, "uploads")

        # Create user directories
        os.makedirs(self.user_dir, exist_ok=True)
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.vector_dir, exist_ok=True)

        # Initialize components
        self.doc_processor = DocumentProcessor(
            num_workers=4,
            exclude_hidden=True,
            required_exts=[".txt", ".pdf", ".md", ".json", ".csv"],
        )
        self.db_manager = DatabaseManager(self.db_path)
        self.vector_store = VectorStoreManager(self.vector_dir, username)

        # Initialize Ollama client
        self.model_name = model_name
        self.client = ollama.Client(host="http://localhost:11434")

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

        self.precision_mode = "interactive"  # Changed default to interactive mode

    def set_precision_mode(self, mode: str):
        """Set the precision mode for responses."""
        valid_modes = {"accurate", "interactive", "flexible"}
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {valid_modes}")
        self.precision_mode = mode
        logger.info(f"Precision mode set to: {mode}")

    def add_documents(self, file_paths: List[str]):
        """Process and add documents to the system."""
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

                # Copy to user uploads directory if needed
                target_path = Path(self.uploads_dir) / Path(file_path).name
                if not target_path.exists():
                    import shutil

                    shutil.copy2(file_path, target_path)

                # Check if already processed
                existing_doc = self.db_manager.get_document_by_path(str(target_path))
                if existing_doc and self.vector_store.has_document(existing_doc["id"]):
                    logger.info(f"Document already processed: {target_path}")
                    continue

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
                            existing_chunk = self.db_manager.get_chunk_metadata(
                                chunk_id
                            )
                            if existing_chunk:
                                logger.warning(
                                    f"Chunk {chunk_id} already exists, skipping"
                                )
                                continue

                            # Try to add chunk to database first
                            try:
                                self.db_manager.add_chunk(chunk_id, doc_id, chunk, i)
                                # Only add to vectors if database insertion succeeded
                                chunk_ids.append(chunk_id)
                                chunk_texts.append(chunk)
                                chunk_metadatas.append(
                                    {
                                        "document_id": doc_id,
                                        "chunk_index": i,
                                        "source": doc["metadata"]["file_path"],
                                    }
                                )
                            except sqlite3.IntegrityError:
                                logger.warning(
                                    f"Chunk {chunk_id} already exists, skipping"
                                )
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
                                    metadatas=chunk_metadatas,
                                )
                                total_chunks += len(chunk_texts)
                                logger.info(
                                    f"Added {len(chunk_texts)} chunks from {target_path}"
                                )
                            except Exception as e:
                                logger.error(
                                    f"Error adding chunks to vector store: {e}"
                                )

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

    def query(
        self, question: str, history: List[Dict[str, str]] = None, k: int = 3
    ) -> Dict[str, Any]:
        """Query the system with a question and optional conversation history."""

        try:
            normalized_question = question.lower().strip().rstrip("?!.,")

            casual_greetings = {
                "hi",
                "hello",
                "hey",
                "how are you",
                "how's it going",
                "what's up",
                "good morning",
                "good afternoon",
                "good evening",
                "hi there",
                "hello there",
                "how are you doing",
                "how do you do",
                "how are things",
                "how's everything",
            }

            is_greeting = any(
                greeting in normalized_question for greeting in casual_greetings
            )

            if is_greeting:
                flexible_response = None
                if self.precision_mode == "flexible":
                    response = self.client.chat(
                        model=self.model_name,
                        messages=[
                            {
                                "role": "system",
                                "content": """You are Hiraku, a friendly and knowledgeable AI assistant. 
                            When responding to greetings:
                            1. Be natural and conversational
                            2. Vary your responses rather than using templates
                            3. Match the user's level of formality
                            4. Keep responses concise but warm
                            5. Mention that you're ready to help
                            6. Don't use bullet points or structured formats
                            7. Don't mention specific capabilities unless asked""",
                            },
                            {"role": "user", "content": question},
                        ],
                        stream=False,
                        options={
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "top_k": 40,
                            "num_ctx": 4096,
                        },
                    )
                    flexible_response = (
                        f"[AI Knowledge: {response.message.content.strip()}]"
                    )

                greeting_responses = {
                    "accurate": "Hi, Im Hiraku, I can answer question base on the file you provided. But Im in Accurate mode now so I should only respond based on documents, but I don't see any greeting-related content. Would you like to ask something about the documents?",
                    "interactive": "Hello! [AI Knowledge: I'm here to help you! While I don't see any greetings in the documents, I can still chat with you.] What would you like to know about?",
                    "flexible": flexible_response,
                }

                return {
                    "answer": greeting_responses[self.precision_mode],
                    "sources": [],
                }

            # For non-greeting queries, perform similarity search
            results = self.vector_store.similarity_search(question, k)
            context = "\n".join(results["documents"][0])

            # Format conversation history
            conversation_context = ""
            if history and len(history) > 0:
                conversation_context = "\nPrevious conversation:\n" + "\n".join(
                    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                    for msg in history
                )

            system_messages = {
                "accurate": """You are Hiraku, a precise AI assistant that ONLY uses provided context. Follow these rules strictly:
                    1. ONLY use information from the given context
                    2. If information isn't in the context, say "I cannot answer this question as the information is not in the provided documents." and suggest user change to other mode
                    3. Do not make assumptions or add external knowledge
                    4. Cite specific sources when referencing information
                    5. Maintain strict accuracy over completeness
                    6. For follow-up questions, consider the previous conversation context""",
                "interactive": """You are Hiraku, a helpful AI assistant that prioritizes accuracy while allowing supplementary knowledge. Follow these guidelines:
                    1. Primarily use information from the provided context
                    2. When adding knowledge beyond the context:
                       - Clearly mark such information with [AI Knowledge: your text]
                    3. Always distinguish between document information and supplementary knowledge
                    4. Consider the previous conversation context for follow-up questions
                    5. If a follow-up question refers to previous topics, maintain consistency with earlier responses
                    6. Maintain transparency about information sources""",
                "flexible": """You are Hiraku, an intellectually curious and knowledgeable AI assistant with knowledge updated as of April 2024. Follow these guidelines:

                    Core Interaction Guidelines:
                    1. First check if the question can be answered using the provided context
                    2. When adding knowledge beyond the context, clearly distinguish between:
                       - Document information
                       - AI knowledge (marked with [AI Knowledge: text])
                       - Time-sensitive information (noting April 2024 knowledge cutoff when relevant)

                    Response Characteristics:
                    3. Be intellectually curious and engage in thoughtful discussion
                    4. Think through problems step-by-step, especially for math or logic questions
                    5. For very long tasks, offer to break them down and get user feedback on each part
                    6. Use markdown for code blocks and offer to explain the code afterward

                    Special Considerations:
                    7. For obscure topics, end with a reminder about potential hallucination
                    8. When citing sources, note that citations should be double-checked
                    9. Handle controversial topics with care and clear information
                    10. For tasks involving various viewpoints, provide assistance regardless of own views

                    Communication Style:
                    11. Be direct - avoid apologizing when declining tasks
                    12. Maintain:
                        - Clear distinction between document content and AI knowledge
                        - Helpful and informative tone
                        - Well-structured responses
                        - Consistency throughout the conversation
                        - Intellectual engagement with user's ideas""",
            }

            messages = [
                {"role": "system", "content": system_messages[self.precision_mode]},
                {
                    "role": "user",
                    "content": f"Context: {context}\n{conversation_context}\n\nCurrent question: {question}",
                },
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
                    "num_ctx": 4096,
                },
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
