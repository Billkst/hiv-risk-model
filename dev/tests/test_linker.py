"""
Unit tests for the symbolic linker module.
"""

import os
import pytest
from pathlib import Path
import tempfile
import shutil

from reorg_tool.linker import SymbolicLinker
from reorg_tool.transaction_log import TransactionLog
from reorg_tool.exceptions import FileOperationError


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
    
    # Create subdirectories
    (project_root / "subdir1").mkdir()
    (project_root / "subdir1" / "file3.txt").write_text("content3")
    
    (project_root / "subdir2").mkdir()
    (project_root / "subdir2" / "nested").mkdir()
    (project_root / "subdir2" / "nested" / "file4.txt").write_text("content4")
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def linker(temp_project):
    """Create a SymbolicLinker instance for testing."""
    return SymbolicLinker(str(temp_project))


@pytest.fixture
def linker_with_log(temp_project):
    """Create a SymbolicLinker with transaction log."""
    log_path = temp_project / ".reorg_transaction_log.json"
    transaction_log = TransactionLog(str(log_path))
    return SymbolicLinker(str(temp_project), transaction_log)


class TestSymbolicLinkerInit:
    """Test SymbolicLinker initialization."""
    
    def test_init_with_valid_path(self, temp_project):
        """Test initialization with valid project root."""
        linker = SymbolicLinker(str(temp_project))
        assert linker.project_root == temp_project
        assert linker.transaction_log is None
    
    def test_init_with_invalid_path(self):
        """Test initialization with invalid project root."""
        with pytest.raises(FileOperationError):
            SymbolicLinker("/nonexistent/path")
    
    def test_init_with_transaction_log(self, temp_project):
        """Test initialization with transaction log."""
        log_path = temp_project / "test.log"
        transaction_log = TransactionLog(str(log_path))
        linker = SymbolicLinker(str(temp_project), transaction_log)
        assert linker.transaction_log is transaction_log


class TestCalculateRelativePath:
    """Test relative path calculation."""
    
    def test_same_directory(self, linker):
        """Test relative path for files in same directory."""
        relative = linker.calculate_relative_path("link.txt", "file1.txt")
        assert relative == "file1.txt"
    
    def test_subdirectory_to_root(self, linker):
        """Test relative path from subdirectory to root."""
        relative = linker.calculate_relative_path("subdir1/link.txt", "file1.txt")
        assert relative == "../file1.txt"
    
    def test_root_to_subdirectory(self, linker):
        """Test relative path from root to subdirectory."""
        relative = linker.calculate_relative_path("link.txt", "subdir1/file3.txt")
        assert relative == "subdir1/file3.txt"
    
    def test_between_subdirectories(self, linker):
        """Test relative path between different subdirectories."""
        relative = linker.calculate_relative_path(
            "subdir1/link.txt",
            "subdir2/nested/file4.txt"
        )
        assert relative == "../subdir2/nested/file4.txt"
    
    def test_nested_to_nested(self, linker):
        """Test relative path between nested directories."""
        relative = linker.calculate_relative_path(
            "subdir2/nested/link.txt",
            "subdir1/file3.txt"
        )
        assert relative == "../../subdir1/file3.txt"


