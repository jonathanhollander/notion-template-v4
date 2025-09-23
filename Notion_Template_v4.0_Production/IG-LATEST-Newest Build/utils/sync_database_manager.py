#!/usr/bin/env python3
"""
Synchronous Database Manager for Estate Planning Concierge v4.0
Provides thread-safe connection pooling and synchronous database operations
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import threading
from queue import Queue
import time

class DatabasePool:
    """Thread-safe SQLite connection pool"""
    
    def __init__(self, db_path: str, pool_size: int = 10):
        """
        Initialize connection pool
        
        Args:
            db_path: Path to SQLite database
            pool_size: Maximum number of connections in pool
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Initialize the pool with connections
        for _ in range(pool_size):
            conn = self._create_connection()
            self.pool.put(conn)
        
        self.logger.info(f"Database pool initialized with {pool_size} connections")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimizations"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,  # Allow multi-threading
            timeout=30.0,  # 30 second timeout for locks
            isolation_level='DEFERRED'  # Better concurrency
        )
        
        # Enable optimizations
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
        conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes, still safe
        conn.execute("PRAGMA cache_size=10000")  # Larger cache
        conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
        
        # Enable row factory for dict-like access
        conn.row_factory = sqlite3.Row
        
        return conn
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            conn = self.pool.get(timeout=5)  # Wait up to 5 seconds
            yield conn
        finally:
            if conn:
                # Return connection to pool
                self.pool.put(conn)
    
    def close_all(self):
        """Close all connections in the pool"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except:
                pass
        self.logger.info("All database connections closed")


class SyncAssetDatabase:
    """Synchronous database operations with connection pooling"""
    
    def __init__(self, db_path: str = "asset_generation.db", pool_size: int = 10):
        """
        Initialize synchronous database manager
        
        Args:
            db_path: Path to SQLite database
            pool_size: Size of connection pool
        """
        self.db_path = db_path
        self.pool = DatabasePool(db_path, pool_size)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        with self.pool.get_connection() as conn:
            # Create tables if they don't exist
            conn.executescript("""
                -- Prompt competitions table
                CREATE TABLE IF NOT EXISTS prompt_competitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    base_prompt TEXT NOT NULL,
                    competition_status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Quality evaluations table
                CREATE TABLE IF NOT EXISTS quality_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competition_id INTEGER NOT NULL,
                    model_source TEXT NOT NULL,
                    prompt_text TEXT NOT NULL,
                    overall_score REAL,
                    weighted_score REAL,
                    evaluation_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (competition_id) REFERENCES prompt_competitions(id)
                );
                
                -- Human decisions table
                CREATE TABLE IF NOT EXISTS human_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competition_id INTEGER NOT NULL,
                    selected_prompt_text TEXT NOT NULL,
                    selected_model TEXT NOT NULL,
                    decision_reasoning TEXT,
                    quality_override REAL,
                    custom_modifications TEXT,
                    reviewer_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (competition_id) REFERENCES prompt_competitions(id)
                );
                
                -- Create indexes for performance
                CREATE INDEX IF NOT EXISTS idx_competitions_status 
                ON prompt_competitions(competition_status);
                
                CREATE INDEX IF NOT EXISTS idx_evaluations_competition 
                ON quality_evaluations(competition_id);
                
                CREATE INDEX IF NOT EXISTS idx_decisions_competition 
                ON human_decisions(competition_id);
            """)
            conn.commit()
    
    def get_competitions(self, status: Optional[str] = None) -> List[Dict]:
        """Get prompt competitions, optionally filtered by status"""
        with self.pool.get_connection() as conn:
            if status:
                cursor = conn.execute(
                    "SELECT * FROM prompt_competitions WHERE competition_status = ?",
                    (status,)
                )
            else:
                cursor = conn.execute("SELECT * FROM prompt_competitions")
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_competition_with_evaluations(self, competition_id: int) -> Dict:
        """Get competition details with all evaluations"""
        with self.pool.get_connection() as conn:
            # Get competition
            cursor = conn.execute(
                "SELECT * FROM prompt_competitions WHERE id = ?",
                (competition_id,)
            )
            competition = cursor.fetchone()
            
            if not competition:
                return None
            
            # Get evaluations
            cursor = conn.execute(
                "SELECT * FROM quality_evaluations WHERE competition_id = ?",
                (competition_id,)
            )
            evaluations = cursor.fetchall()
            
            # Get decision if exists
            cursor = conn.execute(
                "SELECT * FROM human_decisions WHERE competition_id = ?",
                (competition_id,)
            )
            decision = cursor.fetchone()
            
            return {
                'competition': dict(competition),
                'evaluations': [dict(e) for e in evaluations],
                'decision': dict(decision) if decision else None
            }
    
    def store_human_decision(self, decision_data: Dict) -> int:
        """Store a human decision for a competition"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO human_decisions 
                (competition_id, selected_prompt_text, selected_model, 
                 decision_reasoning, quality_override, custom_modifications, 
                 reviewer_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                decision_data['competition_id'],
                decision_data['selected_prompt_text'],
                decision_data['selected_model'],
                decision_data.get('decision_reasoning', ''),
                decision_data.get('quality_override'),
                decision_data.get('custom_modifications'),
                decision_data.get('reviewer_name', 'Anonymous')
            ))
            
            # Update competition status
            conn.execute("""
                UPDATE prompt_competitions 
                SET competition_status = 'decided', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (decision_data['competition_id'],))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_progress_stats(self) -> Dict:
        """Get review progress statistics"""
        with self.pool.get_connection() as conn:
            # Total evaluated competitions
            cursor = conn.execute("""
                SELECT COUNT(*) as total FROM prompt_competitions 
                WHERE competition_status = 'evaluated'
            """)
            total_evaluations = cursor.fetchone()['total']
            
            # Completed decisions
            cursor = conn.execute("""
                SELECT COUNT(*) as total FROM human_decisions
            """)
            decisions_made = cursor.fetchone()['total']
            
            # Pending reviews
            cursor = conn.execute("""
                SELECT COUNT(*) as total FROM prompt_competitions 
                WHERE competition_status = 'evaluated'
                AND id NOT IN (SELECT competition_id FROM human_decisions)
            """)
            pending_reviews = cursor.fetchone()['total']
            
            return {
                'total_evaluations': total_evaluations,
                'decisions_made': decisions_made,
                'pending_reviews': pending_reviews,
                'completion_percentage': (decisions_made / total_evaluations * 100) if total_evaluations > 0 else 0
            }
    
    def get_all_decisions(self) -> List[Dict]:
        """Get all human decisions with competition details"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT hd.*, pc.asset_type, pc.category, pc.base_prompt
                FROM human_decisions hd
                JOIN prompt_competitions pc ON hd.competition_id = pc.id
                ORDER BY hd.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data from database"""
        with self.pool.get_connection() as conn:
            cutoff_date = datetime.now().timestamp() - (days * 86400)
            
            # Delete old evaluations
            conn.execute("""
                DELETE FROM quality_evaluations 
                WHERE created_at < datetime(?, 'unixepoch')
            """, (cutoff_date,))
            
            # Delete old competitions without decisions
            conn.execute("""
                DELETE FROM prompt_competitions 
                WHERE created_at < datetime(?, 'unixepoch')
                AND id NOT IN (SELECT competition_id FROM human_decisions)
            """, (cutoff_date,))
            
            conn.commit()
            
            # Vacuum to reclaim space
            conn.execute("VACUUM")
    
    def init_database(self):
        """Alias for _init_database for backward compatibility"""
        return self._init_database()
    
    def close(self):
        """Close the database connection pool"""
        self.pool.close_all()


# Example usage
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create database manager with connection pool
    db = SyncAssetDatabase(pool_size=5)
    
    # Test operations
    print("Testing synchronous database operations...")
    
    # Get competitions
    competitions = db.get_competitions(status='evaluated')
    print(f"Found {len(competitions)} evaluated competitions")
    
    # Get progress stats
    stats = db.get_progress_stats()
    print(f"Progress stats: {stats}")
    
    # Simulate concurrent access
    import threading
    
    def worker(thread_id):
        for i in range(10):
            stats = db.get_progress_stats()
            print(f"Thread {thread_id} iteration {i}: {stats['decisions_made']} decisions")
            time.sleep(0.1)
    
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print("Concurrent access test complete")
    
    # Cleanup
    db.close()
    print("Database connections closed")