"""
app.py          flask app for RAG system

Author:         Min Thu Khaing
Date:           December 21, 2024
Description:    Flask API for RAG system with user authentication.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_system import HirakuRAG
from user_management import UserManager
import os
import logging
from functools import wraps

app = Flask(__name__)
CORS(app)
user_manager = None
rag_instances = {}  # Store RAG instances per user
_initialized = False

# logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def init_system():
    """Initialize the system"""
    global user_manager, _initialized

    if _initialized:
        return

    try:
        os.makedirs("private", exist_ok=True)
        if user_manager is None:
            user_manager = UserManager()
        _initialized = True

    except Exception as e:
        logging.error(f"Error initializing system: {str(e)}")
        raise


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "No authentication token provided"}), 401

        token = token.split("Bearer ")[-1]
        user_info = user_manager.verify_token(token)

        if not user_info:
            return jsonify({"error": "Invalid or expired token"}), 401

        return f(user_info, *args, **kwargs)

    return decorated


def get_user_rag(username: str) -> HirakuRAG:
    """Get or create RAG instance for user"""
    if username not in rag_instances:
        rag_instances[username] = HirakuRAG(username=username)
    return rag_instances[username]


@app.route("/api/query", methods=["POST"])
@require_auth
def query(user_info):
    """Handle query requests"""
    try:
        data = request.json
        question = data.get("question", "")
        history = user_manager.get_chat_history(user_info["user_id"])

        if not question:
            return jsonify({"error": "No question provided"}), 400

        # Get user-specific RAG instance
        rag = get_user_rag(user_info["username"])

        response = rag.query(question, history=history)

        # Save chat history
        user_manager.save_chat_message(user_info["user_id"], question, "user")
        user_manager.save_chat_message(
            user_info["user_id"], response["answer"], "assistant"
        )

        return jsonify(response)

    except Exception as e:
        logging.error(f"Query error: {str(e)}")
        return jsonify({"error": "Failed to process query"}), 500


@app.route("/api/upload", methods=["POST"])
@require_auth
def upload_file(user_info):
    """Handle file uploads"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Get user-specific RAG instance
        rag = get_user_rag(user_info["username"])

        # File will be saved to user's upload directory by RAG
        filepath = os.path.join(rag.uploads_dir, file.filename)
        file.save(filepath)

        # Process the document
        rag.add_documents([filepath])

        # Link document to user
        user_manager.link_document_to_user(
            user_info["user_id"], os.path.basename(filepath)
        )

        logging.info(f"Successfully uploaded and processed: {file.filename}")
        return jsonify({"message": "File uploaded successfully"})

    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/set-precision", methods=["POST"])
@require_auth
def set_precision(user_info):
    """Handle precision mode changes"""
    try:
        data = request.json
        mode = data.get("mode")
        if not mode:
            return jsonify({"error": "No mode provided"}), 400

        # Get user-specific RAG instance
        rag = get_user_rag(user_info["username"])
        rag.set_precision_mode(mode)

        return jsonify({"message": f"Precision mode set to {mode}"})

    except Exception as e:
        logging.error(f"Error setting precision mode: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")

        if not all([username, password, email]):
            return jsonify({"error": "Missing required fields"}), 400

        if user_manager.register_user(username, password, email):
            return jsonify({"message": "Registration successful"})
        else:
            return jsonify({"error": "Username or email already exists"}), 409

    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500


@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")

        if not all([username, password]):
            return jsonify({"error": "Missing credentials"}), 400

        token = user_manager.authenticate_user(username, password)
        if token:
            return jsonify({"token": token})
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500


if __name__ == "__main__":
    init_system()
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug_mode, port=1512, use_reloader=False)
