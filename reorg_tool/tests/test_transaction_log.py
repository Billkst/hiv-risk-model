"""
Unit tests for the TransactionLog module.
"""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

from reorg_tool.transaction_log import TransactionLog
from reorg_tool.models import TransactionEntry
from reorg_tool.exceptions import FileOperationError


class TestTransactionLog:
    """Test cases for TransactionLog class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for log files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def log_path(self, temp_dir):
        """Create a log file path."""
        return str(Path(temp_dir) / "transaction.log")
    
    @pytest.fixture
    def transaction_log(self, log_path):
        """Create a TransactionLog instance."""
        return TransactionLog(log_path)
    
    def test_transaction_log_initialization(self, transaction_log, log_path):
        """Test TransactionLog initialization."""
        assert transaction_log is not None
        assert transaction_log.log_path == Path(log_path)
        assert len(transaction_log.entries) == 0
        assert transaction_log.reorganization_id.startswith("reorg_")
    
    def test_log_operation(self, transaction_log):
        """Test logging an operation."""
        entry = transaction_log.log_operation(
            operation='move',
            source='file1.txt',
            destination='new/file1.txt',
            success=True
        )
        
        assert entry is not None
        assert entry.operation == 'move'
        assert entry.source == 'file1.txt'
        assert entry.destination == 'new/file1.txt'
        assert entry.success is True
        assert len(transaction_log) == 1
    
    def test_log_multiple_operations(self, transaction_log):
        """Test logging multiple operations."""
        transaction_log.log_operation('move', 'file1.txt', 'new/file1.txt')
        transaction_log.log_operation('link', 'file1.txt', 'old/file1.txt')
        transaction_log.log_operation('delete', 'temp.txt')
        
        assert len(transaction_log) == 3
    
    def test_log_failed_operation(self, transaction_log):
        """Test logging a failed operation."""
        entry = transaction_log.log_operation(
            operation='move',
            source='file1.txt',
            destination='new/file1.txt',
            success=False,
            error_message='Permission denied'
        )
        
        assert entry.success is False
        assert entry.error_message == 'Permission denied'
    
    def test_save_and_load_log(self, transaction_log, log_path):
        """Test saving and loading transaction log."""
        # Log some operations
        transaction_log.log_operation('move', 'file1.txt', 'new/file1.txt')
        transaction_log.log_operation('link', 'file2.txt', 'old/file2.txt')
        
        # Create new log instance and load
        new_log = TransactionLog(log_path)
        new_log.load_log()
        
        # Should have same entries
        assert len(new_log) == 2
        assert new_log.reorganization_id == transaction_log.reorganization_id
        assert new_log.entries[0].operation == 'move'
        assert new_log.entries[1].operation == 'link'
    
    def test_load_nonexistent_log(self, temp_dir):
        """Test loading a nonexistent log file."""
        log_path = str(Path(temp_dir) / "nonexistent.log")
        log = TransactionLog(log_path)
        
        with pytest.raises(FileOperationError):
            log.load_log()
    
    def test_get_operations(self, transaction_log):
        """Test getting operations with filters."""
        transaction_log.log_operation('move', 'file1.txt', 'new/file1.txt')
        transaction_log.log_operation('link', 'file2.txt', 'old/file2.txt')
        transaction_log.log_operation('move', 'file3.txt', 'new/file3.txt')
        transaction_log.log_operation('delete', 'temp.txt')
        
        # Get all operations
        all_ops = transaction_log.get_operations()
        assert len(all_ops) == 4
        
        # Get only move operations
        move_ops = transaction_log.get_operations(operation_type='move')
        assert len(move_ops) == 2
        assert all(op.operation == 'move' for op in move_ops)
        
        # Get only link operations
        link_ops = transaction_log.get_operations(operation_type='link')
        assert len(link_ops) == 1
    
    def test_get_operations_success_only(self, transaction_log):
        """Test getting only successful operations."""
        transaction_log.log_operation('move', 'file1.txt', 'new/file1.txt', success=True)
        transaction_log.log_operation('move', 'file2.txt', 'new/file2.txt', success=False)
        transaction_log.log_operation('link', 'file3.txt', 'old/file3.txt', success=True)
        
        success_ops = transaction_log.get_operations(success_only=True)
        assert len(success_ops) == 2
        assert all(op.success for op in success_ops)
    
    def test_get_failed_operations(self, transaction_log):
        """Test getting failed operations."""
        transaction_log.log_operation('move', 'file1.txt', 'new/file1.txt', success=True)
        transaction_log.log_operation('move', 'file2.txt', 'new/file2.txt', success=False, error_message='Error 1')
        transaction_log.log_operation('link', 'file3.txt', 'old/file3.txt', success=False, error_message='Error 2')
        
        failed_ops = transaction_log.get_failed_operations()
        assert len(failed_ops) == 2
        assert all(not op.success for op in failed_ops)
    
    def test_get_operations_for_file(self, transaction_log):
        """Test getting operations for a specific file."""
        transaction_log.log_operation('move', 'file1.txt', 'new/file1.txt')
        transaction_log.log_operation('link', 'file1.txt', 'old/file1.txt')
        transaction_log.log_operation('move', 'file2.txt', 'new/file2.txt')
        
        file1_ops = transaction_log.get_operations_for_file('file1.txt')
        assert len(file1_ops) == 2
    
    def test_get_reverse_operations(self, transaction_log):
        """Test getting operations in reverse order."""
        transaction_log.log_operation('move', 'file1.txt', 'new/file1.txt')
        transaction_log.log_operation('link', 'file2.txt', 'old/file2.txt')
        transaction_log.log_operation('delete', 'temp.txt')
        
        reverse_ops = transaction_log.get_reverse_operations()
        
        assert len(reverse_ops) == 3
        assert reverse_ops[0].operation == 'delete'
        assert reverse_ops[1].operation == 'link'
        assert reverse_ops[2].operation == 'move'
    
    def test_count_operations(self, transaction_log):
        """Test counting operations."""
        transaction_log.log_operation('move', 'file1.txt', 'new/file1.txt', success=True)
        transaction_log.log_operation('move', 'file2.txt', 'new/file2.txt', success=False)
        transaction_log.log_operation('link', 'file3.txt', 'old/file3.txt', success=True)
        transaction_log.log_operation('delete', 'temp.txt', success=True)
        
        counts = transaction_log.count_operations()
        
        assert counts['total'] == 4
        assert counts['move'] == 2
        assert counts['link'] == 1
        assert counts['delete'] == 1
        assert counts['success'] == 3
        assert counts['failed'] == 1
    
    def test_generate_summary(self, transaction_log):
        """Test generating summary."""
        transaction_log.log_operation('move', 'file1.txt', 'new/file1.txt')
        transaction_log.log_operation('link', 'file2.txt', 'old/file2.txt')
        
        summary = transaction_log.generate_summary()
        
        assert "Transaction Log Summary" in summary
        assert "Reorganization ID:" in summary
        assert "Total operations: 2" in summary
        assert "Move: 1" in summary
        assert "Link: 1" in summary
    
    def test_clear_log(self, transaction_log):
        """Test clearing the log."""
        transaction_log.log_operation('move', 'file1.txt', 'new/file1.txt')
        transaction_log.log_operation('link', 'file2.txt', 'old/file2.txt')
        
        assert len(transaction_log) == 2
        
        transaction_log.clear()
        
        assert len(transaction_log) == 0
    
    def test_log_with_checksums(self, transaction_log):
        """Test logging with checksums."""
        entry = transaction_log.log_operation(
            operation='move',
            source='file1.txt',
            destination='new/file1.txt',
            checksum_before='abc123',
            checksum_after='abc123'
        )
        
        assert entry.checksum_before == 'abc123'
        assert entry.checksum_after == 'abc123'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
