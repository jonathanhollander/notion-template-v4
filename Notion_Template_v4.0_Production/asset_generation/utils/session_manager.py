#!/usr/bin/env python3
"""
SQLite-based Session Management for Estate Planning Concierge v4.0
Provides secure session storage without requiring Redis
"""

import sqlite3
import json
import secrets
import hashlib
import time
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import logging
from pathlib import Path
import asyncio
import aiosqlite

class SessionManager:
    """SQLite-backed session management with CSRF protection"""
    
    def __init__(self, db_path: str = "sessions.db", session_lifetime: int = 3600):
        """
        Initialize session manager
        
        Args:
            db_path: Path to SQLite database file
            session_lifetime: Session lifetime in seconds (default 1 hour)
        """
        self.db_path = db_path
        self.session_lifetime = session_lifetime
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with session tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    csrf_token TEXT NOT NULL,
                    user_data TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_expires 
                ON sessions(expires_at)
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    ip_address TEXT,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            conn.commit()
            self.logger.info(f"Session database initialized at {self.db_path}")
    
    async def init_async_database(self):
        """Initialize async database connection"""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    csrf_token TEXT NOT NULL,
                    user_data TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_expires 
                ON sessions(expires_at)
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS session_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    ip_address TEXT,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            await conn.commit()
    
    def create_session(self, user_data: Optional[Dict] = None, 
                      ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None) -> Dict[str, str]:
        """
        Create a new session with CSRF token
        
        Args:
            user_data: Optional user data to store in session
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Dict with session_id and csrf_token
        """
        session_id = secrets.token_urlsafe(32)
        csrf_token = self._generate_csrf_token(session_id)
        
        now = time.time()
        expires_at = now + self.session_lifetime
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions 
                (session_id, csrf_token, user_data, ip_address, user_agent, 
                 created_at, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, csrf_token, 
                json.dumps(user_data) if user_data else None,
                ip_address, user_agent,
                now, now, expires_at
            ))
            
            # Log session creation
            conn.execute("""
                INSERT INTO session_activity (session_id, action, ip_address, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session_id, 'created', ip_address, now))
            
            conn.commit()
        
        self.logger.info(f"Session created: {session_id[:8]}... from {ip_address}")
        
        return {
            'session_id': session_id,
            'csrf_token': csrf_token,
            'expires_at': datetime.fromtimestamp(expires_at).isoformat()
        }
    
    async def create_session_async(self, user_data: Optional[Dict] = None,
                                  ip_address: Optional[str] = None,
                                  user_agent: Optional[str] = None) -> Dict[str, str]:
        """Async version of create_session"""
        session_id = secrets.token_urlsafe(32)
        csrf_token = self._generate_csrf_token(session_id)
        
        now = time.time()
        expires_at = now + self.session_lifetime
        
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT INTO sessions 
                (session_id, csrf_token, user_data, ip_address, user_agent, 
                 created_at, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, csrf_token,
                json.dumps(user_data) if user_data else None,
                ip_address, user_agent,
                now, now, expires_at
            ))
            
            await conn.execute("""
                INSERT INTO session_activity (session_id, action, ip_address, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session_id, 'created', ip_address, now))
            
            await conn.commit()
        
        return {
            'session_id': session_id,
            'csrf_token': csrf_token,
            'expires_at': datetime.fromtimestamp(expires_at).isoformat()
        }
    
    def validate_session(self, session_id: str, csrf_token: Optional[str] = None,
                        ip_address: Optional[str] = None) -> bool:
        """
        Validate session and optionally CSRF token
        
        Args:
            session_id: Session ID to validate
            csrf_token: Optional CSRF token to validate
            ip_address: Optional IP address to log
            
        Returns:
            True if session is valid, False otherwise
        """
        now = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT csrf_token, expires_at, ip_address 
                FROM sessions 
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            
            if not row:
                self.logger.warning(f"Invalid session attempt: {session_id[:8]}...")
                return False
            
            stored_csrf, expires_at, stored_ip = row
            
            # Check if session expired
            if now > expires_at:
                self.logger.warning(f"Expired session: {session_id[:8]}...")
                conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                return False
            
            # Validate CSRF token if provided
            if csrf_token and not secrets.compare_digest(stored_csrf, csrf_token):
                self.logger.warning(f"Invalid CSRF token for session: {session_id[:8]}...")
                # Log suspicious activity
                conn.execute("""
                    INSERT INTO session_activity (session_id, action, ip_address, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (session_id, 'invalid_csrf', ip_address, now))
                conn.commit()
                return False
            
            # Update session activity
            conn.execute("""
                UPDATE sessions 
                SET updated_at = ? 
                WHERE session_id = ?
            """, (now, session_id))
            
            conn.execute("""
                INSERT INTO session_activity (session_id, action, ip_address, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session_id, 'validated', ip_address, now))
            
            conn.commit()
            
        return True
    
    async def validate_session_async(self, session_id: str, csrf_token: Optional[str] = None,
                                    ip_address: Optional[str] = None) -> bool:
        """Async version of validate_session"""
        now = time.time()
        
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute("""
                SELECT csrf_token, expires_at, ip_address 
                FROM sessions 
                WHERE session_id = ?
            """, (session_id,)) as cursor:
                row = await cursor.fetchone()
            
            if not row:
                return False
            
            stored_csrf, expires_at, stored_ip = row
            
            if now > expires_at:
                await conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                await conn.commit()
                return False
            
            if csrf_token and not secrets.compare_digest(stored_csrf, csrf_token):
                await conn.execute("""
                    INSERT INTO session_activity (session_id, action, ip_address, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (session_id, 'invalid_csrf', ip_address, now))
                await conn.commit()
                return False
            
            await conn.execute("""
                UPDATE sessions 
                SET updated_at = ? 
                WHERE session_id = ?
            """, (now, session_id))
            
            await conn.execute("""
                INSERT INTO session_activity (session_id, action, ip_address, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session_id, 'validated', ip_address, now))
            
            await conn.commit()
            
        return True
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get session user data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT user_data FROM sessions 
                WHERE session_id = ? AND expires_at > ?
            """, (session_id, time.time()))
            
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
        
        return None
    
    def update_session_data(self, session_id: str, user_data: Dict) -> bool:
        """Update session user data"""
        now = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE sessions 
                SET user_data = ?, updated_at = ?
                WHERE session_id = ? AND expires_at > ?
            """, (json.dumps(user_data), now, session_id, now))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM sessions WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions from database"""
        now = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM sessions WHERE expires_at < ?
            """, (now,))
            
            deleted = cursor.rowcount
            
            # Also cleanup old activity logs (older than 7 days)
            week_ago = now - (7 * 24 * 3600)
            conn.execute("""
                DELETE FROM session_activity WHERE timestamp < ?
            """, (week_ago,))
            
            conn.commit()
            
        if deleted > 0:
            self.logger.info(f"Cleaned up {deleted} expired sessions")
        
        return deleted
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM sessions WHERE expires_at > ?
            """, (time.time(),))
            
            return cursor.fetchone()[0]
    
    def get_session_activity(self, session_id: str, limit: int = 100) -> List[Dict]:
        """Get activity log for a session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT action, ip_address, timestamp 
                FROM session_activity 
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _generate_csrf_token(self, session_id: str) -> str:
        """Generate a CSRF token for a session"""
        data = f"{session_id}:{time.time()}:{secrets.token_hex(16)}"
        return hashlib.sha256(data.encode()).hexdigest()


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create session manager
    manager = SessionManager(db_path="test_sessions.db")
    
    # Test synchronous operations
    print("\n=== Testing Synchronous Operations ===")
    
    # Create a session
    session = manager.create_session(
        user_data={'username': 'test_user', 'role': 'reviewer'},
        ip_address='127.0.0.1',
        user_agent='TestClient/1.0'
    )
    print(f"Created session: {session['session_id'][:8]}...")
    print(f"CSRF Token: {session['csrf_token'][:16]}...")
    
    # Validate session
    is_valid = manager.validate_session(
        session['session_id'], 
        session['csrf_token'],
        '127.0.0.1'
    )
    print(f"Session valid: {is_valid}")
    
    # Get session data
    data = manager.get_session_data(session['session_id'])
    print(f"Session data: {data}")
    
    # Update session data
    manager.update_session_data(
        session['session_id'],
        {'username': 'test_user', 'role': 'admin', 'decisions_made': 5}
    )
    
    # Get activity log
    activity = manager.get_session_activity(session['session_id'])
    print(f"Session activity: {activity}")
    
    # Get active sessions count
    count = manager.get_active_sessions_count()
    print(f"Active sessions: {count}")
    
    # Cleanup
    manager.cleanup_expired_sessions()
    
    # Test async operations
    async def test_async():
        print("\n=== Testing Async Operations ===")
        
        await manager.init_async_database()
        
        # Create async session
        async_session = await manager.create_session_async(
            user_data={'username': 'async_user'},
            ip_address='192.168.1.1'
        )
        print(f"Created async session: {async_session['session_id'][:8]}...")
        
        # Validate async session
        is_valid = await manager.validate_session_async(
            async_session['session_id'],
            async_session['csrf_token']
        )
        print(f"Async session valid: {is_valid}")
    
    # Run async tests
    asyncio.run(test_async())
    
    print("\n=== Session Manager Tests Complete ===")