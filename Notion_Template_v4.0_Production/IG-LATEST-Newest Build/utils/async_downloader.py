"""
Estate Planning v4.0 - Asynchronous Image Downloader
Handles efficient, concurrent image downloads from Replicate URLs with retry logic
"""

import asyncio
import aiohttp
import aiofiles
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DownloadStatus(Enum):
    """Status of a download operation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class DownloadTask:
    """Represents a single download task"""
    url: str
    filepath: Path
    task_id: str
    status: DownloadStatus = DownloadStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AsyncImageDownloader:
    """Manages concurrent image downloads with retry logic and error handling"""
    
    def __init__(
        self,
        max_concurrent: int = 5,
        timeout: int = 30,
        chunk_size: int = 8192,
        retry_delay: float = 1.0,
        max_retries: int = 3
    ):
        """
        Initialize the async downloader
        
        Args:
            max_concurrent: Maximum concurrent downloads
            timeout: Timeout per download in seconds
            chunk_size: Size of chunks for streaming downloads
            retry_delay: Delay between retry attempts
            max_retries: Maximum number of retry attempts
        """
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.chunk_size = chunk_size
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None
        self.download_stats = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'total_bytes': 0,
            'total_time': 0.0
        }
    
    @asynccontextmanager
    async def get_session(self):
        """Context manager for aiohttp session"""
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrent * 2,
                limit_per_host=self.max_concurrent
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
            )
        try:
            yield self.session
        finally:
            # Don't close session here, keep it for reuse
            pass
    
    async def download_single(
        self,
        task: DownloadTask,
        progress_callback: Optional[callable] = None
    ) -> DownloadTask:
        """
        Download a single image with retry logic
        
        Args:
            task: Download task to execute
            progress_callback: Optional callback for progress updates
            
        Returns:
            Updated download task with results
        """
        async with self.semaphore:
            task.status = DownloadStatus.IN_PROGRESS
            task.start_time = time.time()
            
            for attempt in range(task.max_attempts):
                task.attempts = attempt + 1
                
                try:
                    if attempt > 0:
                        task.status = DownloadStatus.RETRYING
                        await asyncio.sleep(self.retry_delay * attempt)
                    
                    async with self.get_session() as session:
                        async with session.get(task.url) as response:
                            response.raise_for_status()
                            
                            # Get content length
                            content_length = response.headers.get('Content-Length')
                            if content_length:
                                task.file_size = int(content_length)
                            
                            # Ensure directory exists
                            task.filepath.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Download with progress tracking
                            temp_filepath = task.filepath.with_suffix('.tmp')
                            downloaded = 0
                            hasher = hashlib.sha256()
                            
                            async with aiofiles.open(temp_filepath, 'wb') as file:
                                async for chunk in response.content.iter_chunked(self.chunk_size):
                                    await file.write(chunk)
                                    hasher.update(chunk)
                                    downloaded += len(chunk)
                                    
                                    if progress_callback:
                                        progress_callback(task.task_id, downloaded, task.file_size)
                            
                            # Calculate checksum
                            task.checksum = hasher.hexdigest()
                            
                            # Atomic rename
                            temp_filepath.replace(task.filepath)
                            
                            # Update stats
                            task.status = DownloadStatus.COMPLETED
                            task.end_time = time.time()
                            task.file_size = downloaded
                            
                            self.download_stats['successful_downloads'] += 1
                            self.download_stats['total_bytes'] += downloaded
                            self.download_stats['total_time'] += (task.end_time - task.start_time)
                            
                            logger.info(f"Downloaded {task.filepath.name} ({downloaded:,} bytes)")
                            return task
                            
                except asyncio.TimeoutError:
                    task.error = f"Timeout after {self.timeout.total}s (attempt {attempt + 1}/{task.max_attempts})"
                    logger.warning(f"Download timeout for {task.url}: {task.error}")
                    
                except aiohttp.ClientError as e:
                    task.error = f"Network error: {str(e)} (attempt {attempt + 1}/{task.max_attempts})"
                    logger.warning(f"Download error for {task.url}: {task.error}")
                    
                except Exception as e:
                    task.error = f"Unexpected error: {str(e)} (attempt {attempt + 1}/{task.max_attempts})"
                    logger.error(f"Unexpected download error for {task.url}: {task.error}")
            
            # All attempts failed
            task.status = DownloadStatus.FAILED
            task.end_time = time.time()
            self.download_stats['failed_downloads'] += 1
            
            # Clean up partial download if exists
            temp_filepath = task.filepath.with_suffix('.tmp')
            if temp_filepath.exists():
                temp_filepath.unlink()
            
            logger.error(f"Failed to download {task.url} after {task.attempts} attempts: {task.error}")
            return task
    
    async def download_batch(
        self,
        tasks: List[DownloadTask],
        progress_callback: Optional[callable] = None
    ) -> List[DownloadTask]:
        """
        Download multiple images concurrently
        
        Args:
            tasks: List of download tasks
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of completed download tasks with results
        """
        self.download_stats['total_downloads'] = len(tasks)
        
        # Create download coroutines
        download_coros = [
            self.download_single(task, progress_callback)
            for task in tasks
        ]
        
        # Execute downloads concurrently
        results = await asyncio.gather(*download_coros, return_exceptions=True)
        
        # Process results
        completed_tasks = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tasks[i].status = DownloadStatus.FAILED
                tasks[i].error = str(result)
                logger.error(f"Download exception for task {tasks[i].task_id}: {result}")
            else:
                tasks[i] = result
            completed_tasks.append(tasks[i])
        
        return completed_tasks
    
    async def download_urls(
        self,
        url_map: Dict[str, str],
        output_dir: Path,
        progress_callback: Optional[callable] = None
    ) -> Tuple[List[Path], List[str]]:
        """
        Convenience method to download URLs to a directory
        
        Args:
            url_map: Dictionary mapping filenames to URLs
            output_dir: Output directory for downloads
            progress_callback: Optional progress callback
            
        Returns:
            Tuple of (successful_paths, failed_urls)
        """
        # Create download tasks
        tasks = []
        for filename, url in url_map.items():
            task = DownloadTask(
                url=url,
                filepath=output_dir / filename,
                task_id=filename
            )
            tasks.append(task)
        
        # Execute downloads
        results = await self.download_batch(tasks, progress_callback)
        
        # Separate successes and failures
        successful_paths = []
        failed_urls = []
        
        for task in results:
            if task.status == DownloadStatus.COMPLETED:
                successful_paths.append(task.filepath)
            else:
                failed_urls.append(task.url)
        
        return successful_paths, failed_urls
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get download statistics"""
        stats = self.download_stats.copy()
        if stats['total_time'] > 0:
            stats['average_speed_mbps'] = (stats['total_bytes'] / stats['total_time']) / (1024 * 1024)
        else:
            stats['average_speed_mbps'] = 0
        return stats
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None

