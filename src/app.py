"""
app.py          flask app for RAG system

Author:         Min Thu Khaing
Date:           December 21, 2024
Description:    Flask API for RAG system with user authentication.
"""

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from rag_system import HirakuRAG
from user_management import UserManager
import os
import logging
from functools import wraps
from werkzeug.utils import secure_filename

# Get the project root directory (parent of src/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],  # Next.js default port
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

user_manager = None
rag_instances = {}
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
        # Create base private directory in project root
        private_dir = os.path.join(PROJECT_ROOT, "private")
        os.makedirs(private_dir, exist_ok=True)
        
        # Create subdirectories
        subdirs = ["users", "uploads", "vectordb"]
        for subdir in subdirs:
            os.makedirs(os.path.join(private_dir, subdir), exist_ok=True)

        # Initialize user manager with proper database path
        if user_manager is None:
            db_path = os.path.join(private_dir, "users.db")
            user_manager = UserManager(db_path=db_path)
            # Initialize the database tables
            user_manager.init_database()
        _initialized = True

        logging.info("System initialized successfully")

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
        session_id = data.get("session_id")
        mode = data.get("mode", "interactive")  # Get mode from request
        history = user_manager.get_chat_history(user_info["user_id"], session_id=session_id)

        if not question:
            return jsonify({"error": "No question provided"}), 400

        rag = get_user_rag(user_info["username"])
        
        # Set precision mode if provided
        if mode:
            rag.set_precision_mode(mode)

        # Get response from RAG system
        response = rag.query(question, history=history)

        # Save the conversation
        user_manager.save_chat_message(user_info["user_id"], question, "user", session_id)
        user_manager.save_chat_message(
            user_info["user_id"], response.get("answer", ""), "assistant", session_id
        )

        return jsonify({
            "answer": response.get("answer", ""),
            "sources": response.get("sources", [])
        })
    except Exception as e:
        logging.error(f"Error in query: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
@require_auth
def upload_file(user_info):
    """Handle file upload."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        # Get user directory
        username = user_info["username"]
        user_dir = user_manager.get_user_dir(username)
        user_uploads_dir = os.path.join(user_dir, "uploads")
        os.makedirs(user_uploads_dir, exist_ok=True)

        # Save file to user's upload directory
        filename = secure_filename(file.filename)
        file_path = os.path.join(user_uploads_dir, filename)
        file.save(file_path)

        # Initialize RAG for user if needed
        if username not in rag_instances:
            rag_instances[username] = HirakuRAG(username=username)

        # Process the file with RAG system
        rag_instances[username].add_documents([file_path])

        # Link document to user
        user_manager.link_document_to_user(user_info["user_id"], filename)

        return jsonify({
            "message": "File uploaded and processed successfully",
            "filename": filename
        })

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


@app.route("/api/get-precision", methods=["GET"])
@require_auth
def get_precision(user_info):
    """Get user's precision mode setting"""
    try:
        rag = get_user_rag(user_info["username"])
        return jsonify({"mode": rag.precision_mode})
    except Exception as e:
        logging.error(f"Error getting precision mode: {str(e)}")
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


@app.route("/api/chat-history", methods=["GET"])
@require_auth
def get_chat_history(user_info):
    """Get chat history for a specific session"""
    try:
        session_id = request.args.get("session_id", type=int)
        history = user_manager.get_chat_history(user_info["user_id"], session_id=session_id)
        return jsonify({"history": history})
    except Exception as e:
        logging.error(f"Error getting chat history: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat-sessions", methods=["GET"])
@require_auth
def get_chat_sessions(user_info):
    """Get all chat sessions for a user"""
    try:
        sessions = user_manager.get_chat_sessions(user_info["user_id"])
        return jsonify({"sessions": sessions})
    except Exception as e:
        logging.error(f"Error getting chat sessions: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat-sessions", methods=["POST"])
@require_auth
def create_chat_session(user_info):
    """Create a new chat session"""
    try:
        data = request.json
        title = data.get("title", "New Chat")
        session_id = user_manager.create_chat_session(user_info["user_id"], title)
        return jsonify({"session_id": session_id})
    except Exception as e:
        logging.error(f"Error creating chat session: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stream", methods=["POST"])
@require_auth
def stream_query(user_info):
    """Handle streaming query requests"""
    try:
        data = request.json
        question = data.get("question", "")
        session_id = data.get("session_id")
        history = user_manager.get_chat_history(user_info["user_id"], session_id=session_id)

        if not question:
            return jsonify({"error": "No question provided"}), 400

        rag = get_user_rag(user_info["username"])

        def generate():
            response = ""
            for chunk in rag.stream_query(question, history=history):
                response += chunk
                yield f"data: {chunk}\n\n"
            
            # Save the conversation after completion
            user_manager.save_chat_message(user_info["user_id"], question, "user", session_id)
            user_manager.save_chat_message(user_info["user_id"], response, "assistant", session_id)

        return Response(stream_with_context(generate()), mimetype="text/event-stream")
    except Exception as e:
        logging.error(f"Error in stream query: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_system()
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug_mode, port=1512, use_reloader=False)
