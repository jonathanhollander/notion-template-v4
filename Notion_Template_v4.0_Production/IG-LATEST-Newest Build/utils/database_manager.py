"""SQLite database manager for asset generation tracking.

This module provides comprehensive database functionality for tracking asset
generation, costs, retries, and analytics using SQLite with async support.
"""

import aiosqlite
import sqlite3
import hashlib
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

# Database schema
SCHEMA_SQL = """
-- Core asset tracking table
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_type TEXT NOT NULL,
    prompt TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    file_path TEXT,
    url TEXT,
    cost REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'completed', 'failed', 'cached')),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    model_id TEXT,
    run_id TEXT,
    batch_index INTEGER,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generation runs for batch tracking
CREATE TABLE IF NOT EXISTS generation_runs (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL CHECK(mode IN ('sample', 'production', 'test')),
    total_assets INTEGER,
    completed_assets INTEGER DEFAULT 0,
    failed_assets INTEGER DEFAULT 0,
    cached_assets INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0,
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    checkpoint JSON,
    error_log JSON
);

-- Financial transaction tracking
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER,
    amount REAL NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('charge', 'refund', 'credit')),
    status TEXT NOT NULL CHECK(status IN ('pending', 'completed', 'failed', 'rolled_back')),
    api_response JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- Retry log for failed generations
CREATE TABLE IF NOT EXISTS retry_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    retry_number INTEGER NOT NULL,
    strategy TEXT NOT NULL,
    error_message TEXT,
    success BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- Cache for prompt deduplication
CREATE TABLE IF NOT EXISTS prompt_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_hash TEXT UNIQUE NOT NULL,
    asset_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    quality_score REAL,
    use_count INTEGER DEFAULT 1,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily spending limits
CREATE TABLE IF NOT EXISTS spending_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    daily_limit REAL NOT NULL,
    spent REAL DEFAULT 0,
    remaining REAL GENERATED ALWAYS AS (daily_limit - spent) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_assets_prompt_hash ON assets(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
CREATE INDEX IF NOT EXISTS idx_assets_created_at ON assets(created_at);
CREATE INDEX IF NOT EXISTS idx_assets_run_id ON assets(run_id);
CREATE INDEX IF NOT EXISTS idx_assets_type_status ON assets(asset_type, status);
CREATE INDEX IF NOT EXISTS idx_cache_prompt_hash ON prompt_cache(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_transactions_asset_id ON transactions(asset_id);
CREATE INDEX IF NOT EXISTS idx_retry_asset_id ON retry_log(asset_id);

-- Triggers for updated_at
CREATE TRIGGER IF NOT EXISTS update_assets_timestamp 
AFTER UPDATE ON assets
BEGIN
    UPDATE assets SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Approval workflow tables
CREATE TABLE IF NOT EXISTS prompt_competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_prompt TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    category TEXT NOT NULL,
    index_in_category INTEGER,
    competition_status TEXT DEFAULT 'pending' CHECK(competition_status IN ('pending', 'evaluated', 'decided', 'completed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS competitive_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL REFERENCES prompt_competitions(id),
    model_source TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    generation_metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quality_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL REFERENCES competitive_prompts(id),
    scores JSON NOT NULL,
    overall_score REAL NOT NULL,
    weighted_score REAL NOT NULL,
    evaluator_model TEXT NOT NULL,
    evaluation_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS human_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL REFERENCES prompt_competitions(id),
    selected_prompt_id INTEGER NOT NULL REFERENCES competitive_prompts(id),
    reviewer_name TEXT,
    reasoning TEXT NOT NULL,
    custom_modifications TEXT,
    quality_override REAL,
    decision_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Approval workflow indexing
CREATE INDEX IF NOT EXISTS idx_competitive_prompts_competition ON competitive_prompts(competition_id);
CREATE INDEX IF NOT EXISTS idx_quality_evaluations_prompt ON quality_evaluations(prompt_id);
CREATE INDEX IF NOT EXISTS idx_human_decisions_competition ON human_decisions(competition_id);

-- Approval workflow triggers
CREATE TRIGGER IF NOT EXISTS update_competitions_timestamp 
AFTER UPDATE ON prompt_competitions
BEGIN
    UPDATE prompt_competitions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""


class AssetDatabase:
    """Async SQLite database manager for asset generation tracking.
    
    Provides comprehensive tracking of:
    - Asset generation attempts and results
    - Financial transactions and costs
    - Retry attempts and strategies
    - Cache management for deduplication
    - Analytics and reporting
    """
    
    def __init__(self, db_path: str = "assets.db", logger: Optional[logging.Logger] = None):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
            logger: Optional logger instance
        """
        self.db_path = Path(db_path)
        self.logger = logger or logging.getLogger(__name__)
        self._initialized = False
        
    @asynccontextmanager
    async def get_connection(self):
        """Get async database connection with row factory.
        
        Yields:
            Async database connection
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("PRAGMA journal_mode = WAL")  # Better concurrent access
            yield db
            
    async def initialize(self) -> None:
        """Create database schema if not exists."""
        if self._initialized:
            return
            
        self.logger.info(f"Initializing database at {self.db_path}")
        
        async with self.get_connection() as db:
            await db.executescript(SCHEMA_SQL)
            await db.commit()
            
        self._initialized = True
        self.logger.info("Database initialized successfully")
    
    # === Asset Management ===
    
    async def check_duplicate(self, prompt: str, asset_type: str) -> Optional[Dict[str, Any]]:
        """Check if this exact prompt was already generated.
        
        Args:
            prompt: Generation prompt
            asset_type: Type of asset (icons, covers, etc.)
            
        Returns:
            Asset data if found, None otherwise
        """
        prompt_hash = self._hash_prompt(prompt, asset_type)
        
        async with self.get_connection() as db:
            # Check cache first
            cursor = await db.execute(
                """SELECT pc.*, a.cost 
                   FROM prompt_cache pc
                   LEFT JOIN assets a ON a.prompt_hash = pc.prompt_hash
                   WHERE pc.prompt_hash = ? AND a.status = 'completed'
                   ORDER BY pc.last_used DESC LIMIT 1""",
                (prompt_hash,)
            )
            row = await cursor.fetchone()
            
            if row:
                # Update cache hit count
                await db.execute(
                    """UPDATE prompt_cache 
                       SET use_count = use_count + 1, 
                           last_used = CURRENT_TIMESTAMP
                       WHERE prompt_hash = ?""",
                    (prompt_hash,)
                )
                await db.commit()
                return dict(row)
                
            return None
    
    async def record_generation_attempt(
        self, 
        asset_type: str,
        prompt: str,
        cost: float,
        model_id: str,
        run_id: Optional[str] = None,
        batch_index: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """Record a new generation attempt.
        
        Args:
            asset_type: Type of asset
            prompt: Generation prompt
            cost: Estimated cost
            model_id: Model identifier
            run_id: Optional run ID for batch tracking
            batch_index: Optional index in batch
            metadata: Optional additional metadata
            
        Returns:
            Asset ID for tracking
        """
        prompt_hash = self._hash_prompt(prompt, asset_type)
        
        async with self.get_connection() as db:
            cursor = await db.execute(
                """INSERT INTO assets 
                   (asset_type, prompt, prompt_hash, cost, status, model_id, 
                    run_id, batch_index, metadata)
                   VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
                (asset_type, prompt, prompt_hash, cost, model_id,
                 run_id, batch_index, json.dumps(metadata) if metadata else None)
            )
            
            # Record transaction
            await db.execute(
                """INSERT INTO transactions (asset_id, amount, type, status)
                   VALUES (?, ?, 'charge', 'pending')""",
                (cursor.lastrowid, cost)
            )
            
            await db.commit()
            return cursor.lastrowid
    
    async def update_asset_status(
        self,
        asset_id: int,
        status: str,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        error_message: Optional[str] = None,
        actual_cost: Optional[float] = None
    ) -> None:
        """Update asset after generation attempt.
        
        Args:
            asset_id: Asset ID to update
            status: New status
            file_path: Path to saved file if successful
            url: URL of generated asset
            error_message: Error message if failed
            actual_cost: Actual cost if different from estimate
        """
        async with self.get_connection() as db:
            # Update asset
            await db.execute(
                """UPDATE assets 
                   SET status = ?, file_path = ?, url = ?, error_message = ?,
                       cost = COALESCE(?, cost)
                   WHERE id = ?""",
                (status, file_path, url, error_message, actual_cost, asset_id)
            )
            
            # Update transaction
            transaction_status = 'completed' if status == 'completed' else 'failed'
            await db.execute(
                """UPDATE transactions 
                   SET status = ?, amount = COALESCE(?, amount)
                   WHERE asset_id = ? AND type = 'charge'""",
                (transaction_status, actual_cost, asset_id)
            )
            
            # Add to cache if successful
            if status == 'completed' and file_path:
                asset = await self._get_asset(db, asset_id)
                if asset:
                    await self._add_to_cache(db, asset['prompt_hash'], 
                                           asset['asset_type'], file_path)
            
            # Update run statistics if part of a run
            cursor = await db.execute(
                "SELECT run_id FROM assets WHERE id = ?", (asset_id,)
            )
            row = await cursor.fetchone()
            if row and row['run_id']:
                await self._update_run_stats(db, row['run_id'])
            
            await db.commit()
    
    # === Progress Tracking ===
    
    async def create_generation_run(
        self,
        mode: str,
        total_assets: int
    ) -> str:
        """Create a new generation run for batch tracking.
        
        Args:
            mode: Generation mode (sample/production)
            total_assets: Total number of assets to generate
            
        Returns:
            Run ID for tracking
        """
        run_id = str(uuid.uuid4())
        
        async with self.get_connection() as db:
            await db.execute(
                """INSERT INTO generation_runs 
                   (id, mode, total_assets, status)
                   VALUES (?, ?, ?, 'pending')""",
                (run_id, mode, total_assets)
            )
            await db.commit()
            
        return run_id
    
    async def get_resume_point(self, run_id: str) -> Tuple[int, Dict[str, Any]]:
        """Find where to resume an interrupted run.
        
        Args:
            run_id: Run ID to resume
            
        Returns:
            Tuple of (last completed index, run info)
        """
        async with self.get_connection() as db:
            # Get run info
            cursor = await db.execute(
                "SELECT * FROM generation_runs WHERE id = ?", (run_id,)
            )
            run_info = await cursor.fetchone()
            if not run_info:
                return 0, {}
            
            # Get last completed index
            cursor = await db.execute(
                """SELECT MAX(batch_index) as last_index
                   FROM assets 
                   WHERE run_id = ? AND status = 'completed'""",
                (run_id,)
            )
            row = await cursor.fetchone()
            last_index = row['last_index'] if row and row['last_index'] else 0
            
            # Update run status
            await db.execute(
                """UPDATE generation_runs 
                   SET status = 'running', checkpoint = ?
                   WHERE id = ?""",
                (json.dumps({'last_index': last_index}), run_id)
            )
            await db.commit()
            
            return last_index, dict(run_info)
    
    async def checkpoint_progress(
        self,
        run_id: str,
        checkpoint_data: Dict[str, Any]
    ) -> None:
        """Save progress checkpoint for resuming.
        
        Args:
            run_id: Run ID
            checkpoint_data: Data to save for resuming
        """
        async with self.get_connection() as db:
            await db.execute(
                """UPDATE generation_runs 
                   SET checkpoint = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (json.dumps(checkpoint_data), run_id)
            )
            await db.commit()
    
    # === Financial Tracking ===
    
    async def get_daily_spend(self, date: Optional[datetime] = None) -> float:
        """Get spending for a specific day.
        
        Args:
            date: Date to check (default: today)
            
        Returns:
            Total spending for the day
        """
        if date is None:
            date = datetime.now()
            
        date_str = date.strftime('%Y-%m-%d')
        
        async with self.get_connection() as db:
            cursor = await db.execute(
                """SELECT COALESCE(SUM(amount), 0) as total
                   FROM transactions 
                   WHERE DATE(created_at) = DATE(?)
                   AND status = 'completed' AND type = 'charge'""",
                (date_str,)
            )
            row = await cursor.fetchone()
            return row['total'] if row else 0.0
    
    async def check_budget_available(
        self,
        amount: float,
        daily_limit: float
    ) -> Tuple[bool, float]:
        """Check if budget is available for a transaction.
        
        Args:
            amount: Amount to spend
            daily_limit: Daily spending limit
            
        Returns:
            Tuple of (can_afford, remaining_budget)
        """
        current_spend = await self.get_daily_spend()
        remaining = daily_limit - current_spend
        return amount <= remaining, remaining
    
    # === Retry Management ===
    
    async def record_retry_attempt(
        self,
        asset_id: int,
        strategy: str,
        error_message: Optional[str] = None,
        success: bool = False
    ) -> None:
        """Record a retry attempt for failed generation.
        
        Args:
            asset_id: Asset being retried
            strategy: Retry strategy used
            error_message: Error if retry failed
            success: Whether retry succeeded
        """
        async with self.get_connection() as db:
            # Get current retry count
            cursor = await db.execute(
                "SELECT retry_count FROM assets WHERE id = ?", (asset_id,)
            )
            row = await cursor.fetchone()
            retry_number = (row['retry_count'] if row else 0) + 1
            
            # Record retry
            await db.execute(
                """INSERT INTO retry_log 
                   (asset_id, retry_number, strategy, error_message, success)
                   VALUES (?, ?, ?, ?, ?)""",
                (asset_id, retry_number, strategy, error_message, success)
            )
            
            # Update asset retry count
            await db.execute(
                """UPDATE assets 
                   SET retry_count = ?, 
                       status = CASE WHEN ? THEN 'completed' ELSE status END
                   WHERE id = ?""",
                (retry_number, success, asset_id)
            )
            
            await db.commit()
    
    async def get_failed_assets_for_retry(
        self,
        max_retries: int = 3,
        hours_old: int = 24
    ) -> List[Dict[str, Any]]:
        """Get assets that should be retried.
        
        Args:
            max_retries: Maximum retry attempts
            hours_old: How old failures should be (hours)
            
        Returns:
            List of assets to retry
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        
        async with self.get_connection() as db:
            cursor = await db.execute(
                """SELECT a.*, 
                          (SELECT COUNT(*) FROM retry_log WHERE asset_id = a.id) as retry_attempts
                   FROM assets a
                   WHERE a.status = 'failed' 
                   AND a.retry_count < ?
                   AND a.created_at > ?
                   ORDER BY a.retry_count, a.created_at""",
                (max_retries, cutoff_time)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # === Analytics ===
    
    async def get_generation_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive generation statistics.
        
        Args:
            start_date: Start of period
            end_date: End of period
            
        Returns:
            Dictionary of statistics
        """
        conditions = []
        params = []
        
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)
            
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        async with self.get_connection() as db:
            # Overall stats
            cursor = await db.execute(f"""
                SELECT 
                    COUNT(*) as total_attempts,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN status = 'cached' THEN 1 END) as cached,
                    SUM(CASE WHEN status = 'completed' THEN cost ELSE 0 END) as total_cost,
                    AVG(CASE WHEN status = 'completed' THEN cost END) as avg_cost
                FROM assets {where_clause}
            """, params)
            overall = dict(await cursor.fetchone())
            
            # By asset type
            cursor = await db.execute(f"""
                SELECT 
                    asset_type,
                    COUNT(*) as count,
                    SUM(CASE WHEN status = 'completed' THEN cost ELSE 0 END) as cost,
                    AVG(CASE WHEN status = 'completed' THEN cost END) as avg_cost,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failures
                FROM assets {where_clause}
                GROUP BY asset_type
            """, params)
            by_type = {row['asset_type']: dict(row) for row in await cursor.fetchall()}
            
            # Daily breakdown
            cursor = await db.execute(f"""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as attempts,
                    SUM(CASE WHEN status = 'completed' THEN cost ELSE 0 END) as cost
                FROM assets {where_clause}
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 30
            """, params)
            daily = [dict(row) for row in await cursor.fetchall()]
            
            # Cache efficiency
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_cached,
                    SUM(use_count - 1) as cache_hits,
                    SUM((use_count - 1) * (
                        SELECT AVG(cost) FROM assets WHERE asset_type = pc.asset_type
                    )) as savings
                FROM prompt_cache pc
            """)
            cache_stats = dict(await cursor.fetchone())
            
            return {
                'overall': overall,
                'by_type': by_type,
                'daily': daily,
                'cache': cache_stats
            }
    
    async def find_duplicate_generations(self) -> List[Dict[str, Any]]:
        """Find prompts that were generated multiple times.
        
        Returns:
            List of duplicate generations with waste analysis
        """
        async with self.get_connection() as db:
            cursor = await db.execute("""
                SELECT 
                    prompt,
                    asset_type,
                    COUNT(*) as times_generated,
                    SUM(cost) as total_cost,
                    MIN(cost) as unit_cost,
                    (COUNT(*) - 1) * MIN(cost) as wasted_cost,
                    GROUP_CONCAT(file_path) as file_paths
                FROM assets
                WHERE status = 'completed'
                GROUP BY prompt_hash
                HAVING COUNT(*) > 1
                ORDER BY wasted_cost DESC
            """)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # === Utility Methods ===
    
    def _hash_prompt(self, prompt: str, asset_type: str) -> str:
        """Generate hash for prompt deduplication.
        
        Args:
            prompt: Generation prompt
            asset_type: Type of asset
            
        Returns:
            SHA256 hash of prompt
        """
        return hashlib.sha256(f"{asset_type}:{prompt}".encode()).hexdigest()
    
    async def _get_asset(self, db: aiosqlite.Connection, asset_id: int) -> Optional[Dict]:
        """Get asset by ID.
        
        Args:
            db: Database connection
            asset_id: Asset ID
            
        Returns:
            Asset data or None
        """
        cursor = await db.execute(
            "SELECT * FROM assets WHERE id = ?", (asset_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    
    async def _add_to_cache(
        self,
        db: aiosqlite.Connection,
        prompt_hash: str,
        asset_type: str,
        file_path: str
    ) -> None:
        """Add successful generation to cache.
        
        Args:
            db: Database connection
            prompt_hash: Hash of prompt
            asset_type: Type of asset
            file_path: Path to generated file
        """
        # Check if already in cache
        cursor = await db.execute(
            "SELECT id FROM prompt_cache WHERE prompt_hash = ?", (prompt_hash,)
        )
        if await cursor.fetchone():
            return
            
        # Add to cache
        file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
        await db.execute(
            """INSERT OR IGNORE INTO prompt_cache 
               (prompt_hash, asset_type, file_path, file_size)
               VALUES (?, ?, ?, ?)""",
            (prompt_hash, asset_type, file_path, file_size)
        )
    
    async def _update_run_stats(self, db: aiosqlite.Connection, run_id: str) -> None:
        """Update generation run statistics.
        
        Args:
            db: Database connection
            run_id: Run ID to update
        """
        cursor = await db.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'cached' THEN 1 END) as cached,
                SUM(CASE WHEN status = 'completed' THEN cost ELSE 0 END) as cost
            FROM assets
            WHERE run_id = ?
        """, (run_id,))
        
        stats = await cursor.fetchone()
        if stats:
            await db.execute("""
                UPDATE generation_runs
                SET completed_assets = ?,
                    failed_assets = ?,
                    cached_assets = ?,
                    total_cost = ?
                WHERE id = ?
            """, (stats['completed'], stats['failed'], 
                  stats['cached'], stats['cost'], run_id))
    
    # Approval workflow methods
    async def create_competition(
        self, base_prompt: str, asset_type: str, category: str, index: int
    ) -> int:
        """Create a new prompt competition."""
        async with self.get_connection() as db:
            cursor = await db.execute(
                """INSERT INTO prompt_competitions 
                   (base_prompt, asset_type, category, index_in_category)
                   VALUES (?, ?, ?, ?)""",
                (base_prompt, asset_type, category, index)
            )
            return cursor.lastrowid

    async def store_competitive_prompt(
        self, competition_id: int, model_source: str, prompt_text: str, metadata: Dict = None
    ) -> int:
        """Store a competitive prompt variation."""
        async with self.get_connection() as db:
            cursor = await db.execute(
                """INSERT INTO competitive_prompts 
                   (competition_id, model_source, prompt_text, generation_metadata)
                   VALUES (?, ?, ?, ?)""",
                (competition_id, model_source, prompt_text, json.dumps(metadata or {}))
            )
            return cursor.lastrowid

    async def store_quality_evaluation(
        self, prompt_id: int, scores: Dict, overall_score: float, 
        weighted_score: float, evaluator_model: str, summary: str = ""
    ) -> int:
        """Store quality evaluation for a competitive prompt."""
        async with self.get_connection() as db:
            cursor = await db.execute(
                """INSERT INTO quality_evaluations 
                   (prompt_id, scores, overall_score, weighted_score, evaluator_model, evaluation_summary)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (prompt_id, json.dumps(scores), overall_score, weighted_score, evaluator_model, summary)
            )
            return cursor.lastrowid

    async def store_human_decision(
        self, competition_id: int, selected_prompt_id: int, reviewer_name: str,
        reasoning: str, custom_modifications: str = None, quality_override: float = None
    ) -> int:
        """Store human decision for a competition."""
        async with self.get_connection() as db:
            cursor = await db.execute(
                """INSERT INTO human_decisions 
                   (competition_id, selected_prompt_id, reviewer_name, reasoning, 
                    custom_modifications, quality_override)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (competition_id, selected_prompt_id, reviewer_name, reasoning, 
                 custom_modifications, quality_override)
            )
            
            # Update competition status
            await db.execute(
                "UPDATE prompt_competitions SET competition_status = 'decided' WHERE id = ?",
                (competition_id,)
            )
            return cursor.lastrowid

    async def get_pending_competitions(self) -> List[Dict]:
        """Get all competitions pending human review."""
        async with self.get_connection() as db:
            cursor = await db.execute(
                """SELECT * FROM prompt_competitions 
                   WHERE competition_status = 'evaluated'
                   ORDER BY created_at"""
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_competitive_prompts(self, competition_id: int) -> List[Dict]:
        """Get all competitive prompts for a competition."""
        async with self.get_connection() as db:
            cursor = await db.execute(
                """SELECT cp.*, qe.overall_score, qe.weighted_score, qe.evaluation_summary
                   FROM competitive_prompts cp
                   LEFT JOIN quality_evaluations qe ON cp.id = qe.prompt_id
                   WHERE cp.competition_id = ?
                   ORDER BY qe.weighted_score DESC""",
                (competition_id,)
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_competition_evaluations(self, competition_id: int) -> Dict:
        """Get complete evaluation data for a competition."""
        async with self.get_connection() as db:
            # Get competition info
            cursor = await db.execute(
                "SELECT * FROM prompt_competitions WHERE id = ?", (competition_id,)
            )
            competition = dict(await cursor.fetchone())
            
            # Get competitive prompts with evaluations
            prompts = await self.get_competitive_prompts(competition_id)
            
            # Find winner (highest weighted score)
            winner = max(prompts, key=lambda p: p.get('weighted_score', 0)) if prompts else None
            
            return {
                'competition': competition,
                'prompts': prompts,
                'winner': winner,
                'page_title': f"{competition['asset_type']} {competition['index_in_category']}",
                'page_category': competition['category'],
                'asset_type': competition['asset_type']
            }

    async def get_approved_prompts(self) -> List[Dict]:
        """Get all human-approved prompts ready for generation."""
        async with self.get_connection() as db:
            cursor = await db.execute(
                """SELECT 
                     hd.*,
                     pc.asset_type,
                     pc.category,
                     pc.index_in_category,
                     cp.prompt_text as selected_prompt_text,
                     cp.model_source as selected_model
                   FROM human_decisions hd
                   JOIN prompt_competitions pc ON hd.competition_id = pc.id
                   JOIN competitive_prompts cp ON hd.selected_prompt_id = cp.id
                   WHERE pc.competition_status = 'decided'
                   ORDER BY pc.asset_type, pc.index_in_category"""
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def mark_competition_completed(self, competition_id: int) -> None:
        """Mark a competition as completed after asset generation."""
        async with self.get_connection() as db:
            await db.execute(
                "UPDATE prompt_competitions SET competition_status = 'completed' WHERE id = ?",
                (competition_id,)
            )

    async def close(self) -> None:
        """Close database connections and cleanup."""
        # SQLite handles connection cleanup automatically
        self.logger.info("Database manager closed")


# Convenience function for creating database
async def create_database(db_path: str = "assets.db") -> AssetDatabase:
    """Create and initialize database.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Initialized AssetDatabase instance
    """
    db = AssetDatabase(db_path)
    await db.initialize()
    return db