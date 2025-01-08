"""
user_management.py: User authentication and management module.
"""

import os
import jwt
import logging
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# Get the project root directory (parent of src/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configure private directory paths
PRIVATE_DIR = os.path.join(PROJECT_ROOT, "private")
USERS_DIR = os.path.join(PRIVATE_DIR, "users")
UPLOADS_DIR = os.path.join(PRIVATE_DIR, "uploads")
VECTORDB_DIR = os.path.join(PRIVATE_DIR, "vectordb")
DB_PATH = os.path.join(PRIVATE_DIR, "users.db")

# logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UserManager:
    """Handles user authentication and management."""

    def __init__(self, db_path: str = None):
        """Initialize user manager."""
        self.db_path = db_path or DB_PATH
        self.private_dir = PRIVATE_DIR
        self.users_dir = USERS_DIR
        self.uploads_dir = UPLOADS_DIR
        self.vectordb_dir = VECTORDB_DIR
        
        # Ensure all directories exist
        for directory in [self.private_dir, self.users_dir, self.uploads_dir, self.vectordb_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Get JWT secret from environment or generate a persistent one
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        if not self.secret_key:
            secret_path = os.path.join(self.private_dir, ".jwt_secret")
            if os.path.exists(secret_path):
                with open(secret_path, "r") as f:
                    self.secret_key = f.read().strip()
            else:
                self.secret_key = secrets.token_hex(32)
                with open(secret_path, "w") as f:
                    f.write(self.secret_key)
        
        self.init_database()

    def init_database(self):
        """Initialize user-related database tables."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()

            # Create users table if not exists (don't drop existing)
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)

            # Create chat_sessions table if not exists
            c.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Create user_chats table with session support
            c.execute("""
                CREATE TABLE IF NOT EXISTS user_chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_id INTEGER,
                    message TEXT NOT NULL,
                    role TEXT NOT NULL,
                    timestamp TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
                )
            """)

            # Create user_documents table to track user-specific documents
            c.execute("""
                CREATE TABLE IF NOT EXISTS user_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    document_id TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            conn.commit()
            logger.info("Database initialized successfully")

    def get_user_dir(self, username: str) -> str:
        """Get user-specific directory path."""
        return os.path.join(self.users_dir, username)

    def create_user_directories(self, username: str) -> None:
        """Create user-specific directories."""
        user_dir = self.get_user_dir(username)
        os.makedirs(user_dir, exist_ok=True)
        os.makedirs(os.path.join(user_dir, "uploads"), exist_ok=True)
        os.makedirs(os.path.join(user_dir, "vectordb"), exist_ok=True)
        os.makedirs(os.path.join(user_dir, "chats"), exist_ok=True)

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username: str, password: str, email: str) -> bool:
        """Register a new user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()

                # Check if username or email exists
                c.execute(
                    "SELECT id FROM users WHERE username = ? OR email = ?",
                    (username, email),
                )
                if c.fetchone():
                    return False

                # Create user-specific directory structure
                self.create_user_directories(username)

                # Insert new user
                c.execute(
                    """
                    INSERT INTO users (username, password_hash, email, created_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (username, self._hash_password(password), email, datetime.now()),
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT id, password_hash FROM users WHERE username = ?", (username,)
                )
                result = c.fetchone()

                if result and result[1] == self._hash_password(password):
                    # Update last login
                    c.execute(
                        "UPDATE users SET last_login = ? WHERE id = ?",
                        (datetime.now(), result[0]),
                    )
                    conn.commit()

                    # Generate token
                    token = jwt.encode(
                        {
                            "user_id": result[0],
                            "username": username,
                            "exp": datetime.utcnow() + timedelta(days=7),
                        },
                        self.secret_key,
                        algorithm="HS256",
                    )
                    return token

                return None

        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return user info."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def validate_user_session(self, user_id: int, session_id: int) -> bool:
        """Validate that a session exists and belongs to the user."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # First verify user exists
            c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not c.fetchone():
                logger.warning(f"User {user_id} not found")
                return False
            
            # Then verify session exists and belongs to user
            c.execute(
                """
                SELECT id FROM chat_sessions 
                WHERE id = ? AND user_id = ?
                """,
                (session_id, user_id)
            )
            if not c.fetchone():
                logger.warning(f"Session {session_id} not found or does not belong to user {user_id}")
                return False
                
            return True

    def save_chat_message(self, user_id: int, message: str, role: str, session_id: int) -> Optional[int]:
        """Save a chat message.
        
        Args:
            user_id: The ID of the user
            message: The chat message to save
            role: The role of the message sender
            session_id: The ID of the chat session (required)
            
        Returns:
            Optional[int]: The session ID if successful, None if validation fails
            
        Raises:
            ValueError: If session_id is not provided
            Exception: For database errors
        """
        if session_id is None:
            raise ValueError("session_id is required")

        try:
            # Validate session before proceeding
            if not self.validate_user_session(user_id, session_id):
                logger.error(f"Invalid session {session_id} for user {user_id}")
                return None

            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                now = datetime.utcnow()
                
                # Save the message
                c.execute(
                    """
                    INSERT INTO user_chats (user_id, session_id, message, role, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, session_id, message, role, now),
                )
                
                # Update session's updated_at timestamp
                c.execute(
                    """
                    UPDATE chat_sessions
                    SET updated_at = ?
                    WHERE id = ?
                    """,
                    (now, session_id),
                )
                conn.commit()
                return session_id
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            raise

    def get_chat_history(self, user_id: int, session_id: int = None, limit: int = 50) -> list:
        """Get chat history for a user and optionally for a specific session."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            if session_id:
                c.execute(
                    """
                    SELECT message, role, timestamp, id
                    FROM user_chats
                    WHERE user_id = ? AND session_id = ?
                    ORDER BY timestamp ASC, id ASC
                    LIMIT ?
                    """,
                    (user_id, session_id, limit),
                )
            else:
                # Get the latest session if none specified
                c.execute(
                    """
                    SELECT id FROM chat_sessions
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (user_id,),
                )
                result = c.fetchone()
                if result:
                    session_id = result[0]
                    c.execute(
                        """
                        SELECT message, role, timestamp, id
                        FROM user_chats
                        WHERE user_id = ? AND session_id = ?
                        ORDER BY timestamp ASC, id ASC
                        LIMIT ?
                        """,
                        (user_id, session_id, limit),
                    )
                else:
                    return []

            messages = [
                {
                    "content": row[0],
                    "role": row[1],
                    "timestamp": row[2]
                }
                for row in c.fetchall()
            ]
            return messages  # No need to reverse since we're already ordering by ASC

    def link_document_to_user(self, user_id: int, document_id: str):
        """Link a document to a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                
                # Get username for the user_id
                c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                result = c.fetchone()
                if not result:
                    raise ValueError("User not found")
                
                username = result[0]
                user_dir = self.get_user_dir(username)
                user_uploads_dir = os.path.join(user_dir, "uploads")
                
                # Check if document exists in user's upload directory
                document_path = os.path.join(user_uploads_dir, document_id)
                if not os.path.exists(document_path):
                    raise FileNotFoundError(f"Document not found: {document_id}")

                # Check if document is already linked
                c.execute(
                    """
                    SELECT id FROM user_documents 
                    WHERE user_id = ? AND document_id = ?
                    """,
                    (user_id, document_id)
                )
                
                if not c.fetchone():
                    # Only insert if not already linked
                    c.execute(
                        """
                        INSERT INTO user_documents (user_id, document_id, created_at)
                        VALUES (?, ?, ?)
                    """,
                        (user_id, document_id, datetime.now()),
                    )
                    conn.commit()
                    logger.info(f"Document {document_id} linked to user {username}")
                else:
                    logger.info(f"Document {document_id} already linked to user {username}")

        except Exception as e:
            logger.error(f"Error linking document to user: {e}")
            raise

    def get_user_documents(self, user_id: int) -> list:
        """Get all documents linked to a user."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT document_id, created_at
                FROM user_documents
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            return c.fetchall()

    def create_chat_session(self, user_id: int, title: str = "New Chat") -> int:
        """Create a new chat session for a user."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            now = datetime.utcnow()
            c.execute(
                """
                INSERT INTO chat_sessions (user_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, title, now, now),
            )
            conn.commit()
            return c.lastrowid

    def get_chat_sessions(self, user_id: int) -> list:
        """Get all chat sessions for a user."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM chat_sessions
                WHERE user_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id,),
            )
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "created_at": row[2],
                    "updated_at": row[3]
                }
                for row in c.fetchall()
            ]

    def delete_chat_session(self, user_id: int, session_id: int) -> bool:
        """Delete a chat session and all its messages.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the chat session to delete
            
        Returns:
            bool: True if successful, False if session doesn't exist or belong to user
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                
                # First verify the session belongs to the user
                c.execute(
                    """
                    SELECT id FROM chat_sessions
                    WHERE id = ? AND user_id = ?
                    """,
                    (session_id, user_id)
                )
                
                if not c.fetchone():
                    return False
                
                # Delete all messages in the session
                c.execute(
                    """
                    DELETE FROM user_chats
                    WHERE session_id = ? AND user_id = ?
                    """,
                    (session_id, user_id)
                )
                
                # Delete the session itself
                c.execute(
                    """
                    DELETE FROM chat_sessions
                    WHERE id = ? AND user_id = ?
                    """,
                    (session_id, user_id)
                )
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error deleting chat session: {e}")
            return False
