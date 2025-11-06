"""
Unit tests for the BackupService module.
"""

import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
import pytest

from reorg_tool.backup import BackupService
from reorg_tool.exceptions import FileOperationError


class TestBackupService:
    """Test cases for BackupService class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for testing."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir) / "test_project"
        project_root.mkdir()
        
        # Create some test files
        (project_root / "file1.txt").write_text("content1")
        (project_root / "file2.py").write_text("print('hello')")
        (project_root / "requirements.txt").write_text("pytest\nchardet")
        (project_root / "README.md").write_text("# Test Project")
        
        # Create subdirectory
        subdir = project_root / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        
        # Create __pycache__ (should be ignored)
        pycache = project_root / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").write_text("bytecode")
        
        yield str(project_root)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def backup_service(self, temp_project):
        """Create a BackupService instance."""
        return BackupService(temp_project)
    
    def test_backup_service_initialization(self, backup_service, temp_project):
        """Test BackupService initialization."""
        assert backup_service is not None
        assert backup_service.project_root == Path(temp_project).resolve()
        assert backup_service.backup_dir.exists()
    
    def test_backup_service_invalid_root(self):
        """Test BackupService with invalid project root."""
        with pytest.raises(FileOperationError):
            BackupService("/nonexistent/path")
    
    def test_create_backup(self, backup_service, temp_project):
        """Test backup creation."""
        backup_path = backup_service.create_backup()
        
        # Backup should exist
        assert Path(backup_path).exists()
        assert Path(backup_path).is_dir()
        
        # Backup should contain files
        backup_files = list(Path(backup_path).rglob("*"))
        assert len(backup_files) > 0
        
        # Check specific files exist
        assert (Path(backup_path) / "file1.txt").exists()
        assert (Path(backup_path) / "requirements.txt").exists()
        assert (Path(backup_path) / "README.md").exists()
        
        # __pycache__ should be ignored
        assert not (Path(backup_path) / "__pycache__").exists()
        
        # Cleanup
        shutil.rmtree(backup_path)
    
    def test_create_backup_custom_name(self, backup_service):
        """Test backup creation with custom name."""
        custom_name = "my_custom_backup"
        backup_path = backup_service.create_backup(custom_name)
        
        assert custom_name in backup_path
        assert Path(backup_path).exists()
        
        # Cleanup
        shutil.rmtree(backup_path)
    
    def test_create_backup_duplicate_name(self, backup_service):
        """Test that duplicate backup names raise error."""
        backup_name = "test_backup"
        backup_path = backup_service.create_backup(backup_name)
        
        # Try to create again with same name
        with pytest.raises(FileOperationError):
            backup_service.create_backup(backup_name)
        
        # Cleanup
        shutil.rmtree(backup_path)
    
    def test_verify_backup(self, backup_service):
        """Test backup verification."""
        backup_path = backup_service.create_backup()
        
        # Verification should pass
        assert backup_service.verify_backup(backup_path) is True
        
        # Cleanup
        shutil.rmtree(backup_path)
    
    def test_verify_nonexistent_backup(self, backup_service):
        """Test verification of nonexistent backup."""
        result = backup_service.verify_backup("/nonexistent/backup")
        assert result is False
    
    def test_calculate_checksum(self, backup_service, temp_project):
        """Test checksum calculation."""
        test_file = Path(temp_project) / "file1.txt"
        checksum = backup_service.calculate_checksum(str(test_file))
        
        # Should return a valid MD5 hash
        assert len(checksum) == 32
        assert all(c in '0123456789abcdef' for c in checksum)
    
    def test_list_backups(self, backup_service):
        """Test listing backups."""
        # Create a couple of backups with proper naming
        backup1 = backup_service.create_backup()  # Use default naming
        time.sleep(1.1)  # Ensure different timestamps (need >1 second for timestamp format)
        backup2 = backup_service.create_backup()  # Use default naming
        
        # List backups
        backups = backup_service.list_backups()
        
        # Should find both backups
        assert len(backups) >= 2
        
        # Check backup info structure
        for backup in backups:
            assert 'path' in backup
            assert 'name' in backup
            assert 'created' in backup
            assert 'size_mb' in backup
        
        # Cleanup
        shutil.rmtree(backup1)
        shutil.rmtree(backup2)
    
    def test_cleanup_old_backups(self, backup_service, temp_project):
        """Test cleanup of old backups."""
        # Create a backup
        backup_path = backup_service.create_backup()
        
        # Modify its timestamp to make it old
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        Path(backup_path).touch()
        import os
        os.utime(backup_path, (old_time, old_time))
        
        # Cleanup with 7 day retention
        removed = backup_service.cleanup_old_backups(retention_days=7)
        
        # Old backup should be removed
        assert len(removed) > 0
        assert not Path(backup_path).exists()
    
    def test_restore_backup(self, backup_service, temp_project):
        """Test backup restoration."""
        # Create backup
        backup_path = backup_service.create_backup()
        
        # Create a new target directory
        restore_target = Path(temp_project).parent / "restored_project"
        
        # Restore backup
        backup_service.restore_backup(backup_path, str(restore_target))
        
        # Check restored files
        assert restore_target.exists()
        assert (restore_target / "file1.txt").exists()
        assert (restore_target / "requirements.txt").exists()
        
        # Cleanup
        shutil.rmtree(backup_path)
        shutil.rmtree(restore_target)
    
    def test_restore_to_nonempty_directory(self, backup_service, temp_project):
        """Test that restore fails for non-empty directory."""
        backup_path = backup_service.create_backup()
        
        # Try to restore to existing non-empty directory
        with pytest.raises(FileOperationError):
            backup_service.restore_backup(backup_path, temp_project)
        
        # Cleanup
        shutil.rmtree(backup_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
