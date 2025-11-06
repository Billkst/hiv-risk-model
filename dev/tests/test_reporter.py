"""
Unit tests for the reporter module.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from reorg_tool.reporter import ReorganizationReporter
from reorg_tool.models import ReorgResult, ReorgPhase
from reorg_tool.linker import SymbolicLinker


@pytest.fixture
def temp_project():
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create test directory structure
    project_root = Path(temp_dir) / "test_project"
    project_root.mkdir()
    
    # Create some test files and directories
    (project_root / "file1.txt").write_text("content1")
    (project_root / "file2.txt").write_text("content2")
    
    (project_root / "dir1").mkdir()
    (project_root / "dir1" / "file3.txt").write_text("content3")
    
    (project_root / "dir2").mkdir()
    (project_root / "dir2" / "subdir").mkdir()
    (project_root / "dir2" / "subdir" / "file4.txt").write_text("content4")
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def reporter(temp_project):
    """Create a ReorganizationReporter instance for testing."""
    return ReorganizationReporter(str(temp_project))


@pytest.fixture
def sample_result():
    """Create a sample ReorgResult for testing."""
    start_time = datetime(2025, 1, 1, 10, 0, 0)
    end_time = datetime(2025, 1, 1, 10, 5, 30)
    
    result = ReorgResult(
        success=True,
        start_time=start_time,
        end_time=end_time,
        phases_completed=[ReorgPhase.SCAN, ReorgPhase.CLASSIFY, ReorgPhase.MOVE_CORE],
        files_moved=25,
        links_created=15,
        files_deleted=5,
        backup_path="/backup/project_backup_20250101",
        transaction_log_path="/logs/transaction.log"
    )
    
    result.add_warning("Test warning")
    
    return result


class TestReporterInit:
    """Test ReorganizationReporter initialization."""
    
    def test_init_with_valid_path(self, temp_project):
        """Test initialization with valid project root."""
        reporter = ReorganizationReporter(str(temp_project))
        assert reporter.project_root == temp_project
    
    def test_init_with_invalid_path(self):
        """Test initialization with invalid project root."""
        with pytest.raises(ValueError):
            ReorganizationReporter("/nonexistent/path")


class TestGenerateSummaryReport:
    """Test summary report generation."""
    
    def test_generate_summary_success(self, reporter, sample_result):
        """Test generating summary for successful reorganization."""
        report = reporter.generate_summary_report(sample_result)
        
        assert "Reorganization Summary" in report
        assert "✅ SUCCESS" in report
        assert "Files Moved: 25" in report
        assert "Symbolic Links Created: 15" in report
        assert "Files Deleted: 5" in report
    
    def test_generate_summary_with_errors(self, reporter):
        """Test generating summary with errors."""
        result = ReorgResult(
            success=False,
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        result.add_error("Test error 1")
        result.add_error("Test error 2")
        
        report = reporter.generate_summary_report(result)
        
        assert "❌ FAILED" in report
        assert "## Errors" in report
        assert "Test error 1" in report
        assert "Test error 2" in report
    
    def test_generate_summary_with_warnings(self, reporter, sample_result):
        """Test generating summary with warnings."""
        report = reporter.generate_summary_report(sample_result)
        
        assert "## Warnings" in report
        assert "Test warning" in report
    
    def test_generate_summary_includes_duration(self, reporter, sample_result):
        """Test that summary includes duration."""
        report = reporter.generate_summary_report(sample_result)
        
        assert "Duration" in report
        assert "330.00 seconds" in report  # 5 minutes 30 seconds
    
    def test_generate_summary_includes_phases(self, reporter, sample_result):
        """Test that summary includes completed phases."""
        report = reporter.generate_summary_report(sample_result)
        
        assert "## Phases Completed" in report
        assert "scan" in report
        assert "classify" in report
        assert "move_core" in report


class TestGenerateDetailedReport:
    """Test detailed report generation."""
    
    def test_generate_detailed_basic(self, reporter, sample_result):
        """Test generating basic detailed report."""
        report = reporter.generate_detailed_report(sample_result)
        
        assert "# Detailed Reorganization Report" in report
        assert "## Summary" in report
        assert "Generated:" in report
    
    def test_generate_detailed_with_file_mappings(self, reporter, sample_result):
        """Test detailed report with file mappings."""
        file_mappings = [
            {'old_path': 'old/file1.py', 'new_path': 'new/file1.py', 'category': 'core'},
            {'old_path': 'old/file2.py', 'new_path': 'new/file2.py', 'category': 'docs'},
        ]
        
        report = reporter.generate_detailed_report(sample_result, file_mappings=file_mappings)
        
        assert "## File Mappings" in report
        assert "old/file1.py" in report
        assert "new/file1.py" in report
    
    def test_generate_detailed_with_validation(self, reporter, sample_result):
        """Test detailed report with validation summary."""
        validation_summary = {
            'all_passed': True,
            'links': {'valid': True, 'broken_count': 0, 'broken_links': []},
            'imports': {'passed': True, 'failed_count': 0, 'failed_imports': []},
            'files': {'all_present': True, 'missing_count': 0, 'missing_files': []},
        }
        
        report = reporter.generate_detailed_report(
            sample_result,
            validation_summary=validation_summary
        )
        
        assert "## Validation Results" in report
        assert "✅ All symbolic links are valid" in report
        assert "✅ All imports successful" in report
        assert "✅ All expected files present" in report
    
    def test_generate_detailed_with_validation_failures(self, reporter, sample_result):
        """Test detailed report with validation failures."""
        validation_summary = {
            'all_passed': False,
            'links': {
                'valid': False,
                'broken_count': 2,
                'broken_links': ['link1.py', 'link2.py']
            },
            'imports': {
                'passed': False,
                'failed_count': 1,
                'failed_imports': ['module.broken']
            },
            'files': {
                'all_present': False,
                'missing_count': 1,
                'missing_files': ['missing.txt']
            },
        }
        
        report = reporter.generate_detailed_report(
            sample_result,
            validation_summary=validation_summary
        )
        
        assert "❌ 2 broken links found" in report
        assert "link1.py" in report
        assert "❌ 1 failed imports" in report
        assert "module.broken" in report
        assert "❌ 1 missing files" in report
        assert "missing.txt" in report
    
    def test_generate_detailed_includes_backup_info(self, reporter, sample_result):
        """Test that detailed report includes backup information."""
        report = reporter.generate_detailed_report(sample_result)
        
        assert "## Backup" in report
        assert sample_result.backup_path in report
    
    def test_generate_detailed_includes_transaction_log(self, reporter, sample_result):
        """Test that detailed report includes transaction log path."""
        report = reporter.generate_detailed_report(sample_result)
        
        assert "## Transaction Log" in report
        assert sample_result.transaction_log_path in report


class TestGenerateDirectoryTree:
    """Test directory tree generation."""
    
    def test_generate_tree_basic(self, reporter):
        """Test generating basic directory tree."""
        tree = reporter.generate_directory_tree(max_depth=2)
        
        assert "test_project/" in tree
        assert "dir1/" in tree
        assert "dir2/" in tree
    
    def test_generate_tree_with_files(self, reporter):
        """Test generating tree with files."""
        tree = reporter.generate_directory_tree(show_files=True)
        
        assert "file1.txt" in tree
        assert "file2.txt" in tree
    
    def test_generate_tree_without_files(self, reporter):
        """Test generating tree without files."""
        tree = reporter.generate_directory_tree(show_files=False)
        
        assert "dir1/" in tree
        assert "dir2/" in tree
        assert "file1.txt" not in tree
        assert "file2.txt" not in tree
    
    def test_generate_tree_with_depth_limit(self, reporter):
        """Test generating tree with depth limit."""
        tree = reporter.generate_directory_tree(max_depth=1, show_files=False)
        
        assert "dir1/" in tree
        assert "dir2/" in tree
        # subdir should not appear due to depth limit
        assert "subdir/" not in tree
    
    def test_generate_tree_with_symbolic_links(self, reporter, temp_project):
        """Test generating tree with symbolic links."""
        # Create a symbolic link
        linker = SymbolicLinker(str(temp_project))
        linker.create_link("link_to_file1.txt", "file1.txt")
        
        tree = reporter.generate_directory_tree(show_files=True)
        
        assert "link_to_file1.txt" in tree
        assert "->" in tree  # Arrow indicating symbolic link
    
    def test_generate_tree_subdirectory(self, reporter):
        """Test generating tree for specific subdirectory."""
        tree = reporter.generate_directory_tree(directory="dir1", show_files=True)
        
        assert "dir1/" in tree
        assert "file3.txt" in tree
    
    def test_generate_tree_nonexistent_directory(self, reporter):
        """Test generating tree for nonexistent directory."""
        tree = reporter.generate_directory_tree(directory="nonexistent")
        
        assert "does not exist" in tree


class TestCreateMarkdownReport:
    """Test Markdown report creation."""
    
    def test_create_markdown_basic(self, reporter, sample_result, temp_project):
        """Test creating basic Markdown report."""
        output_path = reporter.create_markdown_report(sample_result)
        
        assert Path(output_path).exists()
        assert output_path.endswith("REORGANIZATION_SUMMARY.md")
        
        # Read and verify content
        content = Path(output_path).read_text()
        assert "# Project Reorganization Report" in content
        assert "## Executive Summary" in content
    
    def test_create_markdown_custom_path(self, reporter, sample_result, temp_project):
        """Test creating Markdown report with custom path."""
        custom_path = temp_project / "custom_report.md"
        output_path = reporter.create_markdown_report(sample_result, output_path=str(custom_path))
        
        assert Path(output_path).exists()
        assert output_path == str(custom_path)
    
    def test_create_markdown_with_file_mappings(self, reporter, sample_result, temp_project):
        """Test creating report with file mappings."""
        file_mappings = [
            {'old_path': 'old/file1.py', 'new_path': 'new/file1.py', 'category': 'core'},
            {'old_path': 'old/file2.py', 'new_path': 'new/file2.py', 'category': 'docs'},
        ]
        
        output_path = reporter.create_markdown_report(
            sample_result,
            file_mappings=file_mappings
        )
        
        content = Path(output_path).read_text()
        assert "## File Relocations" in content
        assert "old/file1.py" in content
        assert "new/file1.py" in content
    
    def test_create_markdown_with_validation(self, reporter, sample_result, temp_project):
        """Test creating report with validation summary."""
        validation_summary = {
            'all_passed': True,
            'links': {'valid': True, 'broken_count': 0, 'broken_links': []},
            'imports': {'passed': True, 'failed_count': 0, 'failed_imports': []},
            'files': {'all_present': True, 'missing_count': 0, 'missing_files': []},
        }
        
        output_path = reporter.create_markdown_report(
            sample_result,
            validation_summary=validation_summary
        )
        
        content = Path(output_path).read_text()
        assert "## Validation Results" in content
        assert "✅ PASSED" in content
    
    def test_create_markdown_without_tree(self, reporter, sample_result, temp_project):
        """Test creating report without directory tree."""
        output_path = reporter.create_markdown_report(
            sample_result,
            include_tree=False
        )
        
        content = Path(output_path).read_text()
        assert "## New Directory Structure" not in content
    
    def test_create_markdown_with_tree(self, reporter, sample_result, temp_project):
        """Test creating report with directory tree."""
        output_path = reporter.create_markdown_report(
            sample_result,
            include_tree=True
        )
        
        content = Path(output_path).read_text()
        assert "## New Directory Structure" in content
    
    def test_create_markdown_includes_statistics_table(self, reporter, sample_result, temp_project):
        """Test that report includes statistics table."""
        output_path = reporter.create_markdown_report(sample_result)
        
        content = Path(output_path).read_text()
        assert "## Detailed Statistics" in content
        assert "| Metric | Value |" in content
        assert "| Files Moved | 25 |" in content
    
    def test_create_markdown_includes_next_steps(self, reporter, sample_result, temp_project):
        """Test that report includes next steps."""
        output_path = reporter.create_markdown_report(sample_result)
        
        content = Path(output_path).read_text()
        assert "## Next Steps" in content
    
    def test_create_markdown_includes_rollback_info(self, reporter, sample_result, temp_project):
        """Test that report includes rollback information."""
        output_path = reporter.create_markdown_report(sample_result)
        
        content = Path(output_path).read_text()
        assert "## Backup and Rollback" in content
        assert "To rollback the reorganization:" in content


class TestGenerateStatisticsSummary:
    """Test statistics summary generation."""
    
    def test_generate_statistics_basic(self, reporter, sample_result):
        """Test generating basic statistics summary."""
        summary = reporter.generate_statistics_summary(sample_result)
        
        assert summary['success'] is True
        assert summary['files_moved'] == 25
        assert summary['links_created'] == 15
        assert summary['files_deleted'] == 5
    
    def test_generate_statistics_includes_times(self, reporter, sample_result):
        """Test that statistics include timestamps."""
        summary = reporter.generate_statistics_summary(sample_result)
        
        assert 'start_time' in summary
        assert 'end_time' in summary
        assert 'duration_seconds' in summary
    
    def test_generate_statistics_includes_phases(self, reporter, sample_result):
        """Test that statistics include completed phases."""
        summary = reporter.generate_statistics_summary(sample_result)
        
        assert 'phases_completed' in summary
        assert 'scan' in summary['phases_completed']
        assert 'classify' in summary['phases_completed']
    
    def test_generate_statistics_includes_counts(self, reporter, sample_result):
        """Test that statistics include error and warning counts."""
        summary = reporter.generate_statistics_summary(sample_result)
        
        assert 'error_count' in summary
        assert 'warning_count' in summary
        assert summary['warning_count'] == 1
    
    def test_generate_statistics_includes_paths(self, reporter, sample_result):
        """Test that statistics include backup and log paths."""
        summary = reporter.generate_statistics_summary(sample_result)
        
        assert 'backup_path' in summary
        assert 'transaction_log_path' in summary
        assert summary['backup_path'] == sample_result.backup_path
