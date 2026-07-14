"""Long-term memory system with SQLite persistence."""

import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

from config import DATABASE_PATH, MEMORY_MAX_ITEMS, MEMORY_TTL_DAYS

logger = logging.getLogger(__name__)

Base = declarative_base()


class ConversationRecord(Base):
    """Conversation memory record."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    provider = Column(String(50), default="unknown")
    tags = Column(Text, default="")  # JSON string


class UserProfile(Base):
    """User profile information."""
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), default="User")
    email = Column(String(255))
    preferences = Column(Text, default="{}")  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Note(Base):
    """User notes."""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    archived = Column(Boolean, default=False)


class Task(Base):
    """User tasks."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    due_date = Column(DateTime)
    priority = Column(Integer, default=0)  # 0=low, 1=medium, 2=high


class ProjectMemory(Base):
    """Memory about projects."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    path = Column(Text)
    description = Column(Text)
    language = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    metadata = Column(Text, default="{}")  # JSON string


class MemorySystem:
    """Manage long-term memory with SQLite."""

    def __init__(self, db_path: Path = DATABASE_PATH):
        """Initialize memory system.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"Memory system initialized at {db_path}")

    def add_conversation(self, user_message: str, assistant_response: str, provider: str = "unknown") -> None:
        """Add conversation to memory.
        
        Args:
            user_message: User's message
            assistant_response: Assistant's response
            provider: AI provider used
        """
        try:
            session = self.Session()
            record = ConversationRecord(
                user_message=user_message,
                assistant_response=assistant_response,
                provider=provider
            )
            session.add(record)
            session.commit()
            session.close()
            logger.debug("Conversation stored")
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations.
        
        Args:
            limit: Number of conversations to retrieve
            
        Returns:
            List of conversation records
        """
        try:
            session = self.Session()
            records = session.query(ConversationRecord).order_by(
                ConversationRecord.timestamp.desc()
            ).limit(limit).all()
            session.close()

            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat(),
                    "user_message": r.user_message,
                    "assistant_response": r.assistant_response,
                    "provider": r.provider
                }
                for r in records
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve conversations: {e}")
            return []

    def search_conversations(self, query: str) -> List[Dict[str, Any]]:
        """Search conversations.
        
        Args:
            query: Search query
            
        Returns:
            Matching conversations
        """
        try:
            session = self.Session()
            records = session.query(ConversationRecord).filter(
                ConversationRecord.user_message.contains(query) |
                ConversationRecord.assistant_response.contains(query)
            ).order_by(ConversationRecord.timestamp.desc()).limit(20).all()
            session.close()

            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat(),
                    "user_message": r.user_message,
                    "assistant_response": r.assistant_response
                }
                for r in records
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def add_note(self, title: str, content: str) -> int:
        """Add a note.
        
        Args:
            title: Note title
            content: Note content
            
        Returns:
            Note ID
        """
        try:
            session = self.Session()
            note = Note(title=title, content=content)
            session.add(note)
            session.commit()
            note_id = note.id
            session.close()
            logger.info(f"Note created: {note_id}")
            return note_id
        except Exception as e:
            logger.error(f"Failed to create note: {e}")
            return -1

    def get_notes(self, archived: bool = False) -> List[Dict[str, Any]]:
        """Get notes.
        
        Args:
            archived: Get archived notes
            
        Returns:
            List of notes
        """
        try:
            session = self.Session()
            notes = session.query(Note).filter(
                Note.archived == archived
            ).order_by(Note.created_at.desc()).all()
            session.close()

            return [
                {
                    "id": n.id,
                    "title": n.title,
                    "content": n.content,
                    "created_at": n.created_at.isoformat(),
                    "updated_at": n.updated_at.isoformat()
                }
                for n in notes
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve notes: {e}")
            return []

    def add_task(self, title: str, description: str = "", priority: int = 0, due_date: Optional[datetime] = None) -> int:
        """Add a task.
        
        Args:
            title: Task title
            description: Task description
            priority: Priority level (0-2)
            due_date: Due date
            
        Returns:
            Task ID
        """
        try:
            session = self.Session()
            task = Task(
                title=title,
                description=description,
                priority=priority,
                due_date=due_date
            )
            session.add(task)
            session.commit()
            task_id = task.id
            session.close()
            logger.info(f"Task created: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return -1

    def get_tasks(self, completed: bool = False) -> List[Dict[str, Any]]:
        """Get tasks.
        
        Args:
            completed: Get completed tasks
            
        Returns:
            List of tasks
        """
        try:
            session = self.Session()
            tasks = session.query(Task).filter(
                Task.completed == completed
            ).order_by(Task.priority.desc(), Task.due_date).all()
            session.close()

            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "completed": t.completed,
                    "priority": t.priority,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "created_at": t.created_at.isoformat()
                }
                for t in tasks
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve tasks: {e}")
            return []

    def complete_task(self, task_id: int) -> bool:
        """Mark task as complete.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if successful
        """
        try:
            session = self.Session()
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                task.completed = True
                session.commit()
                session.close()
                logger.info(f"Task {task_id} completed")
                return True
            session.close()
            return False
        except Exception as e:
            logger.error(f"Failed to complete task: {e}")
            return False

    def add_project(self, name: str, path: str, language: str = "", description: str = "") -> int:
        """Add project to memory.
        
        Args:
            name: Project name
            path: Project path
            language: Programming language
            description: Project description
            
        Returns:
            Project ID
        """
        try:
            session = self.Session()
            project = ProjectMemory(
                name=name,
                path=path,
                language=language,
                description=description
            )
            session.add(project)
            session.commit()
            project_id = project.id
            session.close()
            logger.info(f"Project added: {name}")
            return project_id
        except Exception as e:
            logger.error(f"Failed to add project: {e}")
            return -1

    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects.
        
        Returns:
            List of projects
        """
        try:
            session = self.Session()
            projects = session.query(ProjectMemory).order_by(
                ProjectMemory.last_accessed.desc()
            ).all()
            session.close()

            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "path": p.path,
                    "language": p.language,
                    "description": p.description,
                    "created_at": p.created_at.isoformat(),
                    "last_accessed": p.last_accessed.isoformat()
                }
                for p in projects
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve projects: {e}")
            return []

    def cleanup_old_conversations(self, days: int = MEMORY_TTL_DAYS) -> int:
        """Clean up old conversations.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of records deleted
        """
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
            logger.error(f"Cleanup failed: {e}")
            return 0
