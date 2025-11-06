"""
Transaction log module for the reorganization system.

Records all file operations to support rollback.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from .models import TransactionEntry
from .exceptions import FileOperationError


class TransactionLog:
    """Records and manages transaction log for file operations."""
    
    def __init__(self, log_path: str):
        """
        Initialize the transaction log.
        
        Args:
            log_path: Path to the transaction log file
        """
        self.log_path = Path(log_path)
        self.entries: List[TransactionEntry] = []
        self.reorganization_id = f"reorg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        
        # Create log directory if it doesn't exist
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_operation(
        self,
        operation: str,
        source: str,
        destination: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        checksum_before: Optional[str] = None,
        checksum_after: Optional[str] = None,
    ) -> TransactionEntry:
        """
        Log a file operation.
        
        Args:
            operation: Operation type ('move', 'link', 'delete')
            source: Source file path
            destination: Destination file path (for move/link)
            success: Whether operation succeeded
            error_message: Error message if failed
            checksum_before: MD5 checksum before operation
            checksum_after: MD5 checksum after operation
        
        Returns:
            TransactionEntry object
        """
        entry = TransactionEntry(
            timestamp=datetime.now(),
            operation=operation,
            source=source,
            destination=destination,
            success=success,
            error_message=error_message,
            checksum_before=checksum_before,
            checksum_after=checksum_after,
        )
        
        self.entries.append(entry)
        
        # Auto-save after each operation
        self.save()
        
        return entry
    
    def save(self):
        """Save transaction log to file."""
        try:
            log_data = {
                'reorganization_id': self.reorganization_id,
                'start_time': self.start_time.isoformat(),
                'operations': [entry.to_dict() for entry in self.entries],
            }
            
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            # Don't raise exception - just warn
            # This allows operations to continue even if logging fails
            print(f"Warning: Failed to save transaction log: {e}")
    
    def load_log(self, log_path: Optional[str] = None) -> 'TransactionLog':
        """
        Load transaction log from file.
        
        Args:
            log_path: Path to log file (defaults to self.log_path)
        
        Returns:
            Self for chaining
        """
        if log_path:
            self.log_path = Path(log_path)
        
        if not self.log_path.exists():
            raise FileOperationError(f"Log file does not exist: {self.log_path}")
        
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            self.reorganization_id = log_data.get('reorganization_id', '')
            self.start_time = datetime.fromisoformat(log_data.get('start_time', ''))
            
            self.entries = [
                TransactionEntry.from_dict(entry_dict)
                for entry_dict in log_data.get('operations', [])
            ]
            
            return self
        
        except Exception as e:
            raise FileOperationError(f"Failed to load transaction log: {e}")
    
    def get_operations(
        self,
        operation_type: Optional[str] = None,
        success_only: bool = False
    ) -> List[TransactionEntry]:
        """
        Get operations from the log.
        
        Args:
            operation_type: Filter by operation type ('move', 'link', 'delete')
            success_only: Only return successful operations
        
        Returns:
            List of TransactionEntry objects
        """
        filtered = self.entries
        
        if operation_type:
            filtered = [e for e in filtered if e.operation == operation_type]
        
        if success_only:
            filtered = [e for e in filtered if e.success]
        
        return filtered
    
    def get_failed_operations(self) -> List[TransactionEntry]:
        """
        Get all failed operations.
        
        Returns:
            List of failed TransactionEntry objects
        """
        return [e for e in self.entries if not e.success]
    
    def get_operations_for_file(self, file_path: str) -> List[TransactionEntry]:
        """
        Get all operations involving a specific file.
        
        Args:
            file_path: File path to search for
        
        Returns:
            List of TransactionEntry objects
        """
        return [
            e for e in self.entries
            if e.source == file_path or e.destination == file_path
        ]
    
    def get_reverse_operations(self) -> List[TransactionEntry]:
        """
        Get operations in reverse order for rollback.
        
        Returns:
            List of TransactionEntry objects in reverse order
        """
        return list(reversed(self.entries))
    
    def count_operations(self) -> dict:
        """
        Count operations by type.
        
        Returns:
            Dictionary with operation counts
        """
        counts = {
            'total': len(self.entries),
            'move': 0,
            'link': 0,
            'delete': 0,
            'success': 0,
            'failed': 0,
        }
        
        for entry in self.entries:
            counts[entry.operation] = counts.get(entry.operation, 0) + 1
            if entry.success:
                counts['success'] += 1
            else:
                counts['failed'] += 1
        
        return counts
    
    def generate_summary(self) -> str:
        """
        Generate a human-readable summary of the transaction log.
        
        Returns:
            Summary string
        """
        counts = self.count_operations()
        
        lines = [
            f"# Transaction Log Summary",
            f"",
            f"Reorganization ID: {self.reorganization_id}",
            f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## Operation Counts",
            f"Total operations: {counts['total']}",
            f"  - Move: {counts.get('move', 0)}",
            f"  - Link: {counts.get('link', 0)}",
            f"  - Delete: {counts.get('delete', 0)}",
            f"",
            f"Success: {counts['success']}",
            f"Failed: {counts['failed']}",
        ]
        
        # Add failed operations details
        failed = self.get_failed_operations()
        if failed:
            lines.append(f"")
            lines.append(f"## Failed Operations")
            for entry in failed:
                lines.append(
                    f"  - {entry.operation}: {entry.source} "
                    f"({entry.error_message})"
                )
        
        return "\n".join(lines)
    
    def clear(self):
        """Clear all entries from the log."""
        self.entries = []
        self.save()
    
    def __len__(self) -> int:
        """Return number of entries in the log."""
        return len(self.entries)
    
    def __repr__(self) -> str:
        """String representation of the transaction log."""
        return (
            f"TransactionLog(id={self.reorganization_id}, "
            f"entries={len(self.entries)})"
        )
