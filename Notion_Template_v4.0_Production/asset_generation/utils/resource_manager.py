"""Resource management with context managers for proper cleanup."""

import asyncio
import aiohttp
import aiofiles
from contextlib import asynccontextmanager, contextmanager
from typing import Optional, Any, AsyncIterator, Iterator, Dict
import logging
from pathlib import Path
import tempfile
import shutil
import atexit


class ResourceManager:
    """Manages resources with proper cleanup and context managers."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize resource manager.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.active_sessions: Dict[str, aiohttp.ClientSession] = {}
        self.temp_dirs: list = []
        self.open_files: list = []
        
        # Register cleanup on exit
        atexit.register(self.cleanup_all)
    
    @asynccontextmanager
    async def http_session(
        self,
        timeout: int = 30,
        connector_limit: int = 10
    ) -> AsyncIterator[aiohttp.ClientSession]:
        """Create and manage HTTP session with proper cleanup.
        
        Args:
            timeout: Request timeout in seconds
            connector_limit: Maximum number of connections
            
        Yields:
            Configured aiohttp ClientSession
        """
        session = None
        try:
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            connector = aiohttp.TCPConnector(limit=connector_limit)
            
            session = aiohttp.ClientSession(
                timeout=timeout_config,
                connector=connector
            )
            
            session_id = str(id(session))
            self.active_sessions[session_id] = session
            self.logger.debug(f"Created HTTP session {session_id}")
            
            yield session
            
        finally:
            if session:
                session_id = str(id(session))
                await session.close()
                # Wait for connector to close properly
                await asyncio.sleep(0.25)
                
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                    
                self.logger.debug(f"Closed HTTP session {session_id}")
    
    @asynccontextmanager
    async def async_file(
        self,
        filepath: Path,
        mode: str = 'r',
        encoding: Optional[str] = 'utf-8'
    ) -> AsyncIterator[Any]:
        """Open file asynchronously with proper cleanup.
        
        Args:
            filepath: Path to file
            mode: File open mode
            encoding: Text encoding (None for binary)
            
        Yields:
            Async file handle
        """
        file_handle = None
        try:
            if 'b' in mode:
                file_handle = await aiofiles.open(filepath, mode)
            else:
                file_handle = await aiofiles.open(filepath, mode, encoding=encoding)
            
            self.open_files.append(str(filepath))
            self.logger.debug(f"Opened file: {filepath}")
            
            yield file_handle
            
        finally:
            if file_handle:
                await file_handle.close()
                
                filepath_str = str(filepath)
                if filepath_str in self.open_files:
                    self.open_files.remove(filepath_str)
                    
                self.logger.debug(f"Closed file: {filepath}")
    
    @contextmanager
    def temp_directory(
        self,
        prefix: str = "asset_gen_",
        cleanup: bool = True
    ) -> Iterator[Path]:
        """Create temporary directory with automatic cleanup.
        
        Args:
            prefix: Directory name prefix
            cleanup: Whether to cleanup on exit
            
        Yields:
            Path to temporary directory
        """
        temp_dir = None
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
            self.temp_dirs.append(temp_dir)
            self.logger.debug(f"Created temp directory: {temp_dir}")
            
            yield temp_dir
            
        finally:
            if temp_dir and cleanup and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    if temp_dir in self.temp_dirs:
                        self.temp_dirs.remove(temp_dir)
                    self.logger.debug(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")
    
    @asynccontextmanager
    async def connection_pool(
        self,
        size: int = 5,
        timeout: int = 30
    ) -> AsyncIterator[list]:
        """Create a pool of HTTP sessions for parallel requests.
        
        Args:
            size: Number of sessions in pool
            timeout: Request timeout
            
        Yields:
            List of HTTP sessions
        """
        sessions = []
        try:
            for _ in range(size):
                timeout_config = aiohttp.ClientTimeout(total=timeout)
                session = aiohttp.ClientSession(timeout=timeout_config)
                sessions.append(session)
                self.active_sessions[str(id(session))] = session
            
            self.logger.debug(f"Created connection pool with {size} sessions")
            yield sessions
            
        finally:
            for session in sessions:
                session_id = str(id(session))
                await session.close()
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
            
            # Wait for all connections to close
            await asyncio.sleep(0.5)
            self.logger.debug(f"Closed connection pool with {len(sessions)} sessions")
    
    @asynccontextmanager
    async def rate_limiter(
        self,
        rate: float = 1.0,
        burst: int = 1
    ) -> AsyncIterator['RateLimiter']:
        """Create rate limiter for API calls.
        
        Args:
            rate: Requests per second
            burst: Burst capacity
            
        Yields:
            RateLimiter instance
        """
        limiter = RateLimiter(rate, burst, self.logger)
        try:
            yield limiter
        finally:
            # No cleanup needed for rate limiter
            pass
    
    async def cleanup_sessions(self):
        """Clean up all active HTTP sessions."""
        if self.active_sessions:
            self.logger.info(f"Cleaning up {len(self.active_sessions)} active sessions")
            
            for session_id, session in list(self.active_sessions.items()):
                try:
                    await session.close()
                    del self.active_sessions[session_id]
                except Exception as e:
                    self.logger.warning(f"Error closing session {session_id}: {e}")
            
            # Wait for connections to close
            await asyncio.sleep(0.5)
    
    def cleanup_temp_dirs(self):
        """Clean up all temporary directories."""
        if self.temp_dirs:
            self.logger.info(f"Cleaning up {len(self.temp_dirs)} temporary directories")
            
            for temp_dir in list(self.temp_dirs):
                try:
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
                    self.temp_dirs.remove(temp_dir)
                except Exception as e:
                    self.logger.warning(f"Error cleaning up {temp_dir}: {e}")
    
    def cleanup_all(self):
        """Clean up all resources (called on exit)."""
        # Clean up temp directories synchronously
        self.cleanup_temp_dirs()
        
        # Clean up sessions if event loop is available
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.run_until_complete(self.cleanup_sessions())
        except RuntimeError:
            # No event loop available, sessions will be garbage collected
            pass
        
        if self.open_files:
            self.logger.warning(f"Warning: {len(self.open_files)} files may not have been closed properly")


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, rate: float, burst: int, logger: Optional[logging.Logger] = None):
        """Initialize rate limiter.
        
        Args:
            rate: Requests per second
            burst: Burst capacity
            logger: Logger instance
        """
        self.rate = rate
        self.burst = burst
        self.logger = logger or logging.getLogger(__name__)
        self.tokens = burst
        self.last_update = asyncio.get_event_loop().time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request."""
        async with self.lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_update
            
            # Refill tokens based on elapsed time
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            # Wait if no tokens available
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                self.logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 1
                self.last_update = asyncio.get_event_loop().time()
            
            # Consume a token
            self.tokens -= 1
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


