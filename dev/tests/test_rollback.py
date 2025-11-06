"""
Unit tests for the rollback service.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from reorg_tool.rollback import RollbackService
from reorg_tool.transaction_log import TransactionLog
from reorg_tool.mover import FileMover
from reorg_tool.linker import SymbolicLinker
from reorg_tool.exceptions import RollbackError


@pytest.fixture
def temp_project():
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create test directory structure
    project_root = Path(temp_dir) / "test_project"
    project_root.mkdir()
    
    # Create some test files
    (project_root / "file1.txt").write_text("content1")
    (project_root / "file2.txt").write_text("content2")
    (project_root / "file3.txt").write_text("content3")
    
    # Create subdirectories
    (project_root / "dir1").mkdir()
    (project_root / "dir1" / "file4.txt").write_text("content4")
    
    (project_root / "dir2").mkdir()
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def backup_dir(temp_project):
    """Create a backup of the project."""
    backup_path = temp_project.parent / "backup"
    shutil.copytree(temp_project, backup_path)
    yield backup_path
    # Cleanup handled by temp_project fixture


@pytest.fixture
def rollback_service(temp_project):
    """Create a RollbackService instance for testing."""
    return RollbackService(str(temp_project))


@pytest.fixture
def transaction_log(temp_project):
    """Create a TransactionLog instance for testing."""
    log_path = temp_project / ".transaction_log.json"
    return TransactionLog(str(log_path))


class TestRollbackServiceInit:
    """Test RollbackService initialization."""
    
    def test_init_with_valid_path(self, temp_project):
        """Test initialization with valid project root."""
        service = RollbackService(str(temp_project))
        assert service.project_root == temp_project
        assert service.rollback_log == []
    
    def test_init_with_invalid_path(self):
        """Test initialization with invalid project root."""
        with pytest.raises(RollbackError):
            RollbackService("/nonexistent/path")


class TestReverseMove:
    """Test reversing move operations."""
    
    def test_reverse_move_basic(self, rollback_service, temp_project, transaction_log):
        """Test reversing a basic move operation."""
        # Perform a move
        mover = FileMover(str(temp_project), transaction_log)
        mover.move_file("file1.txt", "dir2/file1.txt")
        
        # Verify file was moved
        assert not (temp_project / "file1.txt").exists()
        assert (temp_project / "dir2" / "file1.txt").exists()
        
        # Get the move entry
        entries = transaction_log.get_operations(operation_type='move')
        assert len(entries) == 1
        
        # Reverse the move
        rollback_service._reverse_move(entries[0])
        
        # Verify file was moved back
        assert (temp_project / "file1.txt").exists()
        assert not (temp_project / "dir2" / "file1.txt").exists()
    
    def test_reverse_move_nonexistent_destination(self, rollback_service, transaction_log):
        """Test reversing move when destination doesn't exist."""
        # Create a fake entry
        entry = transaction_log.log_operation('move', 'file1.txt', 'dir2/file1.txt')
        
        # Remove the destination file
        # (it doesn't exist in this case)
        
        # Should raise error
        with pytest.raises(RollbackError) as exc_info:
            rollback_service._reverse_move(entry)
        
        assert "destination does not exist" in str(exc_info.value)
    
    def test_reverse_move_source_already_exists(self, rollback_service, temp_project, transaction_log):
        """Test reversing move when source already exists."""
        # Move file
        mover = FileMover(str(temp_project), transaction_log)
        mover.move_file("file1.txt", "dir2/file1.txt")
        
        # Recreate source file
        (temp_project / "file1.txt").write_text("new content")
        
        # Get the move entry
        entries = transaction_log.get_operations(operation_type='move')
        
        # Should raise error
        with pytest.raises(RollbackError) as exc_info:
            rollback_service._reverse_move(entries[0])
        
        assert "source already exists" in str(exc_info.value)


