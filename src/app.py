"""
app.py          flask app for RAG system

Author:         Min Thu Khaing
Date:           December 15, 2024
Description:    Flask API for RAG system.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_system import HirakuRAG
import os
import logging

app = Flask(__name__)
CORS(app)
rag = None
_initialized = False

# logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def init_rag():
    """Initialize the RAG system and load documents"""
    global rag, _initialized

    if _initialized:
        return

    try:
        os.makedirs("private/uploads", exist_ok=True)
        os.makedirs("private/vectordb", exist_ok=True)

        if rag is None:
            rag = HirakuRAG()

            if not rag.vector_store_has_documents:
                docs_dir = "private/uploads"
                if os.path.exists(docs_dir):
                    files = set()  # Use set to prevent duplicates
                    for root, _, filenames in os.walk(docs_dir):
                        for filename in filenames:
                            ext = os.path.splitext(filename)[1].lower()
                            if ext in {".pdf", ".txt", ".csv", ".doc", ".docx"}:
                                files.add(os.path.join(root, filename))
                    if files:
                        rag.add_documents(list(files))
                        logging.info(f"Loaded {len(files)} existing documents")

        _initialized = True

    except Exception as e:
        logging.error(f"Error initializing RAG system: {str(e)}")
        raise

@app.route("/api/query", methods=["POST"])
def query():
    """Handle query requests"""
    try:
        data = request.json
        question = data.get("question", "")

        if not question:
            return jsonify({"error": "No question provided"}), 400

        global rag
        if rag is None:
            init_rag()

        if not rag.vector_store_has_documents:
            return jsonify(
                {"answer": "Please upload some documents first.", "sources": []}
            )

        response = rag.query(question)

        if not response or "answer" not in response:
            raise ValueError("Invalid response from RAG system")

        return jsonify(
            {"answer": response["answer"], "sources": response.get("sources", [])}
        )

    except Exception as e:
        logging.error(f"Query error: {str(e)}")
        return jsonify({"error": "Failed to process query. Please try again."}), 500

@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle file uploads"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        os.makedirs("private/uploads", exist_ok=True)

        filepath = os.path.join("private/uploads", file.filename)

        if os.path.exists(filepath):
            logging.info(f"File {file.filename} already exists, skipping upload")
            return jsonify({"message": "File already processed"})

        file.save(filepath)

        global rag
        if rag is None:
            init_rag()

        rag.add_documents([filepath])
        logging.info(f"Successfully uploaded and processed: {file.filename}")

        return jsonify({"message": "File uploaded successfully"})

    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_rag()

    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug_mode, port=1512, use_reloader=False)
