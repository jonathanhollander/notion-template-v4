"""Asset caching manager with database integration.

Prevents costly regeneration of identical prompts by checking cache before
generating new assets. Integrates with SQLite database for persistent storage.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import json
import aiofiles
import asyncio
from contextlib import asynccontextmanager

from .database_manager import DatabaseManager
from .async_file_handler import AsyncFileHandler
from .path_validator import PathValidator

logger = logging.getLogger(__name__)


class AssetCache:
    """Intelligent caching system for generated assets.
    
    Features:
        - Prompt deduplication using SHA256 hashing
        - Database-backed persistent cache
        - File existence validation
        - Cache expiration management
        - Memory-efficient streaming for large files
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        cache_dir: Path = Path("cache/assets"),
        max_cache_age_days: int = 30
    ):
        """Initialize asset cache manager.
        
        Args:
            db_manager: Database manager instance
            cache_dir: Directory for cached assets
            max_cache_age_days: Maximum age for cached items
        """
        self.db = db_manager
        self.cache_dir = Path(cache_dir)
        self.max_cache_age = timedelta(days=max_cache_age_days)
        self.file_handler = AsyncFileHandler()
        self.path_validator = PathValidator()
        self._memory_cache: Dict[str, Path] = {}  # In-memory cache for session
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_cache_key(self, prompt: str, asset_type: str, model: Optional[str] = None) -> str:
        """Generate unique cache key for prompt.
        
        Args:
            prompt: Generation prompt
            asset_type: Type of asset
            model: Optional model identifier
            
        Returns:
            SHA256 hash as cache key
        """
        components = [asset_type, prompt]
        if model:
            components.append(model)
        
        cache_string = ":".join(components)
        return hashlib.sha256(cache_string.encode()).hexdigest()
    
    async def check_exists(
        self,
        prompt: str,
        asset_type: str,
        model: Optional[str] = None
    ) -> Optional[Path]:
        """Check if asset already exists in cache.
        
        Args:
            prompt: Generation prompt
            asset_type: Type of asset
            model: Optional model identifier
            
        Returns:
            Path to cached asset if exists, None otherwise
        """
        cache_key = self._generate_cache_key(prompt, asset_type, model)
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            cached_path = self._memory_cache[cache_key]
            if cached_path.exists():
                logger.debug(f"Cache hit (memory): {cache_key[:8]}...")
                return cached_path
            else:
                # File was deleted, remove from memory cache
                del self._memory_cache[cache_key]
        
        # Check database cache
        cached_info = await self.db.check_duplicate(prompt, asset_type)
        if cached_info:
            file_path = Path(cached_info['file_path'])
            
            # Validate file still exists
            if file_path.exists():
                # Check if cache is not expired
                created_at = datetime.fromisoformat(cached_info['created_at'])
                if datetime.now() - created_at < self.max_cache_age:
                    logger.info(f"Cache hit (database): {cache_key[:8]}...")
                    self._memory_cache[cache_key] = file_path
                    return file_path
                else:
                    logger.debug(f"Cache expired: {cache_key[:8]}...")
            else:
                logger.warning(f"Cached file missing: {file_path}")
        
        return None
    
    async def store(
        self,
        prompt: str,
        asset_type: str,
        file_path: Path,
        model: Optional[str] = None,
        cost: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store successfully generated asset in cache.
        
        Args:
            prompt: Generation prompt
            asset_type: Type of asset
            file_path: Path to generated file
            model: Optional model identifier
            cost: Generation cost
            metadata: Additional metadata
            
        Returns:
            True if stored successfully
        """
        try:
            if not file_path.exists():
                logger.error(f"Cannot cache non-existent file: {file_path}")
                return False
            
            cache_key = self._generate_cache_key(prompt, asset_type, model)
            
            # Copy to cache directory if not already there
            if not str(file_path).startswith(str(self.cache_dir)):
                cache_path = self.cache_dir / asset_type / f"{cache_key[:16]}_{file_path.name}"
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Use async file copy
                await self.file_handler.copy_file(file_path, cache_path)
                file_path = cache_path
            
            # Store in memory cache
            self._memory_cache[cache_key] = file_path
            
            # Store in database (the database manager handles the prompt_cache table)
            # We'll record this as part of the generation attempt
            logger.info(f"Cached asset: {cache_key[:8]}... -> {file_path.name}")
            
            # Save cache metadata
            meta_file = file_path.with_suffix('.meta.json')
            cache_metadata = {
                'prompt': prompt,
                'asset_type': asset_type,
                'model': model,
                'cost': cost,
                'cached_at': datetime.now().isoformat(),
                'cache_key': cache_key,
                **(metadata or {})
            }
            
            async with aiofiles.open(meta_file, 'w') as f:
                await f.write(json.dumps(cache_metadata, indent=2))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache asset: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            'memory_cache_size': len(self._memory_cache),
            'cache_directory': str(self.cache_dir),
            'max_cache_age_days': self.max_cache_age.days
        }
        
        # Count cached files by type
        cache_counts = {}
        if self.cache_dir.exists():
            for asset_dir in self.cache_dir.iterdir():
                if asset_dir.is_dir():
                    count = len(list(asset_dir.glob('*[!.meta.json]')))
                    cache_counts[asset_dir.name] = count
        
        stats['cached_files_by_type'] = cache_counts
        stats['total_cached_files'] = sum(cache_counts.values())
        
        # Get cache directory size
        total_size = 0
        for file_path in self.cache_dir.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        stats['cache_size_mb'] = round(total_size / (1024 * 1024), 2)
        
        return stats
    
    async def clear_expired(self) -> int:
        """Clear expired cache entries.
        
        Returns:
            Number of expired entries removed
        """
        removed_count = 0
        now = datetime.now()
        
        # Clear expired files from disk
        for meta_file in self.cache_dir.rglob('*.meta.json'):
            try:
                async with aiofiles.open(meta_file, 'r') as f:
                    metadata = json.loads(await f.read())
                
                cached_at = datetime.fromisoformat(metadata['cached_at'])
                if now - cached_at > self.max_cache_age:
                    # Remove asset file and metadata
                    asset_file = meta_file.with_suffix('')
                    if asset_file.exists():
                        asset_file.unlink()
                    meta_file.unlink()
                    
                    # Remove from memory cache
                    cache_key = metadata.get('cache_key')
                    if cache_key and cache_key in self._memory_cache:
                        del self._memory_cache[cache_key]
                    
                    removed_count += 1
                    logger.debug(f"Removed expired cache: {asset_file.name}")
                    
            except Exception as e:
                logger.error(f"Error cleaning cache file {meta_file}: {e}")
        
        logger.info(f"Cleared {removed_count} expired cache entries")
        return removed_count
    
    async def warm_cache(self, recent_hours: int = 24) -> int:
        """Warm up memory cache with recent entries.
        
        Args:
            recent_hours: Load entries from last N hours
            
        Returns:
            Number of entries loaded
        """
        loaded_count = 0
        cutoff_time = datetime.now() - timedelta(hours=recent_hours)
        
        for meta_file in self.cache_dir.rglob('*.meta.json'):
            try:
                async with aiofiles.open(meta_file, 'r') as f:
                    metadata = json.loads(await f.read())
                
                cached_at = datetime.fromisoformat(metadata['cached_at'])
                if cached_at > cutoff_time:
                    cache_key = metadata.get('cache_key')
                    asset_file = meta_file.with_suffix('')
                    
                    if cache_key and asset_file.exists():
                        self._memory_cache[cache_key] = asset_file
                        loaded_count += 1
                        
            except Exception as e:
                logger.error(f"Error warming cache from {meta_file}: {e}")
        
        logger.info(f"Warmed cache with {loaded_count} recent entries")
        return loaded_count
    
    async def invalidate(
        self,
        prompt: Optional[str] = None,
        asset_type: Optional[str] = None,
        cache_key: Optional[str] = None
    ) -> bool:
        """Invalidate specific cache entry.
        
        Args:
            prompt: Prompt to invalidate
            asset_type: Asset type to invalidate
            cache_key: Direct cache key to invalidate
            
        Returns:
            True if entry was invalidated
        """
        if cache_key:
            key = cache_key
        elif prompt and asset_type:
            key = self._generate_cache_key(prompt, asset_type)
        else:
            logger.error("Must provide either cache_key or both prompt and asset_type")
            return False
        
        # Remove from memory cache
        if key in self._memory_cache:
            del self._memory_cache[key]
            logger.debug(f"Invalidated memory cache: {key[:8]}...")
        
        # Remove from disk
        for meta_file in self.cache_dir.rglob('*.meta.json'):
            try:
                async with aiofiles.open(meta_file, 'r') as f:
                    metadata = json.loads(await f.read())
                
                if metadata.get('cache_key') == key:
                    asset_file = meta_file.with_suffix('')
                    if asset_file.exists():
                        asset_file.unlink()
                    meta_file.unlink()
                    logger.info(f"Invalidated disk cache: {key[:8]}...")
                    return True
                    
            except Exception as e:
                logger.error(f"Error invalidating cache: {e}")
        
        return False


class CachingStrategy:
    """Advanced caching strategies for different scenarios."""
    
    def __init__(self, cache: AssetCache):
        """Initialize caching strategy.
        
        Args:
            cache: AssetCache instance
        """
        self.cache = cache
    
    async def should_use_cache(
        self,
        prompt: str,
        asset_type: str,
        force_regenerate: bool = False,
        quality_threshold: Optional[float] = None
    ) -> Tuple[bool, Optional[Path]]:
        """Determine if cache should be used.
        
        Args:
            prompt: Generation prompt
            asset_type: Type of asset
            force_regenerate: Force new generation
            quality_threshold: Minimum quality score for cache
            
        Returns:
            Tuple of (should_use_cache, cached_path)
        """
        if force_regenerate:
            return False, None
        
        cached_path = await self.cache.check_exists(prompt, asset_type)
        if not cached_path:
            return False, None
        
        # Check quality threshold if provided
        if quality_threshold is not None:
            meta_file = cached_path.with_suffix('.meta.json')
            if meta_file.exists():
                async with aiofiles.open(meta_file, 'r') as f:
                    metadata = json.loads(await f.read())
                
                quality = metadata.get('quality_score', 1.0)
                if quality < quality_threshold:
                    logger.debug(f"Cache quality {quality} below threshold {quality_threshold}")
                    return False, None
        
        return True, cached_path
    
    async def cache_with_variants(
        self,
        base_prompt: str,
        asset_type: str,
        variants: List[str],
        file_paths: List[Path],
        **kwargs
    ) -> int:
        """Cache asset with multiple prompt variants.
        
        Useful for caching the same image with different prompt phrasings.
        
        Args:
            base_prompt: Base generation prompt
            asset_type: Type of asset
            variants: List of prompt variants
            file_paths: Corresponding file paths
            **kwargs: Additional arguments for store()
            
        Returns:
            Number of variants cached
        """
        cached_count = 0
        
        # Cache base prompt
        if file_paths:
            await self.cache.store(base_prompt, asset_type, file_paths[0], **kwargs)
            cached_count += 1
        
        # Cache variants pointing to same file
        for variant, file_path in zip(variants, file_paths):
            if await self.cache.store(variant, asset_type, file_path, **kwargs):
                cached_count += 1
        
        return cached_count