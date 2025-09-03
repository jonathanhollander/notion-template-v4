# Asset Generator v2 - Audit Fixes for Future Implementation

**Status**: NOT NEEDED FOR LOCAL POC  
**Context**: These fixes were identified by multi-model AI audit but are only necessary for production deployment at scale, not for local proof-of-concept testing.

**For Local POC**: Only fix #1 (secrets) if you care about security. Everything else works fine as-is.

---

## Critical Fixes (Production Only)

### 1. Fix Secrets Management ⚠️ 
**File**: `asset_generator_v2.py`  
**Issue**: API keys get written to config files  
**Risk**: High security risk if config committed to git

```python
# In _load_config(), change this:
'replicate': {
    'api_key': os.getenv('REPLICATE_API_TOKEN'),  # DON'T WRITE TO FILE
}

# To this:
'replicate': {
    'api_key': '',  # Empty in template
}

# And always load from environment:
api_key = self.config.get('replicate', {}).get('api_key') or os.getenv('REPLICATE_API_TOKEN')
```

### 2. Implement Atomic Checkpoints
**File**: `utils/progress_tracker.py`  
**Issue**: Race conditions in checkpoint saving  
**Fix**:
```python
async def _save_checkpoint(self, state: Dict[str, Any]):
    temp_file = self.checkpoint_file.with_suffix('.json.tmp')
    
    # Write to temp file first
    async with aiofiles.open(temp_file, 'w') as f:
        await f.write(json.dumps(state, indent=2))
    
    # Atomic rename (POSIX compliant)
    os.rename(temp_file, self.checkpoint_file)
```

### 3. Add Resource Cleanup
**File**: Create new `services/replicate_client.py`  
**Issue**: HTTP sessions not properly closed  
**Fix**:
```python
import aiohttp
import asyncio
import replicate

class ReplicateClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
        self.client = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.client = replicate.Client(api_token=self.api_key)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Same logic as current ReplicateClient.generate()
        # but using self.client instead of creating new one
        pass

# Usage in asset_generator_v2.py:
async def main():
    generator = EnhancedAssetGenerator(args.config)
    async with generator:  # This would require making EnhancedAssetGenerator a context manager too
        await generator.initialize()
        # ... rest of logic
```

### 4. Input Validation & Sanitization
**File**: Create new `utils/input_validator.py`  
**Issue**: No input sanitization  
**Fix**:
```python
import re
import os
from pathlib import Path

def sanitize_prompt(prompt: str) -> str:
    """Remove dangerous characters and limit length."""
    if not prompt:
        return ""
    
    # Remove potentially dangerous characters
    cleaned = re.sub(r'[<>"\';\\]', '', prompt)
    
    # Limit length
    cleaned = cleaned.strip()[:2000]
    
    return cleaned

def validate_file_path(path: str, base_dir: str = ".") -> str:
    """Prevent directory traversal attacks."""
    # Normalize the path
    safe_path = os.path.normpath(path)
    
    # Check for directory traversal
    if '..' in safe_path or safe_path.startswith('/') or safe_path.startswith('\\'):
        raise ValueError(f"Invalid path: {path}")
    
    # Ensure it's within base directory
    full_path = os.path.join(base_dir, safe_path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
        raise ValueError(f"Path outside base directory: {path}")
    
    return safe_path

# Usage in services/asset_service.py:
async def generate_asset(self, request: AssetRequest) -> AssetResponse:
    # Sanitize inputs
    request.prompt = sanitize_prompt(request.prompt)
    
    # ... rest of logic
```

---

## High Priority Fixes (Scale Only)

