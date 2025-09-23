"""Async file operations handler for non-blocking I/O."""

import json
import yaml
import aiofiles
import aiohttp
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

from .path_validator import PathValidator
from .exceptions import ValidationError, ImageDownloadError


class AsyncFileHandler:
    """Handles all async file operations to prevent event loop blocking."""
    
    def __init__(self, path_validator: Optional[PathValidator] = None):
        """Initialize async file handler.
        
        Args:
            path_validator: Optional path validator for security
        """
        self.path_validator = path_validator or PathValidator()
        self.logger = logging.getLogger(__name__)
    
    async def read_json(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """Read JSON file asynchronously.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValidationError: If file is invalid
        """
        filepath = self.path_validator.sanitize_path(filepath)
        
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in {filepath}: {e}")
        except Exception as e:
            raise ValidationError(f"Error reading {filepath}: {e}")
    
    async def write_json(
        self, 
        filepath: Union[str, Path], 
        data: Any, 
        indent: int = 2
    ) -> None:
        """Write JSON file asynchronously.
        
        Args:
            filepath: Path to JSON file
            data: Data to write
            indent: JSON indentation level
        """
        filepath = self.path_validator.sanitize_path(filepath)
        
        try:
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Serialize to JSON string first
            json_str = json.dumps(data, indent=indent, default=str)
            
            # Write asynchronously
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(json_str)
                
            self.logger.debug(f"Wrote JSON to {filepath}")
        except Exception as e:
            raise ValidationError(f"Error writing JSON to {filepath}: {e}")
    
    async def read_yaml(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """Read YAML file asynchronously.
        
        Args:
            filepath: Path to YAML file
            
        Returns:
            Parsed YAML data
            
        Raises:
            ValidationError: If file is invalid
        """
        filepath = self.path_validator.sanitize_path(filepath)
        
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                content = await f.read()
                return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in {filepath}: {e}")
        except Exception as e:
            raise ValidationError(f"Error reading {filepath}: {e}")
    
    async def write_yaml(
        self, 
        filepath: Union[str, Path], 
        data: Any,
        default_flow_style: bool = False
    ) -> None:
        """Write YAML file asynchronously.
        
        Args:
            filepath: Path to YAML file
            data: Data to write
            default_flow_style: YAML flow style setting
        """
        filepath = self.path_validator.sanitize_path(filepath)
        
        try:
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Serialize to YAML string first
            yaml_str = yaml.dump(
                data, 
                default_flow_style=default_flow_style,
                allow_unicode=True
            )
            
            # Write asynchronously
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(yaml_str)
                
            self.logger.debug(f"Wrote YAML to {filepath}")
        except Exception as e:
            raise ValidationError(f"Error writing YAML to {filepath}: {e}")
    
    async def read_text(self, filepath: Union[str, Path]) -> str:
        """Read text file asynchronously.
        
        Args:
            filepath: Path to text file
            
        Returns:
            File contents as string
        """
        filepath = self.path_validator.sanitize_path(filepath)
        
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            raise ValidationError(f"Error reading {filepath}: {e}")
    
    async def write_text(
        self, 
        filepath: Union[str, Path], 
        content: str
    ) -> None:
        """Write text file asynchronously.
        
        Args:
            filepath: Path to text file
            content: Content to write
        """
        filepath = self.path_validator.sanitize_path(filepath)
        
        try:
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(content)
                
            self.logger.debug(f"Wrote text to {filepath}")
        except Exception as e:
            raise ValidationError(f"Error writing to {filepath}: {e}")
    
    async def append_text(
        self, 
        filepath: Union[str, Path], 
        content: str
    ) -> None:
        """Append to text file asynchronously.
        
        Args:
            filepath: Path to text file
            content: Content to append
        """
        filepath = self.path_validator.sanitize_path(filepath)
        
        try:
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(filepath, 'a', encoding='utf-8') as f:
                await f.write(content)
                
            self.logger.debug(f"Appended to {filepath}")
        except Exception as e:
            raise ValidationError(f"Error appending to {filepath}: {e}")
    
    async def download_file(
        self,
        url: str,
        filepath: Union[str, Path],
        chunk_size: int = 8192,
        timeout: int = 30
    ) -> Path:
        """Download file asynchronously with streaming.
        
        Args:
            url: URL to download from
            filepath: Destination file path
            chunk_size: Size of chunks for streaming
            timeout: Request timeout in seconds
            
        Returns:
            Path to downloaded file
            
        Raises:
            ImageDownloadError: If download fails
        """
        filepath = self.path_validator.sanitize_path(filepath)
        
        try:
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    
                    # Stream to file
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            if chunk:
                                await f.write(chunk)
                    
                    self.logger.info(f"Downloaded {url} to {filepath}")
                    return filepath
                    
        except aiohttp.ClientError as e:
            raise ImageDownloadError(f"Failed to download {url}: {e}")
        except Exception as e:
            raise ImageDownloadError(f"Error downloading to {filepath}: {e}")
    
    async def file_exists(self, filepath: Union[str, Path]) -> bool:
        """Check if file exists asynchronously.
        
        Args:
            filepath: Path to check
            
        Returns:
            True if file exists
        """
        try:
            filepath = self.path_validator.sanitize_path(filepath)
            return filepath.exists()
        except:
            return False
    
    async def list_files(
        self, 
        directory: Union[str, Path],
        pattern: str = "*"
    ) -> List[Path]:
        """List files in directory asynchronously.
        
        Args:
            directory: Directory to list
            pattern: Glob pattern for filtering
            
        Returns:
            List of file paths
        """
        directory = self.path_validator.sanitize_path(directory)
        
        try:
            if not directory.is_dir():
                return []
            
            # Use Path.glob which is already efficient
            return sorted(directory.glob(pattern))
        except Exception as e:
            self.logger.warning(f"Error listing files in {directory}: {e}")
            return []
    
    async def copy_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path]
    ) -> None:
        """Copy file asynchronously.
        
        Args:
            source: Source file path
            destination: Destination file path
        """
        source = self.path_validator.sanitize_path(source)
        destination = self.path_validator.sanitize_path(destination)
        
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Stream copy for efficiency
            async with aiofiles.open(source, 'rb') as src:
                async with aiofiles.open(destination, 'wb') as dst:
                    while chunk := await src.read(8192):
                        await dst.write(chunk)
                        
            self.logger.debug(f"Copied {source} to {destination}")
        except Exception as e:
            raise ValidationError(f"Error copying {source} to {destination}: {e}")
    
    async def delete_file(self, filepath: Union[str, Path]) -> None:
        """Delete file asynchronously.
        
        Args:
            filepath: File to delete
        """
        filepath = self.path_validator.sanitize_path(filepath)
        
        try:
            if filepath.exists():
                filepath.unlink()
                self.logger.debug(f"Deleted {filepath}")
        except Exception as e:
            self.logger.warning(f"Error deleting {filepath}: {e}")