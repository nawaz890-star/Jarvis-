"""Memory Manager - SQLite-based long-term memory system."""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Single memory entry."""
    id: Optional[int] = None
    type: str = "general"  # conversation, task, note, project, code
    content: str = ""
    metadata: Dict[str, Any] = None
    created_at: str = ""
    updated_at: str = ""
    importance: int = 1  # 1-10 scale
    tags: List[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


class MemoryManager:
    """Manage long-term memory with SQLite database."""

    def __init__(self, db_path: Path = Path("data/jarvis.db")):
        """Initialize Memory Manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Memory table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        importance INTEGER DEFAULT 1,
                        tags TEXT
                    )
                """)
                
                # Conversation history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_message TEXT NOT NULL,
                        ai_response TEXT NOT NULL,
                        provider TEXT,
                        timestamp TEXT NOT NULL
                    )
                """)
                
                # User profile table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_profile (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                """)
                
                # Project memory table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        path TEXT,
                        type TEXT,
                        description TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    def add_memory(self, entry: MemoryEntry) -> int:
        """Add new memory entry.
        
        Args:
            entry: Memory entry to add
            
        Returns:
            Memory ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO memory (type, content, metadata, created_at, updated_at, importance, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.type,
                    entry.content,
                    json.dumps(entry.metadata),
                    entry.created_at,
                    entry.updated_at,
                    entry.importance,
                    json.dumps(entry.tags)
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return -1

    def search_memory(self, query: str, memory_type: Optional[str] = None, limit: int = 10) -> List[MemoryEntry]:
        """Search memory entries.
        
        Args:
            query: Search query
            memory_type: Filter by type
            limit: Maximum results
            
        Returns:
            List of matching memory entries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                sql = "SELECT * FROM memory WHERE content LIKE ?"
                params = [f"%{query}%"]
                
                if memory_type:
                    sql += " AND type = ?"
                    params.append(memory_type)
                
                sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    entry = MemoryEntry(
                        id=row[0],
                        type=row[1],
                        content=row[2],
                        metadata=json.loads(row[3]) if row[3] else {},
                        created_at=row[4],
                        updated_at=row[5],
                        importance=row[6],
                        tags=json.loads(row[7]) if row[7] else []
                    )
                    results.append(entry)
                
                return results
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []

    def add_conversation(self, user_message: str, ai_response: str, provider: str = "unknown") -> None:
        """Store conversation turn.
        
        Args:
            user_message: User input
            ai_response: AI response
            provider: AI provider used
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations (user_message, ai_response, provider, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (user_message, ai_response, provider, datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")

    def get_conversation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent conversation history.
        
        Args:
            limit: Number of recent conversations
            
        Returns:
            List of conversation turns
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_message, ai_response, provider, timestamp FROM conversations
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                return [
                    {
                        "user": row[0],
                        "assistant": row[1],
                        "provider": row[2],
                        "timestamp": row[3]
                    }
                    for row in reversed(rows)
                ]
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    def cleanup_old_memories(self, days: int = 90) -> int:
        """Remove old memory entries.
        
        Args:
            days: Remove entries older than this many days
            
        Returns:
            Number of entries deleted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cutoff = (datetime.now() - timedelta(days=days)).isoformat()
                cursor.execute("DELETE FROM memory WHERE created_at < ?", (cutoff,))
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error cleaning up memories: {e}")
            return 0
