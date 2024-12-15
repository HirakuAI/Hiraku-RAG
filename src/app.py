"""
Author:         Min Thu Khaing
Date:           December 15, 2024
Description:    Flask API for RAG system.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_system import HirakuRAG
import os

app = Flask(__name__)
CORS(app)

# Initialize RAG system
rag = None


def init_rag():
    
    if not os.path.exists("private"):
        os.makedirs("private")
            
    global rag
    if rag is None:
        rag = HirakuRAG()
        # Load documents at startup
        docs_dir = "private/uploads"
        if os.path.exists(docs_dir):
            files = []
            for root, _, filenames in os.walk(docs_dir):
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in {".pdf", ".txt", ".csv", ".doc", ".docx"}:
                        files.append(os.path.join(root, filename))
            if files:
                rag.add_documents(files)


@app.route("/api/query", methods=["POST"])
def query():
    try:
        data = request.json
        question = data.get("question", "")

        if not question:
            return jsonify({"error": "No question provided"}), 400

        # Initialize RAG if needed
        global rag
        if rag is None:
            init_rag()

        # Check if documents are loaded
        if not rag.vector_store:
            return jsonify(
                {"answer": "Please upload some documents first.", "sources": []}
            )

        # Process query with timeout
        response = rag.query(question)

        if not response or "answer" not in response:
            raise ValueError("Invalid response from RAG system")

        return jsonify(
            {"answer": response["answer"], "sources": response.get("sources", [])}
        )

    except Exception as e:
        app.logger.error(f"Query error: {str(e)}")
        return jsonify({"error": "Failed to process query. Please try again."}), 500


@app.route("/api/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Save file
        if not os.path.exists("private/uploads"):
            os.makedirs("private/uploads")

        filepath = os.path.join("private/uploads", file.filename)
        file.save(filepath)

        # Add to RAG system
        if rag is None:
            init_rag()
        else:
            rag.add_documents([filepath])

        return jsonify({"message": "File uploaded successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_rag()
    app.run(debug=True, port=5000)