class TestReverseLink:
    """Test reversing link operations."""
    
    def test_reverse_link_basic(self, rollback_service, temp_project, transaction_log):
        """Test reversing a basic link operation."""
        # Create a link
        linker = SymbolicLinker(str(temp_project), transaction_log)
        linker.create_link("link.txt", "file1.txt")
        
        # Verify link exists
        assert (temp_project / "link.txt").is_symlink()
        
        # Get the link entry
        entries = transaction_log.get_operations(operation_type='link')
        assert len(entries) == 1
        
        # Reverse the link
        rollback_service._reverse_link(entries[0])
        
        # Verify link was removed
        assert not (temp_project / "link.txt").exists()
    
    def test_reverse_link_nonexistent(self, rollback_service, transaction_log):
        """Test reversing link that doesn't exist."""
        # Create a fake entry
        entry = transaction_log.log_operation('link', 'nonexistent_link.txt', 'file1.txt')
        
        # Should not raise error (link doesn't exist, nothing to do)
        rollback_service._reverse_link(entry)
    
    def test_reverse_link_not_a_symlink(self, rollback_service, temp_project, transaction_log):
        """Test reversing when path is not a symbolic link."""
        # Create a fake entry pointing to a regular file
        entry = transaction_log.log_operation('link', 'file1.txt', 'file2.txt')
        
        # Should raise error
        with pytest.raises(RollbackError) as exc_info:
            rollback_service._reverse_link(entry)
        
        assert "not a symbolic link" in str(exc_info.value)


class TestReverseDelete:
    """Test reversing delete operations."""
    
    def test_reverse_delete_basic(self, rollback_service, temp_project, backup_dir, transaction_log):
        """Test reversing a basic delete operation."""
        # Delete a file
        (temp_project / "file1.txt").unlink()
        transaction_log.log_operation('delete', 'file1.txt')
        
        # Verify file is deleted
        assert not (temp_project / "file1.txt").exists()
        
        # Get the delete entry
        entries = transaction_log.get_operations(operation_type='delete')
        assert len(entries) == 1
        
        # Reverse the delete
        rollback_service._reverse_delete(entries[0], str(backup_dir))
        
        # Verify file was restored
        assert (temp_project / "file1.txt").exists()
        assert (temp_project / "file1.txt").read_text() == "content1"
    
    def test_reverse_delete_no_backup(self, rollback_service, transaction_log):
        """Test reversing delete without backup path."""
        entry = transaction_log.log_operation('delete', 'file1.txt')
        
        # Should raise error
        with pytest.raises(RollbackError) as exc_info:
            rollback_service._reverse_delete(entry, None)
        
        assert "no backup path" in str(exc_info.value)
    
    def test_reverse_delete_backup_not_found(self, rollback_service, transaction_log):
        """Test reversing delete when backup doesn't exist."""
        entry = transaction_log.log_operation('delete', 'file1.txt')
        
        # Should raise error
        with pytest.raises(RollbackError) as exc_info:
            rollback_service._reverse_delete(entry, "/nonexistent/backup")
        
        assert "does not exist" in str(exc_info.value)
    
    def test_reverse_delete_file_not_in_backup(self, rollback_service, backup_dir, transaction_log):
        """Test reversing delete when file not in backup."""
        entry = transaction_log.log_operation('delete', 'nonexistent.txt')
        
        # Should raise error
        with pytest.raises(RollbackError) as exc_info:
            rollback_service._reverse_delete(entry, str(backup_dir))
        
        assert "not found in backup" in str(exc_info.value)


