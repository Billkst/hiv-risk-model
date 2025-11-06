"""
File scanner module for the reorganization system.

Scans the project directory and collects file information.
"""

import os
import stat
from pathlib import Path
from datetime import datetime
from typing import List, Set
import chardet

from .models import FileInfo
from .exceptions import FileOperationError


class FileScanner:
    """Scans project directory and collects file information."""
    
    def __init__(self, project_root: str, exclude_patterns: Set[str] = None):
        """
        Initialize the file scanner.
        
        Args:
            project_root: Root directory of the project
            exclude_patterns: Set of patterns to exclude (e.g., '__pycache__', '.git')
        """
        self.project_root = Path(project_root).resolve()
        
        if not self.project_root.exists():
            raise FileOperationError(f"Project root does not exist: {project_root}")
        
        if not self.project_root.is_dir():
            raise FileOperationError(f"Project root is not a directory: {project_root}")
        
        # Default exclude patterns
        self.exclude_patterns = exclude_patterns or {
            '__pycache__',
            '.git',
            '.pytest_cache',
            '.venv',
            'venv',
            'env',
            '.idea',
            '.vscode',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.DS_Store',
            'node_modules',
        }
    
    def scan_directory(self, root_path: str = None) -> List[FileInfo]:
        """
        Recursively scan directory and return file information.
        
        Args:
            root_path: Directory to scan (defaults to project_root)
        
        Returns:
            List of FileInfo objects
        """
        if root_path is None:
            root_path = self.project_root
        else:
            root_path = Path(root_path).resolve()
        
        files = []
        
        try:
            for entry in os.scandir(root_path):
                # Skip excluded patterns
                if self._should_exclude(entry.name):
                    continue
                
                if entry.is_file(follow_symlinks=False):
                    # Get file info
                    file_info = self.get_file_info(entry.path)
                    if file_info:
                        files.append(file_info)
                
                elif entry.is_dir(follow_symlinks=False):
                    # Recursively scan subdirectories
                    subdir_files = self.scan_directory(entry.path)
                    files.extend(subdir_files)
        
        except PermissionError as e:
            raise FileOperationError(f"Permission denied scanning {root_path}: {e}")
        except Exception as e:
            raise FileOperationError(f"Error scanning {root_path}: {e}")
        
        return files
    
    def get_file_info(self, file_path: str) -> FileInfo:
        """
        Get detailed information about a single file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            FileInfo object or None if file cannot be accessed
        """
        try:
            path = Path(file_path).resolve()
            
            # Get file stats
            file_stat = path.stat()
            
            # Get relative path from project root
            try:
                relative_path = str(path.relative_to(self.project_root))
            except ValueError:
                # File is outside project root
                relative_path = str(path)
            
            # Check if filename contains non-ASCII characters
            has_non_ascii = not path.name.isascii()
            
            # Check if file is executable
            is_executable = bool(file_stat.st_mode & stat.S_IXUSR)
            
            # Get file extension
            extension = path.suffix.lower()
            
            # Get modification time
            modified_time = datetime.fromtimestamp(file_stat.st_mtime)
            
            return FileInfo(
                path=relative_path,
                name=path.name,
                size=file_stat.st_size,
                extension=extension,
                modified_time=modified_time,
                has_non_ascii_name=has_non_ascii,
                is_executable=is_executable,
            )
        
        except (OSError, PermissionError) as e:
            # Log warning but don't fail
            print(f"Warning: Cannot access file {file_path}: {e}")
            return None
    
    def detect_encoding(self, file_path: str) -> str:
        """
        Detect the encoding of a text file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Detected encoding (e.g., 'utf-8', 'ascii', 'gbk')
        """
        try:
            path = Path(file_path)
            
            # Read first 10KB to detect encoding
            with open(path, 'rb') as f:
                raw_data = f.read(10240)
            
            if not raw_data:
                return 'utf-8'  # Empty file, default to utf-8
            
            # Use chardet to detect encoding
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)
            
            # If confidence is low, default to utf-8
            if confidence < 0.7:
                encoding = 'utf-8'
            
            return encoding or 'utf-8'
        
        except Exception as e:
            print(f"Warning: Cannot detect encoding for {file_path}: {e}")
            return 'utf-8'
    
    def _should_exclude(self, name: str) -> bool:
        """
        Check if a file or directory should be excluded.
        
        Args:
            name: File or directory name
        
        Returns:
            True if should be excluded
        """
        # Check exact matches
        if name in self.exclude_patterns:
            return True
        
        # Check wildcard patterns
        for pattern in self.exclude_patterns:
            if '*' in pattern:
                # Simple wildcard matching
                if pattern.startswith('*'):
                    suffix = pattern[1:]
                    if name.endswith(suffix):
                        return True
                elif pattern.endswith('*'):
                    prefix = pattern[:-1]
                    if name.startswith(prefix):
                        return True
        
        return False
    
    def get_file_count(self, root_path: str = None) -> int:
        """
        Get total number of files in directory.
        
        Args:
            root_path: Directory to count (defaults to project_root)
        
        Returns:
            Number of files
        """
        files = self.scan_directory(root_path)
        return len(files)
    
    def get_total_size(self, root_path: str = None) -> int:
        """
        Get total size of all files in directory.
        
        Args:
            root_path: Directory to measure (defaults to project_root)
        
        Returns:
            Total size in bytes
        """
        files = self.scan_directory(root_path)
        return sum(f.size for f in files)
    
    def find_non_ascii_files(self) -> List[FileInfo]:
        """
        Find all files with non-ASCII characters in their names.
        
        Returns:
            List of FileInfo objects with non-ASCII names
        """
        all_files = self.scan_directory()
        return [f for f in all_files if f.has_non_ascii_name]
