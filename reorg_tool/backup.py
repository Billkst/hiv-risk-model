"""
Backup service module for the reorganization system.

Creates and manages project backups.
"""

import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

from .exceptions import FileOperationError


class BackupService:
    """Creates and manages project backups."""
    
    def __init__(self, project_root: str, backup_dir: Optional[str] = None):
        """
        Initialize the backup service.
        
        Args:
            project_root: Root directory of the project
            backup_dir: Directory to store backups (defaults to parent of project_root)
        """
        self.project_root = Path(project_root).resolve()
        
        if not self.project_root.exists():
            raise FileOperationError(f"Project root does not exist: {project_root}")
        
        # Set backup directory
        if backup_dir:
            self.backup_dir = Path(backup_dir).resolve()
        else:
            self.backup_dir = self.project_root.parent
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a complete backup of the project.
        
        Args:
            backup_name: Custom backup name (defaults to timestamped name)
        
        Returns:
            Path to the backup directory
        """
        # Generate backup name if not provided
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self.project_root.name}_backup_{timestamp}"
        
        backup_path = self.backup_dir / backup_name
        
        # Check if backup already exists
        if backup_path.exists():
            raise FileOperationError(f"Backup already exists: {backup_path}")
        
        try:
            # Copy entire project directory
            print(f"Creating backup: {backup_path}")
            shutil.copytree(
                self.project_root,
                backup_path,
                symlinks=False,  # Don't follow symlinks
                ignore=self._get_ignore_patterns()
            )
            
            print(f"Backup created successfully: {backup_path}")
            return str(backup_path)
        
        except Exception as e:
            # Clean up partial backup if error occurs
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise FileOperationError(f"Failed to create backup: {e}")
    
    def _get_ignore_patterns(self):
        """
        Get patterns to ignore during backup.
        
        Returns:
            Ignore function for shutil.copytree
        """
        ignore_patterns = [
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.pytest_cache',
            '.git',
            '.venv',
            'venv',
            'env',
            '.idea',
            '.vscode',
            'node_modules',
            '*.log',
        ]
        
        return shutil.ignore_patterns(*ignore_patterns)
    
    def verify_backup(self, backup_path: str) -> bool:
        """
        Verify backup integrity by comparing file counts and key files.
        
        Args:
            backup_path: Path to backup directory
        
        Returns:
            True if backup is valid
        """
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            print(f"Backup does not exist: {backup_path}")
            return False
        
        try:
            # Count files in original and backup
            original_files = self._count_files(self.project_root)
            backup_files = self._count_files(backup_path)
            
            # Allow some difference due to ignored patterns
            file_diff = abs(original_files - backup_files)
            if file_diff > original_files * 0.1:  # More than 10% difference
                print(
                    f"File count mismatch: "
                    f"original={original_files}, backup={backup_files}"
                )
                return False
            
            # Verify critical files exist and match
            critical_files = self._get_critical_files()
            for rel_path in critical_files:
                original_file = self.project_root / rel_path
                backup_file = backup_path / rel_path
                
                if not original_file.exists():
                    continue  # Skip if original doesn't exist
                
                if not backup_file.exists():
                    print(f"Critical file missing in backup: {rel_path}")
                    return False
                
                # Compare file sizes
                if original_file.stat().st_size != backup_file.stat().st_size:
                    print(f"File size mismatch: {rel_path}")
                    return False
            
            print(f"Backup verification successful: {backup_path}")
            return True
        
        except Exception as e:
            print(f"Error verifying backup: {e}")
            return False
    
    def _count_files(self, directory: Path) -> int:
        """Count total number of files in directory."""
        count = 0
        for root, dirs, files in os.walk(directory):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            count += len(files)
        return count
    
    def _should_ignore(self, name: str) -> bool:
        """Check if directory should be ignored."""
        ignore_dirs = {
            '__pycache__',
            '.pytest_cache',
            '.git',
            '.venv',
            'venv',
            'env',
            '.idea',
            '.vscode',
            'node_modules',
        }
        return name in ignore_dirs
    
    def _get_critical_files(self) -> List[str]:
        """
        Get list of critical files to verify.
        
        Returns:
            List of relative file paths
        """
        return [
            'requirements.txt',
            'README.md',
        ]
    
    def calculate_checksum(self, file_path: str) -> str:
        """
        Calculate MD5 checksum of a file.
        
        Args:
            file_path: Path to file
        
        Returns:
            MD5 checksum string
        """
        md5 = hashlib.md5()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            raise FileOperationError(f"Failed to calculate checksum: {e}")
    
    def cleanup_old_backups(self, retention_days: int = 7) -> List[str]:
        """
        Remove backups older than retention period.
        
        Args:
            retention_days: Number of days to keep backups
        
        Returns:
            List of removed backup paths
        """
        removed = []
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        try:
            # Find backup directories
            backup_pattern = f"{self.project_root.name}_backup_*"
            
            for item in self.backup_dir.iterdir():
                if not item.is_dir():
                    continue
                
                # Check if it matches backup pattern
                if not item.name.startswith(f"{self.project_root.name}_backup_"):
                    continue
                
                # Get backup creation time
                backup_time = datetime.fromtimestamp(item.stat().st_mtime)
                
                # Remove if older than retention period
                if backup_time < cutoff_date:
                    print(f"Removing old backup: {item}")
                    shutil.rmtree(item)
                    removed.append(str(item))
            
            if removed:
                print(f"Removed {len(removed)} old backups")
            else:
                print("No old backups to remove")
            
            return removed
        
        except Exception as e:
            print(f"Error cleaning up backups: {e}")
            return removed
    
    def list_backups(self) -> List[dict]:
        """
        List all available backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        try:
            for item in self.backup_dir.iterdir():
                if not item.is_dir():
                    continue
                
                # Check if it matches backup pattern
                if not item.name.startswith(f"{self.project_root.name}_backup_"):
                    continue
                
                # Get backup info
                stat = item.stat()
                backups.append({
                    'path': str(item),
                    'name': item.name,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'size_mb': self._get_directory_size(item) / (1024 * 1024),
                })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            return backups
        
        except Exception as e:
            print(f"Error listing backups: {e}")
            return []
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory in bytes."""
        total = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = Path(root) / file
                try:
                    total += file_path.stat().st_size
                except:
                    pass
        return total
    
    def restore_backup(self, backup_path: str, target_path: Optional[str] = None):
        """
        Restore a backup to target location.
        
        Args:
            backup_path: Path to backup directory
            target_path: Target restore location (defaults to original project_root)
        """
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            raise FileOperationError(f"Backup does not exist: {backup_path}")
        
        if target_path is None:
            target_path = self.project_root
        else:
            target_path = Path(target_path)
        
        # Safety check: don't overwrite existing directory without confirmation
        if target_path.exists() and list(target_path.iterdir()):
            raise FileOperationError(
                f"Target directory is not empty: {target_path}. "
                "Please remove it first or choose a different location."
            )
        
        try:
            print(f"Restoring backup from {backup_path} to {target_path}")
            
            # Remove target if it exists (but is empty)
            if target_path.exists():
                shutil.rmtree(target_path)
            
            # Copy backup to target
            shutil.copytree(backup_path, target_path, symlinks=False)
            
            print(f"Backup restored successfully to {target_path}")
        
        except Exception as e:
            raise FileOperationError(f"Failed to restore backup: {e}")
