"""
Unit tests for the FileMover module.
"""

import tempfile
import shutil
from pathlib import Path
import pytest

from reorg_tool.mover import FileMover
from reorg_tool.transaction_log import TransactionLog
from reorg_tool.exceptions import FileOperationError


class TestFileMover:
    """Test cases for FileMover class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for testing."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir) / "test_project"
        project_root.mkdir()
        
        # Create test files
        (project_root / "file1.txt").write_text("content1")
        (project_root / "file2.py").write_text("print('hello')")
        
        # Create subdirectory with file
        subdir = project_root / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        
        yield str(project_root)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mover(self, temp_project):
        """Create a FileMover instance."""
        return FileMover(temp_project)
    
    @pytest.fixture
    def mover_with_log(self, temp_project):
        """Create a FileMover with transaction log."""
        log_path = Path(temp_project) / "transaction.log"
        transaction_log = TransactionLog(str(log_path))
        return FileMover(temp_project, transaction_log)
    
    def test_mover_initialization(self, mover, temp_project):
        """Test FileMover initialization."""
        assert mover is not None
        assert mover.project_root == Path(temp_project).resolve()
    
    def test_mover_invalid_root(self):
        """Test FileMover with invalid project root."""
        with pytest.raises(FileOperationError):
            FileMover("/nonexistent/path")
    
    def test_move_file(self, mover, temp_project):
        """Test moving a single file."""
        result = mover.move_file("file1.txt", "moved/file1.txt")
        
        # Check result
        assert result['success'] is True
        assert result['source'] == "file1.txt"
        assert result['destination'] == "moved/file1.txt"
        assert 'checksum' in result
        
        # Verify file was moved
        assert not (Path(temp_project) / "file1.txt").exists()
        assert (Path(temp_project) / "moved/file1.txt").exists()
        
        # Verify content
        content = (Path(temp_project) / "moved/file1.txt").read_text()
        assert content == "content1"
    
    def test_move_file_nonexistent_source(self, mover):
        """Test moving a nonexistent file."""
        with pytest.raises(FileOperationError):
            mover.move_file("nonexistent.txt", "moved/file.txt")
    
    def test_move_file_existing_destination(self, mover, temp_project):
        """Test moving to an existing destination."""
        # Create destination file
        dest_dir = Path(temp_project) / "moved"
        dest_dir.mkdir()
        (dest_dir / "file1.txt").write_text("existing")
        
        # Try to move
        with pytest.raises(FileOperationError):
            mover.move_file("file1.txt", "moved/file1.txt")
    
    def test_move_file_with_transaction_log(self, temp_project):
        """Test that FileMover accepts and stores a transaction log."""
        # Create mover with transaction log
        log_path = str(Path(temp_project) / "test.log")
        transaction_log = TransactionLog(log_path)
        mover = FileMover(temp_project, transaction_log)
        
        # Verify log is attached
        assert mover.transaction_log is transaction_log
        
        # Move file - should work with transaction_log attached
        result = mover.move_file("file1.txt", "moved/file1.txt")
        
        assert result['success'] is True
        
        # Verify file was moved
        assert not (Path(temp_project) / "file1.txt").exists()
        assert (Path(temp_project) / "moved/file1.txt").exists()
        
        # Note: The actual transaction logging integration is tested
        # in integration tests. This unit test just verifies that
        # FileMover can work with a TransactionLog instance.
    
    def test_move_batch(self, mover, temp_project):
        """Test moving multiple files."""
        moves = [
            ("file1.txt", "moved/file1.txt"),
            ("file2.py", "moved/file2.py"),
            ("subdir/file3.txt", "moved/file3.txt"),
        ]
        
        result = mover.move_batch(moves)
        
        assert result['total'] == 3
        assert result['success'] == 3
        assert result['failed'] == 0
        assert len(result['errors']) == 0
        
        # Verify all files were moved
        assert (Path(temp_project) / "moved/file1.txt").exists()
        assert (Path(temp_project) / "moved/file2.py").exists()
        assert (Path(temp_project) / "moved/file3.txt").exists()
    
    def test_move_batch_with_errors(self, mover):
        """Test batch move with some failures."""
        moves = [
            ("file1.txt", "moved/file1.txt"),
            ("nonexistent.txt", "moved/nonexistent.txt"),  # Will fail
            ("file2.py", "moved/file2.py"),
        ]
        
        result = mover.move_batch(moves)
        
        assert result['total'] == 3
        assert result['success'] == 2
        assert result['failed'] == 1
        assert len(result['errors']) == 1
    
    def test_preserve_permissions(self, mover, temp_project):
        """Test preserving file permissions."""
        # Move file
        mover.move_file("file1.txt", "moved/file1.txt")
        
        # Preserve permissions (in this case, they're already preserved by copy2)
        # This test mainly checks the method doesn't error
        mover.preserve_permissions("file2.py", "file2.py")
    
    def test_verify_move(self, mover, temp_project):
        """Test verifying a move operation."""
        # Before move
        assert not mover.verify_move("file1.txt", "moved/file1.txt")
        
        # After move
        mover.move_file("file1.txt", "moved/file1.txt")
        assert mover.verify_move("file1.txt", "moved/file1.txt")
    
    def test_rollback_move(self, mover, temp_project):
        """Test rolling back a move operation."""
        # Move file
        mover.move_file("file1.txt", "moved/file1.txt")
        
        # Verify moved
        assert not (Path(temp_project) / "file1.txt").exists()
        assert (Path(temp_project) / "moved/file1.txt").exists()
        
        # Rollback
        success = mover.rollback_move("file1.txt", "moved/file1.txt")
        assert success is True
        
        # Verify rolled back
        assert (Path(temp_project) / "file1.txt").exists()
        assert not (Path(temp_project) / "moved/file1.txt").exists()
    
    def test_checksum_verification(self, mover, temp_project):
        """Test that checksum verification works."""
        # Move file
        result = mover.move_file("file1.txt", "moved/file1.txt")
        
        # Calculate checksum of moved file
        moved_path = Path(temp_project) / "moved/file1.txt"
        checksum = mover._calculate_checksum(moved_path)
        
        # Should match the checksum in result
        assert checksum == result['checksum']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
