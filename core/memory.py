"""Memory management system with SQLite persistence."""

import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text
    from sqlalchemy.orm import declarative_base, sessionmaker
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    logging.warning("SQLAlchemy not installed")
    create_engine = None
    declarative_base = None
    sessionmaker = None

from config import DATABASE_PATH, MEMORY_MAX_ITEMS, MEMORY_TTL_DAYS

logger = logging.getLogger(__name__)
Base = declarative_base() if declarative_base else None


class ConversationRecord(Base):
    """SQLAlchemy model for conversation history."""
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    context = Column(Text, default="{}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'user_message': self.user_message,
            'assistant_response': self.assistant_response,
            'context': json.loads(self.context) if self.context else {}
        }


class UserProfile(Base):
    """SQLAlchemy model for user profile."""
    __tablename__ = 'user_profile'

    id = Column(Integer, primary_key=True)
    user_name = Column(String(255), unique=True, nullable=False)
    preferences = Column(Text, default="{}")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'user_name': self.user_name,
            'preferences': json.loads(self.preferences) if self.preferences else {},
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class MemoryManager:
    """Manages conversation history and user profile in SQLite."""

    def __init__(self, db_path: Path = DATABASE_PATH):
        """Initialize memory manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.engine = None
        self.Session = None
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize database and create tables."""
        try:
            if not create_engine:
                logger.error("SQLAlchemy not available")
                return

            db_url = f"sqlite:///{self.db_path}"
            self.engine = create_engine(db_url, echo=False)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            logger.info(f"Memory database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize memory database: {e}")
            self.engine = None
            self.Session = None

    def save_conversation(self, user_message: str, assistant_response: str, context: Optional[Dict] = None) -> bool:
        """Save conversation to memory.
        
        Args:
            user_message: User's message
            assistant_response: Assistant's response
            context: Additional context data
            
        Returns:
            True if saved successfully
        """
        if not self.Session:
            logger.warning("Memory system not initialized")
            return False

        try:
            session = self.Session()
            record = ConversationRecord(
                user_message=user_message,
                assistant_response=assistant_response,
                context=json.dumps(context or {})
            )
            session.add(record)
            session.commit()
            session.close()
            logger.debug(f"Saved conversation: {user_message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False

    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent conversation history.
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation records
        """
        if not self.Session:
            return []

        try:
            session = self.Session()
            records = session.query(ConversationRecord).order_by(
                ConversationRecord.timestamp.desc()
            ).limit(limit).all()
            session.close()
            return [r.to_dict() for r in reversed(records)]
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            return []

    def get_conversation_for_ai(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get conversation history formatted for AI API.
        
        Args:
            limit: Number of recent messages to include
            
        Returns:
            List of messages in OpenAI format
        """
        history = self.get_conversation_history(limit * 2)
        messages = []
        for record in history:
            messages.append({"role": "user", "content": record['user_message']})
            messages.append({"role": "assistant", "content": record['assistant_response']})
        return messages[-limit * 2:]

    def update_user_profile(self, user_name: str, preferences: Optional[Dict] = None, notes: str = "") -> bool:
        """Update or create user profile.
        
        Args:
            user_name: User's name
            preferences: User preferences dictionary
            notes: Additional notes about user
            
        Returns:
            True if successful
        """
        if not self.Session:
            return False

        try:
            session = self.Session()
            profile = session.query(UserProfile).filter_by(user_name=user_name).first()
            
            if not profile:
                profile = UserProfile(user_name=user_name)
            
            if preferences:
                profile.preferences = json.dumps(preferences)
            if notes:
                profile.notes = notes
            profile.updated_at = datetime.utcnow()
            
            session.add(profile)
            session.commit()
            session.close()
            logger.debug(f"Updated user profile: {user_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False

    def get_user_profile(self, user_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile.
        
        Args:
            user_name: User's name
            
        Returns:
            User profile dictionary or None
        """
        if not self.Session:
            return None

        try:
            session = self.Session()
            profile = session.query(UserProfile).filter_by(user_name=user_name).first()
            session.close()
            return profile.to_dict() if profile else None
        except Exception as e:
            logger.error(f"Failed to retrieve user profile: {e}")
            return None

    def cleanup_old_conversations(self, days: int = MEMORY_TTL_DAYS) -> int:
        """Remove conversations older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of records deleted
        """
        if not self.Session:
            return 0

        try:
            session = self.Session()
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted = session.query(ConversationRecord).filter(
                ConversationRecord.timestamp < cutoff_date
            ).delete()
            session.commit()
            session.close()
            logger.info(f"Cleaned up {deleted} old conversations")
            return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup conversations: {e}")
            return 0

    def clear_all_history(self) -> bool:
        """Clear all conversation history (use with caution).
        
        Returns:
            True if successful
        """
        if not self.Session:
            return False

        try:
            session = self.Session()
            session.query(ConversationRecord).delete()
            session.commit()
            session.close()
            logger.warning("Cleared all conversation history")
            return True
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            return False