class TestExecuteRollback:
    """Test complete rollback execution."""
    
    def test_execute_rollback_move_operations(self, rollback_service, temp_project, transaction_log):
        """Test rollback of move operations."""
        # Perform some moves
        mover = FileMover(str(temp_project), transaction_log)
        mover.move_file("file1.txt", "dir2/file1.txt")
        mover.move_file("file2.txt", "dir2/file2.txt")
        
        # Save the log
        transaction_log.save()
        
        # Execute rollback
        results = rollback_service.execute_rollback(str(transaction_log.log_path))
        
        assert results['success'] is True
        assert results['total_operations'] == 2
        assert results['reversed'] == 2
        assert results['failed'] == 0
        
        # Verify files are back
        assert (temp_project / "file1.txt").exists()
        assert (temp_project / "file2.txt").exists()
        assert not (temp_project / "dir2" / "file1.txt").exists()
    
    def test_execute_rollback_link_operations(self, rollback_service, temp_project, transaction_log):
        """Test rollback of link operations."""
        # Create some links
        linker = SymbolicLinker(str(temp_project), transaction_log)
        linker.create_link("link1.txt", "file1.txt")
        linker.create_link("link2.txt", "file2.txt")
        
        # Save the log
        transaction_log.save()
        
        # Execute rollback
        results = rollback_service.execute_rollback(str(transaction_log.log_path))
        
        assert results['success'] is True
        assert results['reversed'] == 2
        
        # Verify links are removed
        assert not (temp_project / "link1.txt").exists()
        assert not (temp_project / "link2.txt").exists()
    
    def test_execute_rollback_mixed_operations(self, rollback_service, temp_project, transaction_log, backup_dir):
        """Test rollback of mixed operations."""
        # Perform various operations
        mover = FileMover(str(temp_project), transaction_log)
        linker = SymbolicLinker(str(temp_project), transaction_log)
        
        mover.move_file("file1.txt", "dir2/file1.txt")
        linker.create_link("link.txt", "file2.txt")
        
        # Delete a file
        (temp_project / "file3.txt").unlink()
        transaction_log.log_operation('delete', 'file3.txt')
        
        # Save the log
        transaction_log.save()
        
        # Execute rollback
        results = rollback_service.execute_rollback(
            str(transaction_log.log_path),
            backup_path=str(backup_dir)
        )
        
        assert results['success'] is True
        assert results['total_operations'] == 3
        assert results['reversed'] == 3
        
        # Verify all operations reversed
        assert (temp_project / "file1.txt").exists()
        assert not (temp_project / "link.txt").exists()
        assert (temp_project / "file3.txt").exists()
    
    def test_execute_rollback_with_failures(self, rollback_service, temp_project, transaction_log):
        """Test rollback with some failures."""
        # Create operations
        mover = FileMover(str(temp_project), transaction_log)
        mover.move_file("file1.txt", "dir2/file1.txt")
        
        # Manually remove the moved file to cause failure
        (temp_project / "dir2" / "file1.txt").unlink()
        
        # Save the log
        transaction_log.save()
        
        # Execute rollback
        results = rollback_service.execute_rollback(str(transaction_log.log_path))
        
        assert results['success'] is False
        assert results['failed'] == 1
        assert len(results['errors']) == 1
    
    def test_execute_rollback_invalid_log(self, rollback_service):
        """Test rollback with invalid transaction log."""
        with pytest.raises(RollbackError) as exc_info:
            rollback_service.execute_rollback("/nonexistent/log.json")
        
        assert "Failed to load transaction log" in str(exc_info.value)


class TestVerifyRollback:
    """Test rollback verification."""
    
    def test_verify_rollback_success(self, rollback_service, temp_project, backup_dir):
        """Test verification when rollback is successful."""
        results = rollback_service.verify_rollback(str(backup_dir))
        
        assert results['success'] is True
        assert results['files_checked'] > 0
        assert results['files_match'] == results['files_checked']
        assert results['files_differ'] == 0
        assert len(results['missing_files']) == 0
    
    def test_verify_rollback_missing_file(self, rollback_service, temp_project, backup_dir):
        """Test verification when file is missing."""
        # Remove a file
        (temp_project / "file1.txt").unlink()
        
        results = rollback_service.verify_rollback(str(backup_dir))
        
        assert results['success'] is False
        assert results['files_differ'] > 0
        assert 'file1.txt' in results['missing_files']
    
    def test_verify_rollback_different_file(self, rollback_service, temp_project, backup_dir):
        """Test verification when file differs."""
        # Modify a file
        (temp_project / "file1.txt").write_text("modified content that is longer")
        
        results = rollback_service.verify_rollback(str(backup_dir))
        
        assert results['success'] is False
        assert results['files_differ'] > 0
        assert 'file1.txt' in results['differing_files']
    
    def test_verify_rollback_invalid_backup(self, rollback_service):
        """Test verification with invalid backup path."""
        with pytest.raises(RollbackError) as exc_info:
            rollback_service.verify_rollback("/nonexistent/backup")
        
        assert "does not exist" in str(exc_info.value)


