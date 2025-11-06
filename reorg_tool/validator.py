"""
Validation module for the reorganization system.

Validates reorganization results including symbolic links, imports, and functionality.
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import List, Optional, Dict

from .models import ValidationChecks
from .linker import SymbolicLinker
from .exceptions import ValidationError


class ReorganizationValidator:
    """Validates reorganization results."""
    
    def __init__(self, project_root: str):
        """
        Initialize the validator.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        
        if not self.project_root.exists():
            raise ValidationError(f"Project root does not exist: {project_root}")
        
        self.linker = SymbolicLinker(str(self.project_root))
        self.validation_checks = ValidationChecks()
    
    def validate_links(self, directory: Optional[str] = None) -> ValidationChecks:
        """
        Validate all symbolic links in the project.
        
        Args:
            directory: Directory to validate (None for entire project)
        
        Returns:
            ValidationChecks with link validation results
        """
        # Verify all links using the linker
        result = self.linker.verify_all_links(directory)
        
        self.validation_checks.all_links_valid = (result['broken'] == 0)
        self.validation_checks.broken_links = result['broken_links']
        
        return self.validation_checks
    
    def validate_imports(self, modules: Optional[List[str]] = None) -> ValidationChecks:
        """
        Validate Python module imports.
        
        Args:
            modules: List of module names to test (e.g., ['models.predictor', 'api.app'])
                    If None, will attempt to discover modules automatically
        
        Returns:
            ValidationChecks with import validation results
        """
        if modules is None:
            modules = self._discover_python_modules()
        
        failed_imports = []
        
        # Add project root to Python path temporarily
        original_path = sys.path.copy()
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
        
        try:
            for module_name in modules:
                try:
                    # Try to import the module
                    if module_name in sys.modules:
                        # Reload if already imported
                        importlib.reload(sys.modules[module_name])
                    else:
                        importlib.import_module(module_name)
                except Exception as e:
                    failed_imports.append(f"{module_name}: {str(e)}")
        finally:
            # Restore original path
            sys.path = original_path
        
        self.validation_checks.import_tests_passed = (len(failed_imports) == 0)
        self.validation_checks.failed_imports = failed_imports
        
        return self.validation_checks
    
    def validate_functionality(self, checks: Optional[Dict[str, callable]] = None) -> ValidationChecks:
        """
        Validate core functionality.
        
        Args:
            checks: Dictionary of check names to callable functions
                   Each function should return True if check passes
        
        Returns:
            ValidationChecks with functionality validation results
        """
        if checks is None:
            checks = {}
        
        # Run custom checks
        for check_name, check_func in checks.items():
            try:
                result = check_func()
                if check_name == 'api_startable':
                    self.validation_checks.api_startable = result
                elif check_name == 'model_loadable':
                    self.validation_checks.model_loadable = result
                elif check_name == 'predictions_working':
                    self.validation_checks.predictions_working = result
            except Exception:
                # Check failed
                if check_name == 'api_startable':
                    self.validation_checks.api_startable = False
                elif check_name == 'model_loadable':
                    self.validation_checks.model_loadable = False
                elif check_name == 'predictions_working':
                    self.validation_checks.predictions_working = False
        
        return self.validation_checks
    
    def validate_file_integrity(self, expected_files: List[str]) -> ValidationChecks:
        """
        Validate that expected files exist.
        
        Args:
            expected_files: List of file paths (relative to project root) that should exist
        
        Returns:
            ValidationChecks with file integrity results
        """
        missing_files = []
        
        for file_path in expected_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        self.validation_checks.no_missing_files = (len(missing_files) == 0)
        self.validation_checks.missing_files = missing_files
        
        return self.validation_checks
    
    def validate_all(
        self,
        modules: Optional[List[str]] = None,
        expected_files: Optional[List[str]] = None,
        functionality_checks: Optional[Dict[str, callable]] = None
    ) -> ValidationChecks:
        """
        Run all validation checks.
        
        Args:
            modules: List of modules to test imports
            expected_files: List of expected files
            functionality_checks: Dictionary of functionality checks
        
        Returns:
            ValidationChecks with all validation results
        """
        # Validate links
        self.validate_links()
        
        # Validate imports
        if modules:
            self.validate_imports(modules)
        
        # Validate file integrity
        if expected_files:
            self.validate_file_integrity(expected_files)
        
        # Validate functionality
        if functionality_checks:
            self.validate_functionality(functionality_checks)
        
        return self.validation_checks
    
    def generate_validation_report(self) -> str:
        """
        Generate a human-readable validation report.
        
        Returns:
            Validation report as string
        """
        lines = [
            "# Validation Report",
            "",
            "## Summary",
            f"Overall Status: {'✅ PASSED' if self.validation_checks.all_passed else '❌ FAILED'}",
            "",
        ]
        
        # Symbolic Links
        lines.append("## Symbolic Links")
        if self.validation_checks.all_links_valid:
            lines.append("✅ All symbolic links are valid")
        else:
            lines.append(f"❌ Found {len(self.validation_checks.broken_links)} broken links:")
            for link in self.validation_checks.broken_links:
                lines.append(f"  - {link}")
        lines.append("")
        
        # Imports
        lines.append("## Python Imports")
        if self.validation_checks.import_tests_passed:
            lines.append("✅ All imports successful")
        else:
            lines.append(f"❌ Found {len(self.validation_checks.failed_imports)} failed imports:")
            for failed_import in self.validation_checks.failed_imports:
                lines.append(f"  - {failed_import}")
        lines.append("")
        
        # File Integrity
        lines.append("## File Integrity")
        if self.validation_checks.no_missing_files:
            lines.append("✅ All expected files present")
        else:
            lines.append(f"❌ Found {len(self.validation_checks.missing_files)} missing files:")
            for missing_file in self.validation_checks.missing_files:
                lines.append(f"  - {missing_file}")
        lines.append("")
        
        # Functionality
        lines.append("## Functionality Checks")
        lines.append(f"API Startable: {'✅' if self.validation_checks.api_startable else '❌'}")
        lines.append(f"Model Loadable: {'✅' if self.validation_checks.model_loadable else '❌'}")
        lines.append(f"Predictions Working: {'✅' if self.validation_checks.predictions_working else '❌'}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _discover_python_modules(self) -> List[str]:
        """
        Discover Python modules in the project.
        
        Returns:
            List of module names
        """
        modules = []
        
        # Find all Python files
        for py_file in self.project_root.rglob("*.py"):
            # Skip test files and __init__.py
            if py_file.name.startswith("test_") or py_file.name == "__init__.py":
                continue
            
            # Skip files in certain directories
            skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', '.venv'}
            if any(skip_dir in py_file.parts for skip_dir in skip_dirs):
                continue
            
            # Convert file path to module name
            try:
                relative_path = py_file.relative_to(self.project_root)
                module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
                module_name = ".".join(module_parts)
                modules.append(module_name)
            except ValueError:
                # File is outside project root
                continue
        
        return modules
    
    def get_validation_summary(self) -> Dict[str, any]:
        """
        Get validation summary as dictionary.
        
        Returns:
            Dictionary with validation summary
        """
        return {
            'all_passed': self.validation_checks.all_passed,
            'links': {
                'valid': self.validation_checks.all_links_valid,
                'broken_count': len(self.validation_checks.broken_links),
                'broken_links': self.validation_checks.broken_links,
            },
            'imports': {
                'passed': self.validation_checks.import_tests_passed,
                'failed_count': len(self.validation_checks.failed_imports),
                'failed_imports': self.validation_checks.failed_imports,
            },
            'files': {
                'all_present': self.validation_checks.no_missing_files,
                'missing_count': len(self.validation_checks.missing_files),
                'missing_files': self.validation_checks.missing_files,
            },
            'functionality': {
                'api_startable': self.validation_checks.api_startable,
                'model_loadable': self.validation_checks.model_loadable,
                'predictions_working': self.validation_checks.predictions_working,
            },
        }