### 5. Refactor Constructor with Factory Pattern
**File**: Create new `factory/generator_factory.py`  
**Issue**: Constructor too complex, hard to test  
**Fix**:
```python
from typing import Optional
import asyncio

class AssetGeneratorFactory:
    @classmethod
    async def create(
        cls, 
        config_path: str = "config.json",
        db_manager: Optional[DatabaseManager] = None,
        api_client: Optional = None
    ) -> EnhancedAssetGenerator:
        """Create properly initialized AssetGenerator."""
        
        # Load configuration
        config = SecureConfig.load(config_path)
        
        # Create services with dependency injection
        if not db_manager:
            db_manager = await DatabaseManager.create(config.database)
        
        if not api_client:
            api_client = await ReplicateClient.create(config.replicate)
        
        # Create logger
        logger = setup_logging(
            log_level=config.logging.log_level,
            log_file=config.logging.log_file,
            json_logs=config.logging.json_logs
        )
        
        # Create generator with dependency injection
        generator = EnhancedAssetGenerator.__new__(EnhancedAssetGenerator)
        generator._initialize(config, db_manager, api_client, logger)
        
        return generator

# Modified EnhancedAssetGenerator.__init__():
def _initialize(self, config, db_manager, api_client, logger):
    """Initialize with injected dependencies."""
    self.config = config
    self.db_manager = db_manager
    self.api_client = api_client
    self.logger = logger
    
    # Create services
    self.asset_service = AssetGenerationService(
        api_client=self.api_client,
        db_manager=self.db_manager,
        # ... other params
    )
    
    # ... rest of initialization
```

### 6. Database Connection Pool
**File**: `utils/database_manager.py`  
**Issue**: No connection pooling for concurrent operations  
**Fix**:
```python
import aiosqlite
import asyncio
from contextlib import asynccontextmanager

class DatabaseManager:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool = asyncio.Queue(maxsize=pool_size)
        self._initialized = False
    
    async def initialize(self):
        """Initialize connection pool."""
        if self._initialized:
            return
        
        # Create pool of connections
        for _ in range(self.pool_size):
            conn = await aiosqlite.connect(self.db_path, check_same_thread=False)
            await self.pool.put(conn)
        
        self._initialized = True
    
    @asynccontextmanager
    async def get_connection(self):
        """Get connection from pool."""
        conn = await self.pool.get()
        try:
            yield conn
        finally:
            await self.pool.put(conn)
    
    async def cleanup(self):
        """Close all connections in pool."""
        while not self.pool.empty():
            conn = await self.pool.get()
            await conn.close()

# Usage throughout the class:
async def record_generation_attempt(self, ...):
    async with self.get_connection() as conn:
        # Use conn instead of self.conn
        pass
```

### 7. Externalize Configuration
**File**: Create new `config/retry_config.yaml`  
**Issue**: Retry logic hardcoded  
**Fix**:
```yaml
# config/retry_config.yaml
retry_strategies:
  error_patterns:
    server_error: 
      patterns: ["server.*error", "500", "502", "503", "504"]
      strategies: [delayed_retry, immediate_retry]
      max_attempts: 3
    
    rate_limit:
      patterns: ["rate.?limit", "429", "quota.*exceeded"]
      strategies: [exponential_backoff]
      max_attempts: 5
    
    content_policy:
      patterns: ["content.?policy", "inappropriate", "blocked"]
      strategies: [simplified_prompt, generic_fallback]
      max_attempts: 2

model_fallbacks:
  flux-dev:
    fallbacks: [flux-schnell, stable-diffusion-xl-base-1.0]
    cost_multiplier: 0.1  # flux-schnell is 10x cheaper
  
  flux-schnell:
    fallbacks: [stable-diffusion-xl-base-1.0]
    cost_multiplier: 10.0  # sdxl is 10x more expensive

parameters:
  max_total_retries: 5
  base_delay_seconds: 1.0
  max_delay_seconds: 60.0
  exponential_base: 2.0
  jitter_factor: 0.1

generic_prompts:
  - "Professional estate planning document design"
  - "Clean modern financial planning layout"
  - "Elegant legal document template"
  - "Minimalist business document design"
```

