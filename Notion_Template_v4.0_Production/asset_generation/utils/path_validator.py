"""Path validation and sanitization utilities."""

import os
from pathlib import Path
from typing import Union, Optional
import re

from .exceptions import PathTraversalError, ValidationError


class PathValidator:
    """Validates and sanitizes file paths for security."""
    
    # Patterns that indicate path traversal attempts
    DANGEROUS_PATTERNS = [
        r'\.\.',  # Parent directory reference
        r'~',      # Home directory reference
        # Note: Removed absolute path check - we validate against base_directory instead
        r'\\\\',   # UNC path
        # Note: Removed colon check as it was causing issues with valid paths
        # Drive letters are handled separately below
    ]
    
    def __init__(self, base_directory: Optional[Union[str, Path]] = None):
        """Initialize path validator.
        
        Args:
            base_directory: Base directory for all operations (defaults to cwd)
        """
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        self.base_directory = self.base_directory.resolve()
        
    def sanitize_path(self, user_path: Union[str, Path]) -> Path:
        """Sanitize and validate a user-provided path.
        
        Args:
            user_path: Path provided by user or configuration
            
        Returns:
            Sanitized absolute path
            
        Raises:
            PathTraversalError: If path traversal is attempted
            ValidationError: If path is invalid
        """
        if not user_path:
            raise ValidationError("Path cannot be empty")
            
        # Convert to string for pattern checking
        path_str = str(user_path)
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, path_str):
                raise PathTraversalError(
                    f"Dangerous pattern detected in path: {path_str}"
                )
        
        # On Windows, check for invalid drive letter patterns (but not on Unix)
        if os.name == 'nt' and ':' in path_str:
            # Check for colons not at position 1 (invalid on Windows)
            colon_positions = [i for i, c in enumerate(path_str) if c == ':']
            if any(pos != 1 for pos in colon_positions):
                raise PathTraversalError(
                    f"Invalid colon position in Windows path: {path_str}"
                )
                
        # Convert to Path object
        path = Path(user_path)
        
        # If path is relative, make it relative to base directory
        if not path.is_absolute():
            path = self.base_directory / path
            
        # Resolve to absolute path (follows symlinks)
        try:
            resolved_path = path.resolve()
        except Exception as e:
            raise ValidationError(f"Cannot resolve path {path}: {e}")
            
        # Ensure path is within base directory
        try:
            resolved_path.relative_to(self.base_directory)
        except ValueError:
            raise PathTraversalError(
                f"Path {resolved_path} is outside base directory {self.base_directory}"
            )
            
        return resolved_path
        
    def validate_filename(self, filename: str) -> str:
        """Validate and sanitize a filename.
        
        Args:
            filename: Filename to validate
            
        Returns:
            Sanitized filename
            
        Raises:
            ValidationError: If filename is invalid
        """
        if not filename:
            raise ValidationError("Filename cannot be empty")
            
        # Remove any path components
        filename = os.path.basename(filename)
        
        # Check for reserved names on Windows
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in reserved_names:
            raise ValidationError(f"Reserved filename: {filename}")
            
        # Remove invalid characters
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
            
        # Ensure filename is not too long (255 chars is typical limit)
        if len(filename) > 255:
            # Preserve extension if possible
            if '.' in filename:
                name, ext = filename.rsplit('.', 1)
                max_name_length = 255 - len(ext) - 1
                filename = name[:max_name_length] + '.' + ext
            else:
                filename = filename[:255]
                
        return filename
        
    def ensure_directory_exists(self, directory: Union[str, Path]) -> Path:
        """Ensure a directory exists, creating it if necessary.
        
        Args:
            directory: Directory path
            
        Returns:
            Sanitized directory path
            
        Raises:
            PathTraversalError: If path traversal is attempted
            ValidationError: If path is invalid
        """
        directory = self.sanitize_path(directory)
        
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValidationError(f"Cannot create directory {directory}: {e}")
            
        return directory
        
    def validate_config_paths(self, config: dict) -> dict:
        """Validate all paths in a configuration dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with validated paths
            
        Raises:
            PathTraversalError: If any path attempts traversal
            ValidationError: If any path is invalid
        """
        validated_config = config.copy()
        
        # Define paths that need validation
        path_keys = [
            ('output', 'sample_directory'),
            ('output', 'production_directory'),
            ('output', 'backup_directory'),
            ('logging', 'log_file'),
            ('logging', 'transaction_log'),
        ]
        
        for keys in path_keys:
            current = validated_config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
                
            if keys[-1] in current:
                path = self.sanitize_path(current[keys[-1]])
                current[keys[-1]] = str(path)
                
        return validated_config


def create_safe_path(base_dir: Union[str, Path], *parts: str) -> Path:
    """Create a safe path by joining parts and validating.
    
    Args:
        base_dir: Base directory
        *parts: Path components to join
        
    Returns:
        Safe, validated path
        
    Raises:
        PathTraversalError: If resulting path is unsafe
    """
    validator = PathValidator(base_dir)
    path = Path(base_dir)
    for part in parts:
        # Validate each component
        if '..' in part or part.startswith('/') or part.startswith('~'):
            raise PathTraversalError(f"Unsafe path component: {part}")
        path = path / part
    return validator.sanitize_path(path)