class TestCreateLink:
    """Test symbolic link creation."""
    
    def test_create_simple_link(self, linker):
        """Test creating a simple symbolic link."""
        result = linker.create_link("link_to_file1.txt", "file1.txt")
        
        assert result['success'] is True
        assert result['link_path'] == "link_to_file1.txt"
        assert result['target_path'] == "file1.txt"
        assert result['relative_path'] == "file1.txt"
        
        # Verify link exists
        link_path = linker.project_root / "link_to_file1.txt"
        assert link_path.is_symlink()
        assert link_path.read_text() == "content1"
    
    def test_create_link_to_subdirectory_file(self, linker):
        """Test creating link to file in subdirectory."""
        result = linker.create_link("link.txt", "subdir1/file3.txt")
        
        assert result['success'] is True
        assert result['relative_path'] == "subdir1/file3.txt"
        
        link_path = linker.project_root / "link.txt"
        assert link_path.is_symlink()
        assert link_path.read_text() == "content3"
    
    def test_create_link_in_subdirectory(self, linker):
        """Test creating link inside a subdirectory."""
        result = linker.create_link("subdir1/link.txt", "file1.txt")
        
        assert result['success'] is True
        assert result['relative_path'] == "../file1.txt"
        
        link_path = linker.project_root / "subdir1" / "link.txt"
        assert link_path.is_symlink()
        assert link_path.read_text() == "content1"
    
    def test_create_link_creates_parent_directory(self, linker):
        """Test that parent directories are created if needed."""
        result = linker.create_link("newdir/link.txt", "file1.txt")
        
        assert result['success'] is True
        
        link_path = linker.project_root / "newdir" / "link.txt"
        assert link_path.is_symlink()
        assert link_path.parent.exists()
    
    def test_create_link_to_nonexistent_target(self, linker):
        """Test creating link to nonexistent target fails."""
        with pytest.raises(FileOperationError) as exc_info:
            linker.create_link("link.txt", "nonexistent.txt")
        
        assert "Target does not exist" in str(exc_info.value)
    
    def test_create_link_at_existing_path(self, linker):
        """Test creating link at existing path fails."""
        with pytest.raises(FileOperationError) as exc_info:
            linker.create_link("file1.txt", "file2.txt")
        
        assert "already exists" in str(exc_info.value)
    
    def test_create_link_logs_to_transaction_log(self, linker_with_log):
        """Test that link creation is logged."""
        linker_with_log.create_link("link.txt", "file1.txt")
        
        operations = linker_with_log.transaction_log.get_operations(operation_type='link')
        assert len(operations) == 1
        assert operations[0].source == "link.txt"
        assert operations[0].destination == "file1.txt"
        assert operations[0].success is True
    
    def test_create_link_logs_failure(self, linker_with_log):
        """Test that failed link creation is logged."""
        with pytest.raises(FileOperationError):
            linker_with_log.create_link("link.txt", "nonexistent.txt")
        
        operations = linker_with_log.transaction_log.get_operations(operation_type='link')
        assert len(operations) == 1
        assert operations[0].success is False
        assert "does not exist" in operations[0].error_message


class TestVerifyLink:
    """Test symbolic link verification."""
    
    def test_verify_valid_link(self, linker):
        """Test verifying a valid symbolic link."""
        linker.create_link("link.txt", "file1.txt")
        assert linker.verify_link("link.txt") is True
    
    def test_verify_nonexistent_link(self, linker):
        """Test verifying nonexistent link returns False."""
        assert linker.verify_link("nonexistent_link.txt") is False
    
    def test_verify_regular_file(self, linker):
        """Test verifying regular file returns False."""
        assert linker.verify_link("file1.txt") is False
    
    def test_verify_broken_link(self, linker):
        """Test verifying broken link returns False."""
        # Create a link
        linker.create_link("link.txt", "file1.txt")
        
        # Remove the target
        (linker.project_root / "file1.txt").unlink()
        
        # Verify should fail
        assert linker.verify_link("link.txt") is False
    
    def test_verify_link_to_directory(self, linker):
        """Test verifying link to directory."""
        linker.create_link("link_dir", "subdir1")
        assert linker.verify_link("link_dir") is True


class TestCreateBatchLinks:
    """Test batch link creation."""
    
    def test_create_batch_all_success(self, linker):
        """Test creating multiple links successfully."""
        links = [
            ("link1.txt", "file1.txt"),
            ("link2.txt", "file2.txt"),
            ("link3.txt", "subdir1/file3.txt"),
        ]
        
        result = linker.create_batch_links(links)
        
        assert result['total'] == 3
        assert result['success'] == 3
        assert result['failed'] == 0
        assert len(result['errors']) == 0
        
        # Verify all links exist
        assert linker.verify_link("link1.txt")
        assert linker.verify_link("link2.txt")
        assert linker.verify_link("link3.txt")
    
    def test_create_batch_partial_failure(self, linker):
        """Test batch creation with some failures."""
        links = [
            ("link1.txt", "file1.txt"),
            ("link2.txt", "nonexistent.txt"),  # This will fail
            ("link3.txt", "file2.txt"),
        ]
        
        result = linker.create_batch_links(links)
        
        assert result['total'] == 3
        assert result['success'] == 2
        assert result['failed'] == 1
        assert len(result['errors']) == 1
        assert result['errors'][0]['link_path'] == "link2.txt"
    
    def test_create_batch_empty_list(self, linker):
        """Test batch creation with empty list."""
        result = linker.create_batch_links([])
        
        assert result['total'] == 0
        assert result['success'] == 0
        assert result['failed'] == 0