```python
# Modified smart_retry.py to load from config:
import yaml
from pathlib import Path

class SmartRetryManager:
    def __init__(self, db_manager: DatabaseManager, config_path: str = "config/retry_config.yaml"):
        self.db = db_manager
        self.config = self._load_retry_config(config_path)
        self.error_strategies = self._build_error_strategies()
        # ... rest of init
    
    def _load_retry_config(self, config_path: str) -> dict:
        """Load retry configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback to hardcoded config
            return self._get_default_config()
    
    def _build_error_strategies(self) -> dict:
        """Build error pattern to strategy mapping from config."""
        strategies = {}
        for error_type, config in self.config['retry_strategies']['error_patterns'].items():
            for pattern in config['patterns']:
                strategies[pattern] = [
                    RetryStrategy[s.upper()] for s in config['strategies']
                ]
        return strategies
```

### 8. Circuit Breaker Persistence
**File**: `utils/smart_retry.py`, `utils/database_manager.py`  
**Issue**: Circuit breaker state lost on restart  
**Fix**:
```python
# Add to database_manager.py:
async def get_circuit_breaker_state(self, service_name: str) -> dict:
    """Get circuit breaker state from database."""
    async with self.get_connection() as conn:
        cursor = await conn.execute(
            "SELECT state, failure_count, last_failure, next_attempt FROM circuit_breakers WHERE service_name = ?",
            (service_name,)
        )
        row = await cursor.fetchone()
        
        if row:
            return {
                'state': row[0],
                'failure_count': row[1],
                'last_failure': row[2],
                'next_attempt': row[3]
            }
        return {'state': 'closed', 'failure_count': 0, 'last_failure': None, 'next_attempt': None}

async def set_circuit_breaker_state(self, service_name: str, state: dict):
    """Save circuit breaker state to database."""
    async with self.get_connection() as conn:
        await conn.execute("""
            INSERT OR REPLACE INTO circuit_breakers 
            (service_name, state, failure_count, last_failure, next_attempt)
            VALUES (?, ?, ?, ?, ?)
        """, (service_name, state['state'], state['failure_count'], 
              state['last_failure'], state['next_attempt']))
        await conn.commit()

# Modified CircuitBreaker class:
class CircuitBreaker:
    def __init__(self, db_manager: DatabaseManager, service_name: str, failure_threshold: int = 5):
        self.db = db_manager
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self._state_cache = None
    
    async def _get_state(self) -> dict:
        """Get current state from database."""
        if not self._state_cache:
            self._state_cache = await self.db.get_circuit_breaker_state(self.service_name)
        return self._state_cache
    
    async def _save_state(self, state: dict):
        """Save state to database."""
        self._state_cache = state
        await self.db.set_circuit_breaker_state(self.service_name, state)
```

---

## Performance Optimizations (Nice-to-Have)

### 9. Optimize Checkpoint Storage
**File**: `utils/progress_tracker.py`  
**Issue**: Memory usage grows with checkpoint count  
**Fix**:
```python
class ProgressTracker:
    def __init__(self, ...):
        # Remove the checkpoints list
        # self.checkpoints = []  # DELETE THIS
        self.latest_checkpoint = None  # Single checkpoint instead
    
    async def checkpoint(self, ...):
        # Don't append to list
        checkpoint = Checkpoint(...)
        self.latest_checkpoint = checkpoint  # Store only latest
        
        # Save to file as before
        await self._save_checkpoint(...)
    
    def get_progress(self) -> dict:
        # Use latest_checkpoint instead of self.checkpoints[-1]
        if not self.latest_checkpoint:
            # Load from file if not in memory
            self.latest_checkpoint = await self._load_latest_checkpoint()
        
        return {
            # ... build progress from latest_checkpoint
        }
```

