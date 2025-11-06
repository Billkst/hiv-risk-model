"""
Unit tests for the FileScanner module.
"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

from reorg_tool.scanner import FileScanner
from reorg_tool.models import FileInfo
from reorg_tool.exceptions import FileOperationError


class TestFileScanner:
    """Test cases for FileScanner class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test directory structure
        project_root = Path(temp_dir) / "test_project"
        project_root.mkdir()
        
        # Create some test files
        (project_root / "file1.py").write_text("print('hello')")
        (project_root / "file2.txt").write_text("test content")
        (project_root / "README.md").write_text("# Test Project")
        
        # Create subdirectory with files
        subdir = project_root / "subdir"
        subdir.mkdir()
        (subdir / "file3.py").write_text("def test(): pass")
        (subdir / "file4.json").write_text('{"key": "value"}')
        
        # Create file with non-ASCII name
        (project_root / "测试文件.txt").write_text("Chinese filename")
        
        # Create executable file
        exec_file = project_root / "script.sh"
        exec_file.write_text("#!/bin/bash\necho 'test'")
        exec_file.chmod(0o755)
        
        # Create __pycache__ directory (should be excluded)
        pycache = project_root / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").write_text("bytecode")
        
        yield str(project_root)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_scanner_initialization(self, temp_project):
        """Test FileScanner initialization."""
        scanner = FileScanner(temp_project)
        assert scanner.project_root == Path(temp_project).resolve()
        assert '__pycache__' in scanner.exclude_patterns
    
    def test_scanner_invalid_root(self):
        """Test FileScanner with invalid project root."""
        with pytest.raises(FileOperationError):
            FileScanner("/nonexistent/path")
    
    def test_scan_directory(self, temp_project):
        """Test directory scanning functionality."""
        scanner = FileScanner(temp_project)
        files = scanner.scan_directory()
        
        # Should find files but exclude __pycache__
        assert len(files) > 0
        
        # Check that we found expected files
        file_names = [f.name for f in files]
        assert "file1.py" in file_names
        assert "file2.txt" in file_names
        assert "README.md" in file_names
        assert "file3.py" in file_names
        assert "file4.json" in file_names
        assert "测试文件.txt" in file_names
        assert "script.sh" in file_names
        
        # Should not include __pycache__ files
        assert "test.pyc" not in file_names
    
    def test_get_file_info(self, temp_project):
        """Test getting file information."""
        scanner = FileScanner(temp_project)
        test_file = Path(temp_project) / "file1.py"
        
        file_info = scanner.get_file_info(str(test_file))
        
        assert file_info is not None
        assert file_info.name == "file1.py"
        assert file_info.extension == ".py"
        assert file_info.size > 0
        assert isinstance(file_info.modified_time, datetime)
        assert file_info.has_non_ascii_name is False
    
    def test_detect_non_ascii_filenames(self, temp_project):
        """Test detection of non-ASCII filenames."""
        scanner = FileScanner(temp_project)
        non_ascii_files = scanner.find_non_ascii_files()
        
        assert len(non_ascii_files) > 0
        assert any(f.name == "测试文件.txt" for f in non_ascii_files)
        
        # Check the flag is set correctly
        for f in non_ascii_files:
            assert f.has_non_ascii_name is True
    
    def test_detect_executable_files(self, temp_project):
        """Test detection of executable files."""
        scanner = FileScanner(temp_project)
        files = scanner.scan_directory()
        
        # Find the script.sh file
        script_file = next((f for f in files if f.name == "script.sh"), None)
        assert script_file is not None
        assert script_file.is_executable is True
    
    def test_detect_encoding(self, temp_project):
        """Test file encoding detection."""
        scanner = FileScanner(temp_project)
        test_file = Path(temp_project) / "file1.py"
        
        encoding = scanner.detect_encoding(str(test_file))
        assert encoding in ['utf-8', 'ascii', 'UTF-8', 'ASCII']
    
    def test_get_file_count(self, temp_project):
        """Test file counting."""
        scanner = FileScanner(temp_project)
        count = scanner.get_file_count()
        
        # Should count all files except those in __pycache__
        assert count >= 7  # At least the files we created
    
    def test_get_total_size(self, temp_project):
        """Test total size calculation."""
        scanner = FileScanner(temp_project)
        total_size = scanner.get_total_size()
        
        assert total_size > 0
    
    def test_exclude_patterns(self, temp_project):
        """Test that exclude patterns work correctly."""
        scanner = FileScanner(temp_project)
        files = scanner.scan_directory()
        
        # Should not include any .pyc files
        assert not any(f.extension == ".pyc" for f in files)
        
        # Should not include files from __pycache__
        assert not any("__pycache__" in f.path for f in files)
    
    def test_custom_exclude_patterns(self, temp_project):
        """Test custom exclude patterns."""
        # Exclude .txt files
        scanner = FileScanner(temp_project, exclude_patterns={'*.txt'})
        files = scanner.scan_directory()
        
        # Should not include .txt files
        assert not any(f.extension == ".txt" for f in files)
    
    def test_relative_paths(self, temp_project):
        """Test that paths are relative to project root."""
        scanner = FileScanner(temp_project)
        files = scanner.scan_directory()
        
        for file_info in files:
            # Paths should be relative, not absolute
            assert not file_info.path.startswith('/')
            # Paths should not contain the temp directory
            assert temp_project not in file_info.path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