# Example usage and testing
async def example_usage():
    """Example of how to use the AsyncImageDownloader"""
    downloader = AsyncImageDownloader(
        max_concurrent=3,
        timeout=30,
        retry_delay=1.0,
        max_retries=3
    )
    
    # Example URLs (would come from Replicate in real usage)
    url_map = {
        'icon_001.png': 'https://example.com/image1.png',
        'icon_002.png': 'https://example.com/image2.png',
        'cover_001.png': 'https://example.com/image3.png',
    }
    
    output_dir = Path('output/downloads')
    
    def progress_callback(task_id: str, downloaded: int, total: Optional[int]):
        if total:
            percent = (downloaded / total) * 100
            print(f"{task_id}: {percent:.1f}% ({downloaded}/{total} bytes)")
        else:
            print(f"{task_id}: {downloaded} bytes downloaded")
    
    try:
        successful, failed = await downloader.download_urls(
            url_map,
            output_dir,
            progress_callback
        )
        
        print(f"\nDownload Summary:")
        print(f"Successful: {len(successful)} files")
        print(f"Failed: {len(failed)} files")
        
        stats = downloader.get_statistics()
        print(f"\nStatistics:")
        print(f"Total downloads: {stats['total_downloads']}")
        print(f"Successful: {stats['successful_downloads']}")
        print(f"Failed: {stats['failed_downloads']}")
        print(f"Total bytes: {stats['total_bytes']:,}")
        print(f"Average speed: {stats['average_speed_mbps']:.2f} MB/s")
        
    finally:
        await downloader.cleanup()

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())