class TestGetLinkTarget:
    """Test getting link target."""
    
    def test_get_target_of_valid_link(self, linker):
        """Test getting target of valid link."""
        linker.create_link("link.txt", "file1.txt")
        target = linker.get_link_target("link.txt")
        assert target == "file1.txt"
    
    def test_get_target_of_nested_link(self, linker):
        """Test getting target of link in subdirectory."""
        linker.create_link("subdir1/link.txt", "file1.txt")
        target = linker.get_link_target("subdir1/link.txt")
        assert target == "file1.txt"
    
    def test_get_target_of_nonexistent_link(self, linker):
        """Test getting target of nonexistent link returns None."""
        target = linker.get_link_target("nonexistent.txt")
        assert target is None
    
    def test_get_target_of_regular_file(self, linker):
        """Test getting target of regular file returns None."""
        target = linker.get_link_target("file1.txt")
        assert target is None


class TestRemoveLink:
    """Test link removal."""
    
    def test_remove_existing_link(self, linker):
        """Test removing an existing link."""
        linker.create_link("link.txt", "file1.txt")
        assert linker.remove_link("link.txt") is True
        
        # Verify link is gone
        link_path = linker.project_root / "link.txt"
        assert not link_path.exists()
        
        # Verify target still exists
        assert (linker.project_root / "file1.txt").exists()
    
    def test_remove_nonexistent_link(self, linker):
        """Test removing nonexistent link returns False."""
        assert linker.remove_link("nonexistent.txt") is False
    
    def test_remove_regular_file(self, linker):
        """Test removing regular file returns False."""
        assert linker.remove_link("file1.txt") is False


class TestListLinks:
    """Test listing symbolic links."""
    
    def test_list_links_in_root(self, linker):
        """Test listing links in root directory."""
        linker.create_link("link1.txt", "file1.txt")
        linker.create_link("link2.txt", "file2.txt")
        
        links = linker.list_links()
        
        assert len(links) == 2
        link_paths = [link['link_path'] for link in links]
        assert "link1.txt" in link_paths
        assert "link2.txt" in link_paths
    
    def test_list_links_in_subdirectory(self, linker):
        """Test listing links in specific subdirectory."""
        linker.create_link("subdir1/link.txt", "file1.txt")
        linker.create_link("link.txt", "file2.txt")
        
        links = linker.list_links("subdir1")
        
        assert len(links) == 1
        assert links[0]['link_path'] == "subdir1/link.txt"
    
    def test_list_links_includes_validity(self, linker):
        """Test that list includes validity information."""
        linker.create_link("link.txt", "file1.txt")
        
        links = linker.list_links()
        
        assert len(links) == 1
        assert links[0]['is_valid'] is True
        assert links[0]['target_path'] == "file1.txt"
    
    def test_list_links_empty_directory(self, linker):
        """Test listing links in directory with no links."""
        links = linker.list_links()
        assert len(links) == 0


class TestVerifyAllLinks:
    """Test verifying all links."""
    
    def test_verify_all_valid_links(self, linker):
        """Test verifying all links when all are valid."""
        linker.create_link("link1.txt", "file1.txt")
        linker.create_link("link2.txt", "file2.txt")
        
        result = linker.verify_all_links()
        
        assert result['total'] == 2
        assert result['valid'] == 2
        assert result['broken'] == 0
        assert len(result['broken_links']) == 0
    
    def test_verify_all_with_broken_link(self, linker):
        """Test verifying all links with broken link."""
        linker.create_link("link1.txt", "file1.txt")
        linker.create_link("link2.txt", "file2.txt")
        
        # Break one link
        (linker.project_root / "file2.txt").unlink()
        
        result = linker.verify_all_links()
        
        assert result['total'] == 2
        assert result['valid'] == 1
        assert result['broken'] == 1
        assert "link2.txt" in result['broken_links']
    
    def test_verify_all_no_links(self, linker):
        """Test verifying when no links exist."""
        result = linker.verify_all_links()
        
        assert result['total'] == 0
        assert result['valid'] == 0
        assert result['broken'] == 0
