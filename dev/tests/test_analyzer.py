"""
Unit tests for the DependencyAnalyzer module.
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

from reorg_tool.analyzer import DependencyAnalyzer
from reorg_tool.models import FileInfo, ImportDependency, PathDependency


class TestDependencyAnalyzer:
    """Test cases for DependencyAnalyzer class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with Python files."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir) / "test_project"
        project_root.mkdir()
        
        # Create test Python files with imports
        (project_root / "main.py").write_text("""
import os
import sys
from models.predictor import HIVRiskPredictor
from models import enhanced_predictor
from .utils import helper

def main():
    model = HIVRiskPredictor('saved_models/model.pkl')
    data = open('data/test.csv', 'r')
""")
        
        # Create models directory
        models_dir = project_root / "models"
        models_dir.mkdir()
        (models_dir / "__init__.py").write_text("")
        (models_dir / "predictor.py").write_text("""
import numpy as np
from .enhanced_predictor import EnhancedPredictor

class HIVRiskPredictor:
    def __init__(self, model_path):
        self.model_path = model_path
""")
        
        (models_dir / "enhanced_predictor.py").write_text("""
from models.predictor import HIVRiskPredictor

class EnhancedPredictor(HIVRiskPredictor):
    pass
""")
        
        # Create utils directory
        utils_dir = project_root / "utils"
        utils_dir.mkdir()
        (utils_dir / "helper.py").write_text("""
import json

def load_config(path='config.json'):
    with open(path) as f:
        return json.load(f)
""")
        
        yield str(project_root)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def analyzer(self, temp_project):
        """Create a DependencyAnalyzer instance."""
        return DependencyAnalyzer(temp_project)
    
    @pytest.fixture
    def sample_files(self, temp_project):
        """Create sample FileInfo objects."""
        return [
            FileInfo(
                path="main.py",
                name="main.py",
                size=1024,
                extension=".py",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="models/predictor.py",
                name="predictor.py",
                size=2048,
                extension=".py",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="models/enhanced_predictor.py",
                name="enhanced_predictor.py",
                size=1536,
                extension=".py",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="utils/helper.py",
                name="helper.py",
                size=512,
                extension=".py",
                modified_time=datetime.now()
            ),
        ]
    
    def test_analyzer_initialization(self, analyzer, temp_project):
        """Test DependencyAnalyzer initialization."""
        assert analyzer is not None
        assert analyzer.project_root == Path(temp_project).resolve()
    
    def test_analyze_imports(self, analyzer):
        """Test import statement analysis."""
        imports = analyzer.analyze_imports("main.py")
        
        # Should find multiple imports
        assert len(imports) > 0
        
        # Check for specific imports
        import_stmts = [imp.import_statement for imp in imports]
        assert any("import os" in stmt for stmt in import_stmts)
        assert any("import sys" in stmt for stmt in import_stmts)
        assert any("from models.predictor" in stmt for stmt in import_stmts)
    
    def test_analyze_relative_imports(self, analyzer):
        """Test relative import detection."""
        imports = analyzer.analyze_imports("main.py")
        
        # Find relative imports
        relative_imports = [imp for imp in imports if imp.is_relative]
        
        # Should have at least one relative import (from .utils)
        assert len(relative_imports) > 0
    
    def test_analyze_file_paths(self, analyzer):
        """Test file path reference analysis."""
        paths = analyzer.analyze_file_paths("main.py")
        
        # Should find file path references
        assert len(paths) > 0
        
        # Check for specific paths
        path_refs = [p.referenced_path for p in paths]
        assert any("model.pkl" in ref for ref in path_refs)
        assert any("test.csv" in ref for ref in path_refs)
    
    def test_build_dependency_graph(self, analyzer, sample_files):
        """Test dependency graph construction."""
        graph = analyzer.build_dependency_graph(sample_files)
        
        # Should have nodes for all files
        assert len(graph.nodes) == len(sample_files)
        
        # Should have import edges
        assert len(graph.import_edges) > 0
        
        # Should have path edges
        assert len(graph.path_edges) > 0
    
    def test_identify_critical_dependencies(self, analyzer, sample_files):
        """Test critical dependency identification."""
        graph = analyzer.build_dependency_graph(sample_files)
        critical = analyzer.identify_critical_dependencies(graph)
        
        # Should identify project module imports as critical
        assert len(critical) > 0
        
        # Check that project modules are identified
        critical_modules = [dep.imported_module for dep in critical]
        assert any("models" in mod for mod in critical_modules)
    
    def test_is_project_module(self, analyzer):
        """Test project module detection."""
        # Project modules
        assert analyzer._is_project_module("models.predictor")
        assert analyzer._is_project_module("api.app")
        assert analyzer._is_project_module("utils.helper")
        assert analyzer._is_project_module(".relative")
        
        # External modules
        assert not analyzer._is_project_module("numpy")
        assert not analyzer._is_project_module("pandas")
        assert not analyzer._is_project_module("os")
    
    def test_is_likely_file_path(self, analyzer):
        """Test file path detection."""
        # Valid file paths
        assert analyzer._is_likely_file_path("data/test.csv")
        assert analyzer._is_likely_file_path("models/model.pkl")
        assert analyzer._is_likely_file_path("config.json")
        
        # Not file paths
        assert not analyzer._is_likely_file_path("DEBUG")
        assert not analyzer._is_likely_file_path("123")
        assert not analyzer._is_likely_file_path("http://example.com")
        assert not analyzer._is_likely_file_path("test")
    
    def test_get_files_depending_on(self, analyzer, sample_files):
        """Test finding files that depend on a target."""
        graph = analyzer.build_dependency_graph(sample_files)
        
        # Find files depending on predictor.py
        dependents = analyzer.get_files_depending_on(
            graph,
            "models/predictor.py"
        )
        
        # Should find files that import predictor
        assert len(dependents) > 0
    
    def test_generate_dependency_report(self, analyzer, sample_files):
        """Test dependency report generation."""
        graph = analyzer.build_dependency_graph(sample_files)
        report = analyzer.generate_dependency_report(graph)
        
        # Check report content
        assert "Dependency Analysis Report" in report
        assert "Total files:" in report
        assert "Import dependencies:" in report
        assert "Critical Dependencies" in report
    
    def test_analyze_imports_with_syntax_error(self, analyzer, temp_project):
        """Test handling of files with syntax errors."""
        # Create file with syntax error
        bad_file = Path(temp_project) / "bad.py"
        bad_file.write_text("def broken(\n  # Missing closing paren")
        
        # Should handle gracefully
        imports = analyzer.analyze_imports("bad.py")
        assert imports == []  # Should return empty list, not crash
    
    def test_analyze_nonexistent_file(self, analyzer):
        """Test handling of nonexistent files."""
        imports = analyzer.analyze_imports("nonexistent.py")
        assert imports == []
        
        paths = analyzer.analyze_file_paths("nonexistent.py")
        assert paths == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