### 10. Database Indexing
**File**: `utils/database_manager.py`  
**Issue**: Slow queries on large datasets  
**Fix**:
```python
# Add to schema creation:
CREATE_TABLES = [
    # ... existing tables ...
    
    # New run metadata table with indexes
    """
    CREATE TABLE IF NOT EXISTS run_metadata (
        run_id TEXT PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL,
        completed_count INTEGER DEFAULT 0,
        total_count INTEGER DEFAULT 0,
        progress_percentage REAL DEFAULT 0.0,
        estimated_cost REAL DEFAULT 0.0,
        actual_cost REAL DEFAULT 0.0
    )
    """,
    
    # Performance indexes
    "CREATE INDEX IF NOT EXISTS idx_run_status ON run_metadata(status, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_run_progress ON run_metadata(progress_percentage, updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_generation_attempts_run ON generation_attempts(run_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_spending_daily ON daily_spending(date DESC)",
]

# Fast resumable runs query:
async def list_resumable_runs_fast(self) -> List[dict]:
    """Fast database-based resumable runs query."""
    async with self.get_connection() as conn:
        cursor = await conn.execute("""
            SELECT run_id, completed_count, total_count, progress_percentage,
                   (julianday('now') - julianday(updated_at)) * 24 as age_hours
            FROM run_metadata 
            WHERE status IN ('running', 'paused') 
              AND progress_percentage < 100
            ORDER BY updated_at DESC
            LIMIT 10
        """)
        
        runs = []
        async for row in cursor:
            runs.append({
                'run_id': row[0],
                'completed': row[1],
                'total': row[2],
                'progress_percentage': row[3],
                'age_hours': row[4]
            })
        
        return runs
```

### 11. Structured Error Handling
**File**: Create new `utils/error_classifier.py`  
**Issue**: Brittle regex-based error parsing  
**Fix**:
```python
from enum import Enum
from typing import Optional
import re

class ErrorType(Enum):
    SERVER_ERROR = "server_error"
    RATE_LIMIT = "rate_limit" 
    CONTENT_POLICY = "content_policy"
    AUTHENTICATION = "authentication"
    QUOTA_EXCEEDED = "quota_exceeded"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"

class ErrorClassifier:
    """Classify errors using structured approach."""
    
    def __init__(self):
        # HTTP status code mappings
        self.status_mappings = {
            401: ErrorType.AUTHENTICATION,
            403: ErrorType.CONTENT_POLICY,
            429: ErrorType.RATE_LIMIT,
            500: ErrorType.SERVER_ERROR,
            502: ErrorType.SERVER_ERROR,
            503: ErrorType.SERVER_ERROR,
            504: ErrorType.SERVER_ERROR,
        }
        
        # API-specific error code mappings (if available)
        self.error_code_mappings = {
            'rate_limit_exceeded': ErrorType.RATE_LIMIT,
            'content_policy_violation': ErrorType.CONTENT_POLICY,
            'quota_exceeded': ErrorType.QUOTA_EXCEEDED,
            'server_overloaded': ErrorType.SERVER_ERROR,
        }
    
    def classify_error(self, error: Exception, response_data: Optional[dict] = None) -> ErrorType:
        """Classify error using multiple signals."""
        
        # 1. Check HTTP status code if available
        if hasattr(error, 'status_code'):
            error_type = self.status_mappings.get(error.status_code)
            if error_type:
                return error_type
        
        # 2. Check structured error response if available
        if response_data and 'error' in response_data:
            error_code = response_data['error'].get('code')
            error_type = self.error_code_mappings.get(error_code)
            if error_type:
                return error_type
        
        # 3. Fall back to message pattern matching (last resort)
        error_message = str(error).lower()
        
        if any(pattern in error_message for pattern in ['rate limit', '429', 'quota']):
            return ErrorType.RATE_LIMIT
        elif any(pattern in error_message for pattern in ['server error', '500', '502', '503']):
            return ErrorType.SERVER_ERROR
        elif any(pattern in error_message for pattern in ['content policy', 'inappropriate', 'blocked']):
            return ErrorType.CONTENT_POLICY
        elif any(pattern in error_message for pattern in ['auth', 'token', 'unauthorized']):
            return ErrorType.AUTHENTICATION
        elif any(pattern in error_message for pattern in ['network', 'connection', 'timeout']):
            return ErrorType.NETWORK_ERROR
        
        return ErrorType.UNKNOWN
```

