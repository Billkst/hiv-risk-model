"""
Unit tests for the validation module.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import sys

from reorg_tool.validator import ReorganizationValidator
from reorg_tool.linker import SymbolicLinker
from reorg_tool.exceptions import ValidationError


@pytest.fixture
def temp_project():
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create test directory structure
    project_root = Path(temp_dir) / "test_project"
    project_root.mkdir()
    
    # Create some test files
    (project_root / "file1.py").write_text("# Test file 1\ndef func1():\n    return 'test1'")
    (project_root / "file2.py").write_text("# Test file 2\ndef func2():\n    return 'test2'")
    
    # Create subdirectories with Python files
    (project_root / "module1").mkdir()
    (project_root / "module1" / "__init__.py").write_text("")
    (project_root / "module1" / "submodule.py").write_text("def sub_func():\n    return 'sub'")
    
    (project_root / "module2").mkdir()
    (project_root / "module2" / "__init__.py").write_text("")
    (project_root / "module2" / "another.py").write_text("def another_func():\n    return 'another'")
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def validator(temp_project):
    """Create a ReorganizationValidator instance for testing."""
    return ReorganizationValidator(str(temp_project))


class TestValidatorInit:
    """Test ReorganizationValidator initialization."""
    
    def test_init_with_valid_path(self, temp_project):
        """Test initialization with valid project root."""
        validator = ReorganizationValidator(str(temp_project))
        assert validator.project_root == temp_project
        assert validator.linker is not None
        assert validator.validation_checks is not None
    
    def test_init_with_invalid_path(self):
        """Test initialization with invalid project root."""
        with pytest.raises(ValidationError):
            ReorganizationValidator("/nonexistent/path")


class TestValidateLinks:
    """Test symbolic link validation."""
    
    def test_validate_links_no_links(self, validator):
        """Test validation when no links exist."""
        result = validator.validate_links()
        
        assert result.all_links_valid is True
        assert len(result.broken_links) == 0
    
    def test_validate_links_with_valid_links(self, validator, temp_project):
        """Test validation with valid symbolic links."""
        # Create some valid links
        linker = SymbolicLinker(str(temp_project))
        linker.create_link("link1.py", "file1.py")
        linker.create_link("link2.py", "file2.py")
        
        result = validator.validate_links()
        
        assert result.all_links_valid is True
        assert len(result.broken_links) == 0
    
    def test_validate_links_with_broken_link(self, validator, temp_project):
        """Test validation with broken symbolic link."""
        # Create a link
        linker = SymbolicLinker(str(temp_project))
        linker.create_link("link.py", "file1.py")
        
        # Break the link by removing target
        (temp_project / "file1.py").unlink()
        
        result = validator.validate_links()
        
        assert result.all_links_valid is False
        assert len(result.broken_links) == 1
        assert "link.py" in result.broken_links[0]
    
    def test_validate_links_in_subdirectory(self, validator, temp_project):
        """Test validation of links in specific subdirectory."""
        # Create links in subdirectory
        linker = SymbolicLinker(str(temp_project))
        linker.create_link("module1/link.py", "file1.py")
        
        result = validator.validate_links("module1")
        
        assert result.all_links_valid is True


class TestValidateImports:
    """Test Python import validation."""
    
    def test_validate_imports_with_valid_modules(self, validator, temp_project):
        """Test validation with valid module imports."""
        # Add project to path temporarily
        sys.path.insert(0, str(temp_project))
        
        try:
            modules = ["file1", "file2"]
            result = validator.validate_imports(modules)
            
            assert result.import_tests_passed is True
            assert len(result.failed_imports) == 0
        finally:
            sys.path.remove(str(temp_project))
    
    def test_validate_imports_with_nonexistent_module(self, validator):
        """Test validation with nonexistent module."""
        modules = ["nonexistent_module"]
        result = validator.validate_imports(modules)
        
        assert result.import_tests_passed is False
        assert len(result.failed_imports) == 1
        assert "nonexistent_module" in result.failed_imports[0]
    
    def test_validate_imports_with_nested_modules(self, validator, temp_project):
        """Test validation with nested module imports."""
        sys.path.insert(0, str(temp_project))
        
        try:
            modules = ["module1.submodule", "module2.another"]
            result = validator.validate_imports(modules)
            
            assert result.import_tests_passed is True
            assert len(result.failed_imports) == 0
        finally:
            sys.path.remove(str(temp_project))
    
    def test_validate_imports_auto_discovery(self, validator, temp_project):
        """Test automatic module discovery."""
        sys.path.insert(0, str(temp_project))
        
        try:
            # Call without specifying modules
            result = validator.validate_imports()
            
            # Should discover and test modules automatically
            # Some may fail but the mechanism should work
            assert result.import_tests_passed is not None
        finally:
            sys.path.remove(str(temp_project))


class TestValidateFunctionality:
    """Test functionality validation."""
    
    def test_validate_functionality_with_passing_checks(self, validator):
        """Test validation with passing functionality checks."""
        checks = {
            'api_startable': lambda: True,
            'model_loadable': lambda: True,
            'predictions_working': lambda: True,
        }
        
        result = validator.validate_functionality(checks)
        
        assert result.api_startable is True
        assert result.model_loadable is True
        assert result.predictions_working is True
    
    def test_validate_functionality_with_failing_checks(self, validator):
        """Test validation with failing functionality checks."""
        checks = {
            'api_startable': lambda: False,
            'model_loadable': lambda: True,
            'predictions_working': lambda: False,
        }
        
        result = validator.validate_functionality(checks)
        
        assert result.api_startable is False
        assert result.model_loadable is True
        assert result.predictions_working is False
    
    def test_validate_functionality_with_exception(self, validator):
        """Test validation when check raises exception."""
        def failing_check():
            raise Exception("Check failed")
        
        checks = {
            'api_startable': failing_check,
        }
        
        result = validator.validate_functionality(checks)
        
        assert result.api_startable is False
    
    def test_validate_functionality_empty_checks(self, validator):
        """Test validation with no checks."""
        result = validator.validate_functionality({})
        
        # Should not crash, just return current state
        assert result is not None


class TestValidateFileIntegrity:
    """Test file integrity validation."""
    
    def test_validate_file_integrity_all_present(self, validator):
        """Test validation when all expected files are present."""
        expected_files = ["file1.py", "file2.py", "module1/submodule.py"]
        result = validator.validate_file_integrity(expected_files)
        
        assert result.no_missing_files is True
        assert len(result.missing_files) == 0
    
    def test_validate_file_integrity_with_missing_files(self, validator):
        """Test validation with missing files."""
        expected_files = ["file1.py", "nonexistent.py", "module1/missing.py"]
        result = validator.validate_file_integrity(expected_files)
        
        assert result.no_missing_files is False
        assert len(result.missing_files) == 2
        assert "nonexistent.py" in result.missing_files
        assert "module1/missing.py" in result.missing_files
    
    def test_validate_file_integrity_empty_list(self, validator):
        """Test validation with empty expected files list."""
        result = validator.validate_file_integrity([])
        
        assert result.no_missing_files is True
        assert len(result.missing_files) == 0


class TestValidateAll:
    """Test comprehensive validation."""
    
    def test_validate_all_with_all_checks(self, validator, temp_project):
        """Test running all validation checks."""
        sys.path.insert(0, str(temp_project))
        
        try:
            modules = ["file1", "file2"]
            expected_files = ["file1.py", "file2.py"]
            functionality_checks = {
                'api_startable': lambda: True,
                'model_loadable': lambda: True,
            }
            
            result = validator.validate_all(
                modules=modules,
                expected_files=expected_files,
                functionality_checks=functionality_checks
            )
            
            assert result.all_links_valid is True
            assert result.import_tests_passed is True
            assert result.no_missing_files is True
            assert result.api_startable is True
            assert result.model_loadable is True
        finally:
            sys.path.remove(str(temp_project))
    
    def test_validate_all_with_failures(self, validator, temp_project):
        """Test validation with some failures."""
        # Create a broken link
        linker = SymbolicLinker(str(temp_project))
        linker.create_link("link.py", "file1.py")
        (temp_project / "file1.py").unlink()
        
        modules = ["nonexistent_module"]
        expected_files = ["missing.py"]
        functionality_checks = {
            'api_startable': lambda: False,
        }
        
        result = validator.validate_all(
            modules=modules,
            expected_files=expected_files,
            functionality_checks=functionality_checks
        )
        
        assert result.all_links_valid is False
        assert result.import_tests_passed is False
        assert result.no_missing_files is False
        assert result.api_startable is False
    
    def test_validate_all_minimal(self, validator):
        """Test validation with minimal parameters."""
        result = validator.validate_all()
        
        # Should run at least link validation
        assert result is not None


class TestGenerateValidationReport:
    """Test validation report generation."""
    
    def test_generate_report_all_passed(self, validator, temp_project):
        """Test report generation when all checks pass."""
        sys.path.insert(0, str(temp_project))
        
        try:
            validator.validate_all(
                modules=["file1"],
                expected_files=["file1.py"],
                functionality_checks={'api_startable': lambda: True}
            )
            
            report = validator.generate_validation_report()
            
            assert "✅ PASSED" in report
            assert "All symbolic links are valid" in report
            assert "All imports successful" in report
            assert "All expected files present" in report
        finally:
            sys.path.remove(str(temp_project))
    
    def test_generate_report_with_failures(self, validator, temp_project):
        """Test report generation with failures."""
        # Create broken link
        linker = SymbolicLinker(str(temp_project))
        linker.create_link("link.py", "file1.py")
        (temp_project / "file1.py").unlink()
        
        validator.validate_all(
            modules=["nonexistent"],
            expected_files=["missing.py"],
            functionality_checks={'api_startable': lambda: False}
        )
        
        report = validator.generate_validation_report()
        
        assert "❌ FAILED" in report
        assert "broken links" in report
        assert "failed imports" in report
        assert "missing files" in report
    
    def test_generate_report_format(self, validator):
        """Test report format structure."""
        validator.validate_all()
        report = validator.generate_validation_report()
        
        assert "# Validation Report" in report
        assert "## Summary" in report
        assert "## Symbolic Links" in report
        assert "## Python Imports" in report
        assert "## File Integrity" in report
        assert "## Functionality Checks" in report


class TestGetValidationSummary:
    """Test validation summary generation."""
    
    def test_get_validation_summary_structure(self, validator):
        """Test validation summary structure."""
        validator.validate_all()
        summary = validator.get_validation_summary()
        
        assert 'all_passed' in summary
        assert 'links' in summary
        assert 'imports' in summary
        assert 'files' in summary
        assert 'functionality' in summary
    
    def test_get_validation_summary_links_section(self, validator, temp_project):
        """Test links section in summary."""
        # Create a broken link
        linker = SymbolicLinker(str(temp_project))
        linker.create_link("link.py", "file1.py")
        (temp_project / "file1.py").unlink()
        
        validator.validate_links()
        summary = validator.get_validation_summary()
        
        assert summary['links']['valid'] is False
        assert summary['links']['broken_count'] == 1
        assert len(summary['links']['broken_links']) == 1
    
    def test_get_validation_summary_imports_section(self, validator):
        """Test imports section in summary."""
        validator.validate_imports(["nonexistent"])
        summary = validator.get_validation_summary()
        
        assert summary['imports']['passed'] is False
        assert summary['imports']['failed_count'] == 1
        assert len(summary['imports']['failed_imports']) == 1
    
    def test_get_validation_summary_files_section(self, validator):
        """Test files section in summary."""
        validator.validate_file_integrity(["missing.py"])
        summary = validator.get_validation_summary()
        
        assert summary['files']['all_present'] is False
        assert summary['files']['missing_count'] == 1
        assert "missing.py" in summary['files']['missing_files']
    
    def test_get_validation_summary_functionality_section(self, validator):
        """Test functionality section in summary."""
        checks = {
            'api_startable': lambda: True,
            'model_loadable': lambda: False,
            'predictions_working': lambda: True,
        }
        validator.validate_functionality(checks)
        summary = validator.get_validation_summary()
        
        assert summary['functionality']['api_startable'] is True
        assert summary['functionality']['model_loadable'] is False
        assert summary['functionality']['predictions_working'] is True


class TestDiscoverPythonModules:
    """Test Python module discovery."""
    
    def test_discover_modules(self, validator, temp_project):
        """Test discovering Python modules in project."""
        modules = validator._discover_python_modules()
        
        # Should find the Python files we created
        assert len(modules) > 0
        
        # Should include our test files
        module_names = [m.replace("\\", "/") for m in modules]  # Normalize paths
        assert any("file1" in m for m in module_names)
        assert any("file2" in m for m in module_names)
    
    def test_discover_modules_excludes_tests(self, validator, temp_project):
        """Test that test files are excluded from discovery."""
        # Create a test file
        (temp_project / "test_something.py").write_text("def test_func(): pass")
        
        modules = validator._discover_python_modules()
        
        # Should not include test files
        assert not any("test_" in m for m in modules)
    
    def test_discover_modules_excludes_init(self, validator, temp_project):
        """Test that __init__.py files are excluded."""
        modules = validator._discover_python_modules()
        
        # Should not include __init__.py
        assert not any("__init__" in m for m in modules)
