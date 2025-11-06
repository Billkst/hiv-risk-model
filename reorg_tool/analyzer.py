"""
Dependency analyzer module for the reorganization system.

Analyzes Python import statements and file path references.
"""

import ast
import re
from pathlib import Path
from typing import List, Set

from .models import (
    FileInfo,
    ImportDependency,
    PathDependency,
    DependencyGraph,
)
from .exceptions import DependencyError


class DependencyAnalyzer:
    """Analyzes code dependencies (imports and file paths)."""
    
    def __init__(self, project_root: str):
        """
        Initialize the dependency analyzer.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
    
    def analyze_imports(self, file_path: str) -> List[ImportDependency]:
        """
        Analyze Python import statements in a file.
        
        Args:
            file_path: Path to Python file
        
        Returns:
            List of ImportDependency objects
        """
        dependencies = []
        
        try:
            # Read file content
            full_path = self.project_root / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse Python AST
            try:
                tree = ast.parse(content, filename=file_path)
            except SyntaxError as e:
                # Skip files with syntax errors
                print(f"Warning: Syntax error in {file_path}: {e}")
                return dependencies
            
            # Visit all import nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # Handle: import module
                    for alias in node.names:
                        dependencies.append(ImportDependency(
                            source_file=file_path,
                            import_statement=f"import {alias.name}",
                            imported_module=alias.name,
                            line_number=node.lineno,
                            is_relative=False,
                        ))
                
                elif isinstance(node, ast.ImportFrom):
                    # Handle: from module import name
                    module = node.module or ''
                    level = node.level  # Number of dots for relative imports
                    
                    is_relative = level > 0
                    
                    for alias in node.names:
                        import_stmt = self._format_import_from(
                            module, alias.name, level
                        )
                        
                        dependencies.append(ImportDependency(
                            source_file=file_path,
                            import_statement=import_stmt,
                            imported_module=module,
                            line_number=node.lineno,
                            is_relative=is_relative,
                        ))
        
        except FileNotFoundError:
            print(f"Warning: File not found: {file_path}")
        except Exception as e:
            print(f"Warning: Error analyzing imports in {file_path}: {e}")
        
        return dependencies
    
    def _format_import_from(self, module: str, name: str, level: int) -> str:
        """Format 'from ... import ...' statement."""
        dots = '.' * level
        if module:
            return f"from {dots}{module} import {name}"
        else:
            return f"from {dots} import {name}"
    
    def analyze_file_paths(self, file_path: str) -> List[PathDependency]:
        """
        Analyze file path references in code.
        
        Args:
            file_path: Path to file
        
        Returns:
            List of PathDependency objects
        """
        dependencies = []
        
        try:
            # Read file content
            full_path = self.project_root / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Common patterns for file paths
            patterns = [
                # String literals with file paths
                r'''['"]([^'"]+\.(py|csv|pkl|json|txt|md|yml|yaml))['"]''',
                # Path-like strings
                r'''['"]([^'"]*[/\\][^'"]+)['"]''',
                # open() calls
                r'''open\s*\(\s*['"]([^'"]+)['"]''',
                # Path() calls
                r'''Path\s*\(\s*['"]([^'"]+)['"]''',
            ]
            
            for line_num, line in enumerate(lines, start=1):
                for pattern in patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        path_ref = match.group(1)
                        
                        # Filter out obvious non-file-paths
                        if self._is_likely_file_path(path_ref):
                            dependencies.append(PathDependency(
                                source_file=file_path,
                                referenced_path=path_ref,
                                line_number=line_num,
                                context=line.strip(),
                            ))
        
        except FileNotFoundError:
            print(f"Warning: File not found: {file_path}")
        except Exception as e:
            print(f"Warning: Error analyzing paths in {file_path}: {e}")
        
        return dependencies
    
    def _is_likely_file_path(self, path: str) -> bool:
        """Check if string is likely a file path."""
        # Skip very short strings
        if len(path) < 3:
            return False
        
        # Skip URLs
        if path.startswith(('http://', 'https://', 'ftp://')):
            return False
        
        # Skip common non-path strings
        skip_patterns = [
            r'^[A-Z_]+$',  # Constants like 'DEBUG', 'ERROR'
            r'^\d+$',      # Pure numbers
            r'^[a-z]+$',   # Single lowercase words
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, path):
                return False
        
        # Check for file-like indicators
        has_extension = '.' in path and not path.endswith('.')
        has_separator = '/' in path or '\\' in path
        
        return has_extension or has_separator
    
    def build_dependency_graph(self, files: List[FileInfo]) -> DependencyGraph:
        """
        Build a dependency graph for all files.
        
        Args:
            files: List of file information
        
        Returns:
            DependencyGraph object
        """
        graph = DependencyGraph()
        
        # Add all files as nodes
        for file_info in files:
            graph.add_node(file_info)
        
        # Analyze Python files for imports and paths
        for file_info in files:
            if file_info.extension == '.py':
                # Analyze imports
                imports = self.analyze_imports(file_info.path)
                for imp in imports:
                    graph.add_import_edge(imp)
                
                # Analyze file paths
                paths = self.analyze_file_paths(file_info.path)
                for path_dep in paths:
                    graph.add_path_edge(path_dep)
        
        return graph
    
    def identify_critical_dependencies(
        self,
        graph: DependencyGraph
    ) -> List[ImportDependency]:
        """
        Identify critical dependencies that require symbolic links.
        
        Args:
            graph: Dependency graph
        
        Returns:
            List of critical import dependencies
        """
        critical = []
        
        # Find imports that reference project modules
        for imp_dep in graph.import_edges:
            # Check if imported module is a project module
            if self._is_project_module(imp_dep.imported_module):
                critical.append(imp_dep)
        
        return critical
    
    def _is_project_module(self, module_name: str) -> bool:
        """
        Check if module is part of the project (not external).
        
        Args:
            module_name: Module name
        
        Returns:
            True if it's a project module
        """
        # Common project module patterns
        project_modules = [
            'models',
            'api',
            'utils',
            'data',
            'tests',
            'reorg_tool',
        ]
        
        # Check if module starts with any project module name
        for proj_mod in project_modules:
            if module_name.startswith(proj_mod):
                return True
        
        # Check if it's a relative import (starts with .)
        if module_name.startswith('.'):
            return True
        
        return False
    
    def get_files_depending_on(
        self,
        graph: DependencyGraph,
        target_file: str
    ) -> Set[str]:
        """
        Get all files that depend on a target file.
        
        Args:
            graph: Dependency graph
            target_file: Target file path
        
        Returns:
            Set of file paths that depend on target
        """
        dependents = set()
        
        # Check import dependencies
        for imp_dep in graph.import_edges:
            # Convert module name to file path
            module_path = imp_dep.imported_module.replace('.', '/') + '.py'
            if module_path in target_file or target_file in module_path:
                dependents.add(imp_dep.source_file)
        
        # Check path dependencies
        for path_dep in graph.path_edges:
            if target_file in path_dep.referenced_path:
                dependents.add(path_dep.source_file)
        
        return dependents
    
    def generate_dependency_report(self, graph: DependencyGraph) -> str:
        """
        Generate a human-readable dependency report.
        
        Args:
            graph: Dependency graph
        
        Returns:
            Report string
        """
        lines = ["# Dependency Analysis Report\n"]
        
        lines.append(f"Total files: {len(graph.nodes)}")
        lines.append(f"Import dependencies: {len(graph.import_edges)}")
        lines.append(f"Path dependencies: {len(graph.path_edges)}\n")
        
        # Critical dependencies
        critical = self.identify_critical_dependencies(graph)
        lines.append(f"## Critical Dependencies ({len(critical)})\n")
        lines.append("These imports will require symbolic links:\n")
        
        for imp_dep in sorted(critical, key=lambda x: x.source_file):
            lines.append(
                f"  - {imp_dep.source_file}:{imp_dep.line_number} "
                f"→ {imp_dep.import_statement}"
            )
        
        # Most imported modules
        lines.append("\n## Most Imported Modules\n")
        module_counts = {}
        for imp_dep in graph.import_edges:
            module = imp_dep.imported_module
            module_counts[module] = module_counts.get(module, 0) + 1
        
        top_modules = sorted(
            module_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        for module, count in top_modules:
            lines.append(f"  - {module}: {count} imports")
        
        return "\n".join(lines)