class ConnectionPoolManager:
    """Manages a pool of connections for parallel operations."""
    
    def __init__(
        self,
        size: int = 5,
        timeout: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize connection pool manager.
        
        Args:
            size: Pool size
            timeout: Connection timeout
            logger: Logger instance
        """
        self.size = size
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        self.pool: list = []
        self.available: asyncio.Queue = asyncio.Queue()
        self.initialized = False
    
    async def initialize(self):
        """Initialize the connection pool."""
        if self.initialized:
            return
        
        for i in range(self.size):
            timeout_config = aiohttp.ClientTimeout(total=self.timeout)
            session = aiohttp.ClientSession(timeout=timeout_config)
            self.pool.append(session)
            await self.available.put(session)
        
        self.initialized = True
        self.logger.info(f"Initialized connection pool with {self.size} connections")
    
    async def acquire(self) -> aiohttp.ClientSession:
        """Acquire a connection from the pool.
        
        Returns:
            Available session
        """
        if not self.initialized:
            await self.initialize()
        
        session = await self.available.get()
        return session
    
    async def release(self, session: aiohttp.ClientSession):
        """Release a connection back to the pool.
        
        Args:
            session: Session to release
        """
        if session in self.pool:
            await self.available.put(session)
    
    async def close(self):
        """Close all connections in the pool."""
        for session in self.pool:
            await session.close()
        
        # Wait for connections to close
        await asyncio.sleep(0.5)
        
        self.pool.clear()
        self.initialized = False
        self.logger.info("Closed connection pool")
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()


def create_resource_manager(logger: Optional[logging.Logger] = None) -> ResourceManager:
    """Create and configure a resource manager.
    
    Args:
        logger: Logger instance
        
    Returns:
        Configured ResourceManager
    """
    return ResourceManager(logger)