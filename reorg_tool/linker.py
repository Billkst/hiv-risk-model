"""
Symbolic link module for the reorganization system.

Creates and manages symbolic links to maintain backward compatibility.
"""

import os
from pathlib import Path
from typing import List, Tuple, Optional

from .transaction_log import TransactionLog
from .exceptions import FileOperationError


class SymbolicLinker:
    """Creates and manages symbolic links for file reorganization."""
    
    def __init__(self, project_root: str, transaction_log: Optional[TransactionLog] = None):
        """
        Initialize the symbolic linker.
        
        Args:
            project_root: Root directory of the project
            transaction_log: Transaction log instance (optional)
        """
        self.project_root = Path(project_root).resolve()
        self.transaction_log = transaction_log
        
        if not self.project_root.exists():
            raise FileOperationError(f"Project root does not exist: {project_root}")
    
    def calculate_relative_path(self, link_path: str, target_path: str) -> str:
        """
        Calculate relative path from link to target.
        
        Args:
            link_path: Path where the symbolic link will be created
            target_path: Path to the target file/directory
        
        Returns:
            Relative path string from link to target
        """
        # Convert to absolute paths
        link_abs = self.project_root / link_path
        target_abs = self.project_root / target_path
        
        # Get the directory containing the link
        link_dir = link_abs.parent
        
        # Calculate relative path from link directory to target
        try:
            relative = os.path.relpath(target_abs, link_dir)
            return relative
        except ValueError as e:
            # This can happen on Windows with different drives
            raise FileOperationError(
                f"Cannot create relative path from {link_path} to {target_path}: {e}"
            )
    
    def create_link(self, link_path: str, target_path: str) -> dict:
        """
        Create a symbolic link.
        
        Args:
            link_path: Path where the symbolic link will be created (relative to project root)
            target_path: Path to the target file/directory (relative to project root)
        
        Returns:
            Dictionary with link creation result
        """
        link_abs = self.project_root / link_path
        target_abs = self.project_root / target_path
        
        # Validate target exists
        if not target_abs.exists():
            error_msg = f"Target does not exist: {target_path}"
            if self.transaction_log is not None:
                self.transaction_log.log_operation(
                    'link', link_path, target_path,
                    success=False, error_message=error_msg
                )
            raise FileOperationError(error_msg)
        
        # Check if link already exists
        if link_abs.exists() or link_abs.is_symlink():
            error_msg = f"Link path already exists: {link_path}"
            if self.transaction_log is not None:
                self.transaction_log.log_operation(
                    'link', link_path, target_path,
                    success=False, error_message=error_msg
                )
            raise FileOperationError(error_msg)
        
        try:
            # Create parent directory if needed
            link_abs.parent.mkdir(parents=True, exist_ok=True)
            
            # Calculate relative path for portability
            relative_target = self.calculate_relative_path(link_path, target_path)
            
            # Create symbolic link
            os.symlink(relative_target, link_abs)
            
            # Verify the link was created successfully
            if not self.verify_link(link_path):
                # Cleanup failed link
                if link_abs.is_symlink():
                    link_abs.unlink()
                error_msg = "Link verification failed after creation"
                if self.transaction_log is not None:
                    self.transaction_log.log_operation(
                        'link', link_path, target_path,
                        success=False, error_message=error_msg
                    )
                raise FileOperationError(error_msg)
            
            # Log successful operation
            if self.transaction_log is not None:
                self.transaction_log.log_operation(
                    'link', link_path, target_path,
                    success=True
                )
            
            return {
                'success': True,
                'link_path': link_path,
                'target_path': target_path,
                'relative_path': relative_target,
            }
        
        except OSError as e:
            # Handle platform-specific errors
            error_msg = f"Failed to create symbolic link: {e}"
            
            # Check for Windows permission issues
            if os.name == 'nt' and 'privilege' in str(e).lower():
                error_msg += " (Administrator privileges may be required on Windows)"
            
            if self.transaction_log is not None:
                self.transaction_log.log_operation(
                    'link', link_path, target_path,
                    success=False, error_message=error_msg
                )
            raise FileOperationError(error_msg)
        
        except Exception as e:
            error_msg = f"Failed to create symbolic link: {e}"
            if self.transaction_log is not None:
                self.transaction_log.log_operation(
                    'link', link_path, target_path,
                    success=False, error_message=error_msg
                )
            raise FileOperationError(error_msg)
    
    def verify_link(self, link_path: str) -> bool:
        """
        Verify that a symbolic link is valid.
        
        Args:
            link_path: Path to the symbolic link (relative to project root)
        
        Returns:
            True if link exists and target is accessible
        """
        link_abs = self.project_root / link_path
        
        # Check if link exists
        if not link_abs.is_symlink():
            return False
        
        # Check if target exists and is accessible
        try:
            # This will resolve the link and check if target exists
            if not link_abs.exists():
                return False
            
            # Try to read the target (for files)
            if link_abs.is_file():
                # Just check if we can open it
                with open(link_abs, 'rb') as f:
                    f.read(1)  # Read one byte to verify access
            
            return True
        
        except (OSError, IOError):
            return False
    
    def create_batch_links(self, links: List[Tuple[str, str]]) -> dict:
        """
        Create multiple symbolic links in batch.
        
        Args:
            links: List of (link_path, target_path) tuples
        
        Returns:
            Dictionary with batch creation results
        """
        results = {
            'total': len(links),
            'success': 0,
            'failed': 0,
            'errors': [],
        }
        
        for link_path, target_path in links:
            try:
                self.create_link(link_path, target_path)
                results['success'] += 1
            except FileOperationError as e:
                results['failed'] += 1
                results['errors'].append({
                    'link_path': link_path,
                    'target_path': target_path,
                    'error': str(e),
                })
        
        return results
    
    def get_link_target(self, link_path: str) -> Optional[str]:
        """
        Get the target path of a symbolic link.
        
        Args:
            link_path: Path to the symbolic link (relative to project root)
        
        Returns:
            Target path (relative to project root) or None if not a link
        """
        link_abs = self.project_root / link_path
        
        if not link_abs.is_symlink():
            return None
        
        try:
            # Read the link target
            target = os.readlink(link_abs)
            
            # Convert to absolute path
            if not os.path.isabs(target):
                target_abs = (link_abs.parent / target).resolve()
            else:
                target_abs = Path(target)
            
            # Convert back to relative path from project root
            try:
                relative = target_abs.relative_to(self.project_root)
                return str(relative)
            except ValueError:
                # Target is outside project root
                return str(target_abs)
        
        except OSError:
            return None
    
    def remove_link(self, link_path: str) -> bool:
        """
        Remove a symbolic link.
        
        Args:
            link_path: Path to the symbolic link (relative to project root)
        
        Returns:
            True if link was removed successfully
        """
        link_abs = self.project_root / link_path
        
        if not link_abs.is_symlink():
            return False
        
        try:
            link_abs.unlink()
            return True
        except OSError:
            return False
    
    def list_links(self, directory: Optional[str] = None) -> List[dict]:
        """
        List all symbolic links in a directory.
        
        Args:
            directory: Directory to search (relative to project root, None for root)
        
        Returns:
            List of dictionaries with link information
        """
        if directory:
            search_path = self.project_root / directory
        else:
            search_path = self.project_root
        
        if not search_path.exists():
            return []
        
        links = []
        
        for item in search_path.rglob('*'):
            if item.is_symlink():
                try:
                    relative_link = item.relative_to(self.project_root)
                    target = self.get_link_target(str(relative_link))
                    is_valid = self.verify_link(str(relative_link))
                    
                    links.append({
                        'link_path': str(relative_link),
                        'target_path': target,
                        'is_valid': is_valid,
                    })
                except ValueError:
                    # Skip links outside project root
                    pass
        
        return links
    
    def verify_all_links(self, directory: Optional[str] = None) -> dict:
        """
        Verify all symbolic links in a directory.
        
        Args:
            directory: Directory to check (relative to project root, None for root)
        
        Returns:
            Dictionary with verification results
        """
        links = self.list_links(directory)
        
        results = {
            'total': len(links),
            'valid': 0,
            'broken': 0,
            'broken_links': [],
        }
        
        for link_info in links:
            if link_info['is_valid']:
                results['valid'] += 1
            else:
                results['broken'] += 1
                results['broken_links'].append(link_info['link_path'])
        
        return results
