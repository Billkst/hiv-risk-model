"""
File mover module for the reorganization system.

Safely moves files with verification and rollback support.
"""

import shutil
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional

from .transaction_log import TransactionLog
from .exceptions import FileOperationError


class FileMover:
    """Safely moves files with verification and transaction logging."""
    
    def __init__(self, project_root: str, transaction_log: Optional[TransactionLog] = None):
        """
        Initialize the file mover.
        
        Args:
            project_root: Root directory of the project
            transaction_log: Transaction log instance (optional)
        """
        self.project_root = Path(project_root).resolve()
        self.transaction_log = transaction_log
        
        if not self.project_root.exists():
            raise FileOperationError(f"Project root does not exist: {project_root}")
    
    def move_file(self, source: str, destination: str) -> dict:
        """
        Safely move a single file (copy + verify + delete).
        
        Args:
            source: Source file path (relative to project root)
            destination: Destination file path (relative to project root)
        
        Returns:
            Dictionary with move result information
        """
        source_path = self.project_root / source
        dest_path = self.project_root / destination
        
        # Validate source exists
        if not source_path.exists():
            error_msg = f"Source file does not exist: {source}"
            if self.transaction_log is not None:
                self.transaction_log.log_operation(
                    'move', source, destination,
                    success=False, error_message=error_msg
                )
            raise FileOperationError(error_msg)
        
        # Check if destination already exists
        if dest_path.exists():
            error_msg = f"Destination already exists: {destination}"
            if self.transaction_log is not None:
                self.transaction_log.log_operation(
                    'move', source, destination,
                    success=False, error_message=error_msg
                )
            raise FileOperationError(error_msg)
        
        try:
            # Calculate checksum before move
            checksum_before = self._calculate_checksum(source_path)
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to destination
            shutil.copy2(source_path, dest_path)
            
            # Verify copy integrity
            checksum_after = self._calculate_checksum(dest_path)
            
            if checksum_before != checksum_after:
                # Cleanup failed copy
                dest_path.unlink()
                error_msg = "Checksum mismatch after copy"
                if self.transaction_log is not None:
                    self.transaction_log.log_operation(
                        'move', source, destination,
                        success=False, error_message=error_msg,
                        checksum_before=checksum_before,
                        checksum_after=checksum_after
                    )
                raise FileOperationError(error_msg)
            
            # Delete source file
            source_path.unlink()
            
            # Log successful operation
            if self.transaction_log is not None:
                self.transaction_log.log_operation(
                    'move', source, destination,
                    success=True,
                    checksum_before=checksum_before,
                    checksum_after=checksum_after
                )
            
            return {
                'success': True,
                'source': source,
                'destination': destination,
                'checksum': checksum_after,
            }
        
        except Exception as e:
            # Attempt to restore source if it was deleted
            if not source_path.exists() and dest_path.exists():
                try:
                    shutil.copy2(dest_path, source_path)
                    dest_path.unlink()
                except:
                    pass
            
            error_msg = f"Failed to move file: {e}"
            if self.transaction_log is not None:
                self.transaction_log.log_operation(
                    'move', source, destination,
                    success=False, error_message=error_msg
                )
            raise FileOperationError(error_msg)
    
    def move_batch(self, moves: List[Tuple[str, str]]) -> dict:
        """
        Move multiple files in batch.
        
        Args:
            moves: List of (source, destination) tuples
        
        Returns:
            Dictionary with batch move results
        """
        results = {
            'total': len(moves),
            'success': 0,
            'failed': 0,
            'errors': [],
        }
        
        for source, destination in moves:
            try:
                self.move_file(source, destination)
                results['success'] += 1
            except FileOperationError as e:
                results['failed'] += 1
                results['errors'].append({
                    'source': source,
                    'destination': destination,
                    'error': str(e),
                })
        
        return results
    
    def preserve_permissions(self, source: str, destination: str):
        """
        Preserve file permissions and timestamps.
        
        Args:
            source: Source file path
            destination: Destination file path
        """
        source_path = self.project_root / source
        dest_path = self.project_root / destination
        
        if not source_path.exists():
            raise FileOperationError(f"Source file does not exist: {source}")
        
        if not dest_path.exists():
            raise FileOperationError(f"Destination file does not exist: {destination}")
        
        try:
            # Copy permissions and timestamps
            shutil.copystat(source_path, dest_path)
        except Exception as e:
            raise FileOperationError(f"Failed to preserve permissions: {e}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
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
    
    def verify_move(self, source: str, destination: str) -> bool:
        """
        Verify that a file was moved successfully.
        
        Args:
            source: Original source path
            destination: Destination path
        
        Returns:
            True if move was successful
        """
        source_path = self.project_root / source
        dest_path = self.project_root / destination
        
        # Source should not exist
        if source_path.exists():
            return False
        
        # Destination should exist
        if not dest_path.exists():
            return False
        
        return True
    
    def rollback_move(self, source: str, destination: str) -> bool:
        """
        Rollback a file move operation.
        
        Args:
            source: Original source path
            destination: Current destination path
        
        Returns:
            True if rollback was successful
        """
        source_path = self.project_root / source
        dest_path = self.project_root / destination
        
        # Destination must exist
        if not dest_path.exists():
            return False
        
        # Source must not exist
        if source_path.exists():
            return False
        
        try:
            # Create source directory if needed
            source_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file back
            shutil.move(str(dest_path), str(source_path))
            
            return True
        except Exception as e:
            print(f"Failed to rollback move: {e}")
            return False
