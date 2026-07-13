"""
Memory - SQLite-backed Storage for FRIDAY AI
Stores voice interactions, preferences, events, etc.
"""

import atexit
import json
import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.friday.config.settings import DB_PATH as SETTINGS_DB_PATH

logger = logging.getLogger("friday.memory")

# Database path - can be overridden by config
DB_PATH = SETTINGS_DB_PATH

# Connection pool - thread-local storage
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """
    Get a thread-local SQLite connection with WAL mode for concurrency.
    """
    if not hasattr(_local, 'connection') or _local.connection is None:
        _local.connection = sqlite3.connect(
            DB_PATH,
            check_same_thread=False,
            timeout=10.0
        )
        _local.connection.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        _local.connection.execute("PRAGMA journal_mode=WAL")
        _local.connection.execute("PRAGMA synchronous=NORMAL")
        _local.connection.execute("PRAGMA cache_size=-2000")  # 2MB cache
        _local.connection.execute("PRAGMA foreign_keys=ON")
        logger.debug(f"New DB connection to {DB_PATH}")
    return _local.connection


@contextmanager
def get_cursor(commit: bool = False):
    """
    Context manager for database operations.

    Usage:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM table")
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        cursor.close()


def init_db():
    """
    Initialize database schema if not exists.
    Called on module import.
    """
    logger.info(f"Initializing database at {DB_PATH}")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_cursor(commit=True) as cursor:
        # Voice interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                wake_timestamp DATETIME,
                transcript TEXT NOT NULL,
                response TEXT,
                total_latency_ms REAL,
                stt_latency_ms REAL,
                tts_latency_ms REAL,
                llm_latency_ms REAL,
                audio_duration_sec REAL,
                confidence REAL,
                wake_word TEXT,
                is_successful BOOLEAN DEFAULT 1
            )
        """)

        # User preferences (key-value store)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Conversation history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_text TEXT NOT NULL,
                friday_response TEXT,
                session_id TEXT,
                metadata TEXT  -- JSON blob for extra data
            )
        """)

        # System events log (for debugging/audit)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                source TEXT,  -- module name
                data TEXT,    -- JSON blob
                processed BOOLEAN DEFAULT 0
            )
        """)

        # Automation triggers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                trigger_condition TEXT,  -- JSON condition
                action TEXT,             -- JSON action
                enabled BOOLEAN DEFAULT 1,
                last_triggered DATETIME,
                trigger_count INTEGER DEFAULT 0
            )
        """)

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_voice_timestamp
            ON voice_interactions(timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_voice_wake
            ON voice_interactions(wake_timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_timestamp
            ON conversations(timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_events_timestamp
            ON system_events(timestamp DESC)
        """)

    logger.info("Database schema initialized")


def close_connections():
    """
    Close all thread-local connections.
    Called at exit.
    """
    if hasattr(_local, 'connection') and _local.connection:
        _local.connection.close()
        _local.connection = None
        logger.debug("DB connection closed")


# Register cleanup
atexit.register(close_connections)


# ========== Voice Interaction CRUD ==========

def log_voice_interaction(
    transcript: str,
    response: Optional[str] = None,
    wake_timestamp: Optional[float] = None,
    total_latency_ms: Optional[float] = None,
    stt_latency_ms: Optional[float] = None,
    tts_latency_ms: Optional[float] = None,
    llm_latency_ms: Optional[float] = None,
    audio_duration_sec: Optional[float] = None,
    confidence: Optional[float] = None,
    wake_word: Optional[str] = None,
    is_successful: bool = True
) -> int:
    """
    Log a voice interaction to the database.

    Returns:
        The ID of the inserted row.
    """
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO voice_interactions (
                wake_timestamp, transcript, response, total_latency_ms,
                stt_latency_ms, tts_latency_ms, llm_latency_ms,
                audio_duration_sec, confidence, wake_word, is_successful
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wake_timestamp, transcript, response, total_latency_ms,
            stt_latency_ms, tts_latency_ms, llm_latency_ms,
            audio_duration_sec, confidence, wake_word, is_successful
        ))
        return cursor.lastrowid


def get_recent_interactions(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent voice interactions."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM voice_interactions
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_voice_interaction_stats() -> Dict[str, Any]:
    """Get statistics about voice interactions."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_count,
                AVG(total_latency_ms) as avg_latency,
                MIN(total_latency_ms) as min_latency,
                MAX(total_latency_ms) as max_latency,
                AVG(stt_latency_ms) as avg_stt,
                AVG(tts_latency_ms) as avg_tts,
                AVG(llm_latency_ms) as avg_llm,
                SUM(CASE WHEN is_successful THEN 1 ELSE 0 END) as successful_count
            FROM voice_interactions
            WHERE timestamp > datetime('now', '-24 hours')
        """)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {}


# ========== Preferences ==========

def get_preference(key: str, default: Any = None) -> Any:
    """Get a preference value."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT value FROM preferences WHERE key = ?
        """, (key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row['value'])
            except (json.JSONDecodeError, TypeError):
                return row['value']
        return default


def set_preference(key: str, value: Any):
    """Set a preference value."""
    if isinstance(value, (dict, list)):
        value_str = json.dumps(value)
    else:
        value_str = str(value)

    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT OR REPLACE INTO preferences (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value_str))


# ========== Conversations ==========

def log_conversation(
    user_text: str,
    friday_response: str,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Log a conversation turn."""
    metadata_json = json.dumps(metadata) if metadata else None
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO conversations (
                user_text, friday_response, session_id, metadata
            ) VALUES (?, ?, ?, ?)
        """, (user_text, friday_response, session_id, metadata_json))
        return cursor.lastrowid


def get_recent_conversations(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent conversations."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            conv = dict(row)
            if conv['metadata']:
                try:
                    conv['metadata'] = json.loads(conv['metadata'])
                except json.JSONDecodeError:
                    pass
            result.append(conv)
        return result


# ========== System Events ==========

def log_system_event(
    event_type: str,
    source: str,
    data: Optional[Dict[str, Any]] = None
) -> int:
    """Log a system event."""
    data_json = json.dumps(data) if data else None
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO system_events (event_type, source, data)
            VALUES (?, ?, ?)
        """, (event_type, source, data_json))
        return cursor.lastrowid


def get_recent_system_events(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent system events."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM system_events
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            evt = dict(row)
            if evt['data']:
                try:
                    evt['data'] = json.loads(evt['data'])
                except json.JSONDecodeError:
                    pass
            result.append(evt)
        return result


# ========== Utility Functions ==========

def vacuum_database():
    """Vacuum the database to reclaim space."""
    with get_cursor(commit=True) as cursor:
        cursor.execute("VACUUM")
    logger.info("Database vacuumed")


def get_database_size() -> int:
    """Get database size in bytes."""
    if DB_PATH.exists():
        return DB_PATH.stat().st_size
    return 0


def execute_query(query: str, params: Tuple = (), fetch: bool = True) -> Optional[List[Dict[str, Any]]]:
    """
    Execute a raw query (use with caution).
    """
    with get_cursor() as cursor:
        cursor.execute(query, params)
        if fetch:
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        return None


# Initialize on import
init_db()

# Exported functions
__all__ = [
    'get_connection',
    'get_cursor',
    'init_db',
    'close_connections',
    'log_voice_interaction',
    'get_recent_interactions',
    'get_voice_interaction_stats',
    'get_preference',
    'set_preference',
    'log_conversation',
    'get_recent_conversations',
    'log_system_event',
    'get_recent_system_events',
    'vacuum_database',
    'get_database_size',
    'execute_query'
]