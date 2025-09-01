#!/usr/bin/env python3
"""
Git operations for automatic asset commits.
Handles staging, committing, and pushing generated assets to GitHub.
"""

import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class GitOperations:
    """Handles Git operations for asset management"""
    
    def __init__(self, repo_path: Path = None):
        """Initialize Git operations
        
        Args:
            repo_path: Path to Git repository root (defaults to current directory)
        """
        self.repo_path = repo_path or Path.cwd()
        
    def check_git_repo(self) -> bool:
        """Check if current directory is a Git repository
        
        Returns:
            True if Git repo exists, False otherwise
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            logger.error("Git is not installed or not in PATH")
            return False
        except Exception as e:
            logger.error(f"Error checking Git repository: {e}")
            return False
    
    def get_current_branch(self) -> Optional[str]:
        """Get the current Git branch name
        
        Returns:
            Branch name or None if error
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Error getting current branch: {e}")
            return None
    
    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes
        
        Returns:
            True if there are uncommitted changes
        """
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return bool(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error checking Git status: {e}")
            return False
    
    def stage_assets(self, asset_dir: str = "assets") -> Tuple[bool, List[str]]:
        """Stage all files in the assets directory
        
        Args:
            asset_dir: Directory containing assets to stage
            
        Returns:
            Tuple of (success, list of staged files)
        """
        staged_files = []
        try:
            # Get list of files to stage
            asset_path = self.repo_path / asset_dir
            if not asset_path.exists():
                logger.warning(f"Asset directory {asset_path} does not exist")
                return False, []
            
            # Stage all files in assets directory
            result = subprocess.run(
                ['git', 'add', asset_dir],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to stage assets: {result.stderr}")
                return False, []
            
            # Get list of staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', asset_dir],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            staged_files = [f for f in result.stdout.strip().split('\n') if f]
            logger.info(f"Staged {len(staged_files)} files from {asset_dir}")
            
            return True, staged_files
            
        except Exception as e:
            logger.error(f"Error staging assets: {e}")
            return False, []
    
    def create_commit(self, message: str, body: str = "") -> bool:
        """Create a Git commit with the staged changes
        
        Args:
            message: Commit message title
            body: Optional commit message body
            
        Returns:
            True if commit successful
        """
        try:
            # Check if there are staged changes
            result = subprocess.run(
                ['git', 'diff', '--cached', '--quiet'],
                cwd=self.repo_path,
                capture_output=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info("No staged changes to commit")
                return True
            
            # Create commit
            commit_message = message
            if body:
                commit_message = f"{message}\n\n{body}"
            
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to create commit: {result.stderr}")
                return False
            
            logger.info(f"Created commit: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating commit: {e}")
            return False
    
    def push_to_remote(self, remote: str = "origin", branch: str = None) -> bool:
        """Push commits to remote repository
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch to push (default: current branch)
            
        Returns:
            True if push successful
        """
        try:
            if branch is None:
                branch = self.get_current_branch()
                if not branch:
                    logger.error("Could not determine current branch")
                    return False
            
            # Check if remote exists
            result = subprocess.run(
                ['git', 'remote', 'get-url', remote],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.warning(f"Remote '{remote}' not configured, skipping push")
                return True  # Not an error, just skip push
            
            # Push to remote
            logger.info(f"Pushing to {remote}/{branch}...")
            result = subprocess.run(
                ['git', 'push', remote, branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to push: {result.stderr}")
                return False
            
            logger.info(f"Successfully pushed to {remote}/{branch}")
            return True
            
        except Exception as e:
            logger.error(f"Error pushing to remote: {e}")
            return False
    
    def auto_commit_assets(self, stats: Dict, mode: str = "production", 
                          dry_run: bool = False) -> bool:
        """Automatically commit and push generated assets
        
        Args:
            stats: Dictionary with generation statistics
            mode: Generation mode (sample/production)
            dry_run: If True, only preview what would be done
            
        Returns:
            True if successful
        """
        try:
            # Check if we're in a Git repo
            if not self.check_git_repo():
                logger.warning("Not in a Git repository, skipping auto-commit")
                return True
            
            # Stage assets
            success, staged_files = self.stage_assets()
            if not success:
                logger.error("Failed to stage assets")
                return False
            
            if not staged_files:
                logger.info("No new assets to commit")
                return True
            
            # Create commit message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Extract statistics
            icons_count = stats.get('icons_generated', 0)
            covers_count = stats.get('covers_generated', 0)
            textures_count = stats.get('textures_generated', 0)
            total_count = icons_count + covers_count + textures_count
            total_cost = stats.get('total_cost', 0.0)
            
            # Commit title
            title = f"feat(assets): Generate {total_count} {mode} assets"
            
            # Commit body with statistics
            body_lines = [
                f"Generated on: {timestamp}",
                f"Mode: {mode.capitalize()}",
                "",
                "Assets generated:",
                f"  - Icons: {icons_count}",
                f"  - Covers: {covers_count}",
                f"  - Textures: {textures_count}",
                f"  - Total: {total_count}",
                "",
                f"Cost: ${total_cost:.2f}",
                f"Files changed: {len(staged_files)}",
            ]
            
            if stats.get('regenerated_count'):
                body_lines.append(f"Regenerated: {stats['regenerated_count']} assets")
            
            body = '\n'.join(body_lines)
            
            if dry_run:
                logger.info("DRY RUN - Would commit with message:")
                logger.info(f"{title}\n\n{body}")
                logger.info(f"Files to be committed: {len(staged_files)}")
                return True
            
            # Create commit
            if not self.create_commit(title, body):
                logger.error("Failed to create commit")
                return False
            
            # Push to remote
            if not self.push_to_remote():
                logger.warning("Commit created but push failed - you may need to push manually")
                # Not a fatal error - commit was still created locally
            
            logger.info(f"Successfully committed {len(staged_files)} asset files")
            return True
            
        except Exception as e:
            logger.error(f"Error in auto-commit process: {e}")
            return False
    
    def get_last_asset_commit(self) -> Optional[str]:
        """Get the SHA of the last asset-related commit
        
        Returns:
            Commit SHA or None if not found
        """
        try:
            result = subprocess.run(
                ['git', 'log', '--grep=feat(assets):', '-1', '--format=%H'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commit_sha = result.stdout.strip()
            return commit_sha if commit_sha else None
            
        except Exception as e:
            logger.error(f"Error getting last asset commit: {e}")
            return None