### 12. Enhanced Logging & Metrics
**File**: Create new `monitoring/metrics.py`  
**Issue**: Limited observability  
**Fix**:
```python
import time
import json
from typing import Dict, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta

class MetricsCollector:
    """Collect and export metrics for monitoring."""
    
    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.metrics = defaultdict(int)
        self.timing_metrics = defaultdict(list)
        self.rate_metrics = defaultdict(lambda: deque())
        
    def increment(self, metric_name: str, value: int = 1):
        """Increment a counter metric."""
        self.metrics[metric_name] += value
    
    def record_timing(self, metric_name: str, duration_seconds: float):
        """Record timing metric."""
        self.timing_metrics[metric_name].append(duration_seconds)
        
        # Keep only recent timings
        cutoff = len(self.timing_metrics[metric_name]) - 1000
        if cutoff > 0:
            self.timing_metrics[metric_name] = self.timing_metrics[metric_name][cutoff:]
    
    def record_rate_event(self, metric_name: str):
        """Record an event for rate calculation."""
        now = datetime.now()
        self.rate_metrics[metric_name].append(now)
        
        # Remove old events outside window
        cutoff = now - timedelta(minutes=self.window_minutes)
        while self.rate_metrics[metric_name] and self.rate_metrics[metric_name][0] < cutoff:
            self.rate_metrics[metric_name].popleft()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        summary = {
            'counters': dict(self.metrics),
            'rates': {},
            'timings': {}
        }
        
        # Calculate rates (events per minute)
        for metric, events in self.rate_metrics.items():
            rate = len(events) / self.window_minutes if events else 0
            summary['rates'][f"{metric}_per_minute"] = round(rate, 2)
        
        # Calculate timing statistics
        for metric, timings in self.timing_metrics.items():
            if timings:
                summary['timings'][metric] = {
                    'avg': round(sum(timings) / len(timings), 3),
                    'min': round(min(timings), 3),
                    'max': round(max(timings), 3),
                    'count': len(timings)
                }
        
        return summary
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # Counter metrics
        for metric, value in self.metrics.items():
            lines.append(f"# TYPE {metric} counter")
            lines.append(f"{metric} {value}")
        
        # Rate metrics  
        for metric, events in self.rate_metrics.items():
            rate = len(events) / self.window_minutes if events else 0
            lines.append(f"# TYPE {metric}_rate gauge") 
            lines.append(f"{metric}_rate {rate}")
        
        # Timing metrics
        for metric, timings in self.timing_metrics.items():
            if timings:
                avg = sum(timings) / len(timings)
                lines.append(f"# TYPE {metric}_duration_avg gauge")
                lines.append(f"{metric}_duration_avg {avg}")
        
        return '\n'.join(lines)

# Usage in asset_service.py:
class AssetGenerationService:
    def __init__(self, ...):
        # ... existing init ...
        self.metrics = MetricsCollector()
    
    async def generate_asset(self, request: AssetRequest) -> AssetResponse:
        start_time = time.time()
        self.metrics.record_rate_event('api_requests')
        
        try:
            # ... existing logic ...
            
            if response.cached:
                self.metrics.increment('cache_hits')
            else:
                self.metrics.increment('api_calls')
                self.metrics.record_timing('generation_duration', response.generation_time)
            
            return response
            
        except Exception as e:
            self.metrics.increment('errors')
            raise
        finally:
            total_time = time.time() - start_time
            self.metrics.record_timing('total_request_duration', total_time)
```

---

## Summary

**For Local POC**: Just fix the secrets issue (#1) and you're good to go.

**For Production**: Implement fixes in order of priority based on actual needs:
- Critical fixes before any production deployment
- High priority fixes before scaling beyond single instance
- Performance optimizations when you hit actual bottlenecks

Most of these "critical" issues only matter at scale or in multi-user production environments.