"""
user_management.py: User authentication and management.

Author:             Min Thu Khaing
Date:               December 21, 2024
Description:        Handles user authentication, registration, and 
                    session management.
"""

import os
import sqlite3
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
import jwt
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class UserManager:
    """Handles user authentication and management."""

    def __init__(self, db_path: str = "private/users.db"):
        """Initialize user manager."""
        os.makedirs("private", exist_ok=True)
        self.db_path = db_path
        self.secret_key = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
        self.init_database()

    def init_database(self):
        """Initialize user-related database tables."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()

            # Create users table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP,
                    last_login TIMESTAMP
                )
            """
            )

            # Create user_chats table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS user_chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message TEXT NOT NULL,
                    role TEXT NOT NULL,
                    timestamp TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )

            # Create user_documents table to track user-specific documents
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS user_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    document_id TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            """
            )

            conn.commit()

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username: str, password: str, email: str) -> bool:
        """
        Register a new user.

        Args:
            username: Desired username
            password: User's password
            email: User's email address

        Returns:
            bool: True if registration successful, False otherwise
        """
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
                user_dir = os.path.join("private", username)
                os.makedirs(os.path.join(user_dir, "uploads"), exist_ok=True)
                os.makedirs(os.path.join(user_dir, "vectordb"), exist_ok=True)

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
        """
        Authenticate user and return JWT token.

        Args:
            username: Username
            password: Password

        Returns:
            Optional[str]: JWT token if authentication successful, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()

                c.execute(
                    """
                    SELECT id, password_hash 
                    FROM users 
                    WHERE username = ?
                """,
                    (username,),
                )

                result = c.fetchone()
                if not result:
                    return None

                user_id, stored_hash = result

                if self._hash_password(password) != stored_hash:
                    return None

                # Update last login
                c.execute(
                    """
                    UPDATE users 
                    SET last_login = ? 
                    WHERE id = ?
                """,
                    (datetime.now(), user_id),
                )

                # Generate JWT token
                token = jwt.encode(
                    {
                        "user_id": user_id,
                        "username": username,
                        "exp": datetime.utcnow() + timedelta(days=1),
                    },
                    self.secret_key,
                    algorithm="HS256",
                )

                conn.commit()
                return token

        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token and return user info.

        Args:
            token: JWT token

        Returns:
            Optional[Dict]: User info if token valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return {"user_id": payload["user_id"], "username": payload["username"]}
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def save_chat_message(self, user_id: int, message: str, role: str):
        """
        Save chat message for a user.

        Args:
            user_id: User ID
            message: Chat message
            role: Message role ('user' or 'assistant')
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO user_chats (user_id, message, role, timestamp)
                    VALUES (?, ?, ?, ?)
                """,
                    (user_id, message, role, datetime.now()),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            raise

    def get_chat_history(self, user_id: int, limit: int = 50) -> list:
        """
        Get chat history for a user.

        Args:
            user_id: User ID
            limit: Maximum number of messages to return

        Returns:
            list: List of chat messages
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT message, role, timestamp
                    FROM user_chats
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (user_id, limit),
                )

                messages = []
                for msg, role, timestamp in c.fetchall():
                    messages.append(
                        {"content": msg, "role": role, "timestamp": timestamp}
                    )
                return messages[::-1]  # Reverse to get chronological order

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            raise

    def link_document_to_user(self, user_id: int, document_id: str):
        """
        Link a document to a user.

        Args:
            user_id: User ID
            document_id: Document ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO user_documents (user_id, document_id, created_at)
                    VALUES (?, ?, ?)
                """,
                    (user_id, document_id, datetime.now()),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error linking document to user: {e}")
            raise

    def get_user_documents(self, user_id: int) -> list:
        """
        Get all documents linked to a user.

        Args:
            user_id: User ID

        Returns:
            list: List of document IDs
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT document_id
                    FROM user_documents
                    WHERE user_id = ?
                """,
                    (user_id,),
                )
                return [row[0] for row in c.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user documents: {e}")
            raise
