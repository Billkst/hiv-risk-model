"""
Rollback service for the reorganization system.

Provides functionality to rollback reorganization operations.
"""

import shutil
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from .transaction_log import TransactionLog
from .models import TransactionEntry
from .exceptions import RollbackError


class RollbackService:
    """Handles rollback of reorganization operations."""
    
    def __init__(self, project_root: str):
        """
        Initialize the rollback service.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        
        if not self.project_root.exists():
            raise RollbackError(f"Project root does not exist: {project_root}")
        
        self.rollback_log: List[Dict] = []
    
    def execute_rollback(
        self,
        transaction_log_path: str,
        backup_path: Optional[str] = None
    ) -> Dict:
        """
        Execute rollback based on transaction log.
        
        Args:
            transaction_log_path: Path to the transaction log file
            backup_path: Optional path to backup for verification
        
        Returns:
            Dictionary with rollback results
        """
        # Load transaction log
        try:
            transaction_log = TransactionLog(transaction_log_path)
            transaction_log.load_log()
        except Exception as e:
            raise RollbackError(f"Failed to load transaction log: {e}")
        
        # Get operations in reverse order
        operations = transaction_log.get_reverse_operations()
        
        results = {
            'success': True,
            'total_operations': len(operations),
            'reversed': 0,
            'failed': 0,
            'errors': [],
            'start_time': datetime.now(),
        }
        
        # Execute reverse operations
        for entry in operations:
            try:
                if entry.operation == 'move':
                    self._reverse_move(entry)
                elif entry.operation == 'link':
                    self._reverse_link(entry)
                elif entry.operation == 'delete':
                    self._reverse_delete(entry, backup_path)
                
                results['reversed'] += 1
                self.rollback_log.append({
                    'operation': entry.operation,
                    'source': entry.source,
                    'destination': entry.destination,
                    'success': True,
                })
            
            except Exception as e:
                results['failed'] += 1
                results['success'] = False
                error_msg = f"Failed to reverse {entry.operation}: {entry.source} - {str(e)}"
                results['errors'].append(error_msg)
                self.rollback_log.append({
                    'operation': entry.operation,
                    'source': entry.source,
                    'destination': entry.destination,
                    'success': False,
                    'error': str(e),
                })
        
        results['end_time'] = datetime.now()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        return results
    
    def _reverse_move(self, entry: TransactionEntry):
        """
        Reverse a move operation (move file back to original location).
        
        Args:
            entry: Transaction entry for the move operation
        """
        # For move: source is old path, destination is new path
        # To reverse: move from destination back to source
        source_path = self.project_root / entry.source
        dest_path = self.project_root / entry.destination
        
        # Check if destination exists (the file should be there after move)
        if not dest_path.exists():
            raise RollbackError(f"Cannot reverse move: destination does not exist: {entry.destination}")
        
        # Check if source already exists (shouldn't exist after move)
        if source_path.exists():
            raise RollbackError(f"Cannot reverse move: source already exists: {entry.source}")
        
        # Create source directory if needed
        source_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file back
        shutil.move(str(dest_path), str(source_path))
    
    def _reverse_link(self, entry: TransactionEntry):
        """
        Reverse a link operation (remove symbolic link).
        
        Args:
            entry: Transaction entry for the link operation
        """
        # For link: source is link path, destination is target path
        # To reverse: remove the link
        link_path = self.project_root / entry.source
        
        # Check if link exists
        if not link_path.exists() and not link_path.is_symlink():
            # Link doesn't exist, nothing to do
            return
        
        # Verify it's actually a symbolic link
        if not link_path.is_symlink():
            raise RollbackError(f"Cannot reverse link: path is not a symbolic link: {entry.source}")
        
        # Remove the symbolic link
        link_path.unlink()
    
    def _reverse_delete(self, entry: TransactionEntry, backup_path: Optional[str] = None):
        """
        Reverse a delete operation (restore file from backup).
        
        Args:
            entry: Transaction entry for the delete operation
            backup_path: Path to backup directory
        """
        if not backup_path:
            raise RollbackError("Cannot reverse delete: no backup path provided")
        
        backup_root = Path(backup_path)
        if not backup_root.exists():
            raise RollbackError(f"Backup directory does not exist: {backup_path}")
        
        # For delete: source is the deleted file path
        # To reverse: restore from backup
        deleted_file = self.project_root / entry.source
        backup_file = backup_root / entry.source
        
        # Check if backup file exists
        if not backup_file.exists():
            raise RollbackError(f"Cannot restore: file not found in backup: {entry.source}")
        
        # Check if file already exists at destination
        if deleted_file.exists():
            raise RollbackError(f"Cannot restore: file already exists: {entry.source}")
        
        # Create directory if needed
        deleted_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file from backup
        shutil.copy2(str(backup_file), str(deleted_file))
    
    def verify_rollback(self, backup_path: str) -> Dict:
        """
        Verify that rollback was successful by comparing with backup.
        
        Args:
            backup_path: Path to the backup directory
        
        Returns:
            Dictionary with verification results
        """
        backup_root = Path(backup_path)
        
        if not backup_root.exists():
            raise RollbackError(f"Backup directory does not exist: {backup_path}")
        
        results = {
            'success': True,
            'files_checked': 0,
            'files_match': 0,
            'files_differ': 0,
            'missing_files': [],
            'differing_files': [],
        }
        
        # Get all files from backup
        backup_files = []
        for item in backup_root.rglob('*'):
            if item.is_file():
                try:
                    relative_path = item.relative_to(backup_root)
                    backup_files.append(relative_path)
                except ValueError:
                    continue
        
        # Check each file
        for relative_path in backup_files:
            results['files_checked'] += 1
            
            current_file = self.project_root / relative_path
            backup_file = backup_root / relative_path
            
            # Check if file exists
            if not current_file.exists():
                results['missing_files'].append(str(relative_path))
                results['files_differ'] += 1
                results['success'] = False
                continue
            
            # Compare file sizes
            if current_file.stat().st_size != backup_file.stat().st_size:
                results['differing_files'].append(str(relative_path))
                results['files_differ'] += 1
                results['success'] = False
                continue
            
            # Files match
            results['files_match'] += 1
        
        return results
    
    def generate_rollback_report(self, rollback_results: Dict, verification_results: Optional[Dict] = None) -> str:
        """
        Generate a human-readable rollback report.
        
        Args:
            rollback_results: Results from execute_rollback
            verification_results: Optional results from verify_rollback
        
        Returns:
            Rollback report as string
        """
        lines = [
            "# Rollback Report",
            "",
            f"**Status**: {'✅ SUCCESS' if rollback_results['success'] else '❌ FAILED'}",
            f"**Duration**: {rollback_results.get('duration', 0):.2f} seconds",
            "",
            "## Rollback Statistics",
            f"- Total Operations: {rollback_results['total_operations']}",
            f"- Successfully Reversed: {rollback_results['reversed']}",
            f"- Failed: {rollback_results['failed']}",
            "",
        ]
        
        # Errors
        if rollback_results['errors']:
            lines.append("## Errors")
            for error in rollback_results['errors']:
                lines.append(f"- ❌ {error}")
            lines.append("")
        
        # Verification results
        if verification_results:
            lines.append("## Verification Results")
            if verification_results['success']:
                lines.append("✅ All files match backup")
            else:
                lines.append("❌ Some files do not match backup")
            lines.append("")
            lines.append(f"- Files Checked: {verification_results['files_checked']}")
            lines.append(f"- Files Match: {verification_results['files_match']}")
            lines.append(f"- Files Differ: {verification_results['files_differ']}")
            lines.append("")
            
            if verification_results['missing_files']:
                lines.append("### Missing Files")
                for file in verification_results['missing_files']:
                    lines.append(f"- {file}")
                lines.append("")
            
            if verification_results['differing_files']:
                lines.append("### Differing Files")
                for file in verification_results['differing_files']:
                    lines.append(f"- {file}")
                lines.append("")
        
        # Rollback log
        if self.rollback_log:
            lines.append("## Rollback Operations")
            for entry in self.rollback_log:
                status = "✅" if entry['success'] else "❌"
                lines.append(f"- {status} {entry['operation']}: {entry['source']}")
                if not entry['success']:
                    lines.append(f"  Error: {entry.get('error', 'Unknown error')}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_rollback_summary(self, rollback_results: Dict) -> Dict:
        """
        Get rollback summary as dictionary.
        
        Args:
            rollback_results: Results from execute_rollback
        
        Returns:
            Dictionary with rollback summary
        """
        return {
            'success': rollback_results['success'],
            'total_operations': rollback_results['total_operations'],
            'reversed': rollback_results['reversed'],
            'failed': rollback_results['failed'],
            'error_count': len(rollback_results['errors']),
            'duration_seconds': rollback_results.get('duration', 0),
            'start_time': rollback_results['start_time'].isoformat(),
            'end_time': rollback_results['end_time'].isoformat(),
        }
    
    def can_rollback(self, transaction_log_path: str) -> Dict:
        """
        Check if rollback is possible.
        
        Args:
            transaction_log_path: Path to the transaction log file
        
        Returns:
            Dictionary with rollback feasibility information
        """
        try:
            transaction_log = TransactionLog(transaction_log_path)
            transaction_log.load_log()
        except Exception as e:
            return {
                'can_rollback': False,
                'reason': f"Cannot load transaction log: {e}",
            }
        
        operations = transaction_log.get_operations()
        
        if not operations:
            return {
                'can_rollback': False,
                'reason': "No operations found in transaction log",
            }
        
        return {
            'can_rollback': True,
            'operation_count': len(operations),
            'operations_by_type': transaction_log.count_operations(),
        }