class TestGenerateRollbackReport:
    """Test rollback report generation."""
    
    def test_generate_report_success(self, rollback_service):
        """Test generating report for successful rollback."""
        rollback_results = {
            'success': True,
            'total_operations': 5,
            'reversed': 5,
            'failed': 0,
            'errors': [],
            'duration': 1.5,
        }
        
        report = rollback_service.generate_rollback_report(rollback_results)
        
        assert "# Rollback Report" in report
        assert "✅ SUCCESS" in report
        assert "Total Operations: 5" in report
        assert "Successfully Reversed: 5" in report
    
    def test_generate_report_with_errors(self, rollback_service):
        """Test generating report with errors."""
        rollback_results = {
            'success': False,
            'total_operations': 5,
            'reversed': 3,
            'failed': 2,
            'errors': ['Error 1', 'Error 2'],
            'duration': 2.0,
        }
        
        report = rollback_service.generate_rollback_report(rollback_results)
        
        assert "❌ FAILED" in report
        assert "## Errors" in report
        assert "Error 1" in report
        assert "Error 2" in report
    
    def test_generate_report_with_verification(self, rollback_service):
        """Test generating report with verification results."""
        rollback_results = {
            'success': True,
            'total_operations': 3,
            'reversed': 3,
            'failed': 0,
            'errors': [],
            'duration': 1.0,
        }
        
        verification_results = {
            'success': True,
            'files_checked': 10,
            'files_match': 10,
            'files_differ': 0,
            'missing_files': [],
            'differing_files': [],
        }
        
        report = rollback_service.generate_rollback_report(
            rollback_results,
            verification_results
        )
        
        assert "## Verification Results" in report
        assert "✅ All files match backup" in report
        assert "Files Checked: 10" in report


class TestGetRollbackSummary:
    """Test rollback summary generation."""
    
    def test_get_summary(self, rollback_service):
        """Test getting rollback summary."""
        rollback_results = {
            'success': True,
            'total_operations': 5,
            'reversed': 5,
            'failed': 0,
            'errors': [],
            'duration': 1.5,
            'start_time': datetime.now(),
            'end_time': datetime.now(),
        }
        
        summary = rollback_service.get_rollback_summary(rollback_results)
        
        assert summary['success'] is True
        assert summary['total_operations'] == 5
        assert summary['reversed'] == 5
        assert summary['failed'] == 0
        assert 'start_time' in summary
        assert 'end_time' in summary


class TestCanRollback:
    """Test rollback feasibility check."""
    
    def test_can_rollback_valid_log(self, rollback_service, temp_project, transaction_log):
        """Test checking rollback with valid log."""
        # Add some operations
        transaction_log.log_operation('move', 'file1.txt', 'dir2/file1.txt')
        transaction_log.save()
        
        result = rollback_service.can_rollback(str(transaction_log.log_path))
        
        assert result['can_rollback'] is True
        assert result['operation_count'] == 1
    
    def test_can_rollback_empty_log(self, rollback_service, temp_project, transaction_log):
        """Test checking rollback with empty log."""
        transaction_log.save()
        
        result = rollback_service.can_rollback(str(transaction_log.log_path))
        
        assert result['can_rollback'] is False
        assert "No operations" in result['reason']
    
    def test_can_rollback_invalid_log(self, rollback_service):
        """Test checking rollback with invalid log."""
        result = rollback_service.can_rollback("/nonexistent/log.json")
        
        assert result['can_rollback'] is False
        assert "Cannot load" in result['reason']
