"""
Reporter module for the reorganization system.

Generates reports and documentation about reorganization results.
"""

from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from .models import ReorgResult, FileCategory


class ReorganizationReporter:
    """Generates reports about reorganization results."""
    
    def __init__(self, project_root: str):
        """
        Initialize the reporter.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {project_root}")
    
    def generate_summary_report(self, result: ReorgResult) -> str:
        """
        Generate a summary report of the reorganization.
        
        Args:
            result: ReorgResult object with reorganization results
        
        Returns:
            Summary report as string
        """
        lines = [
            "# Reorganization Summary",
            "",
            f"**Status**: {'✅ SUCCESS' if result.success else '❌ FAILED'}",
            f"**Duration**: {result.duration:.2f} seconds",
            f"**Start Time**: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**End Time**: {result.end_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Statistics",
            f"- Files Moved: {result.files_moved}",
            f"- Symbolic Links Created: {result.links_created}",
            f"- Files Deleted: {result.files_deleted}",
            "",
            "## Phases Completed",
        ]
        
        for phase in result.phases_completed:
            lines.append(f"- ✅ {phase.value}")
        
        lines.append("")
        
        # Errors and warnings
        if result.errors:
            lines.append("## Errors")
            for error in result.errors:
                lines.append(f"- ❌ {error}")
            lines.append("")
        
        if result.warnings:
            lines.append("## Warnings")
            for warning in result.warnings:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_detailed_report(
        self,
        result: ReorgResult,
        file_mappings: Optional[List[Dict]] = None,
        validation_summary: Optional[Dict] = None
    ) -> str:
        """
        Generate a detailed report of the reorganization.
        
        Args:
            result: ReorgResult object
            file_mappings: List of file mapping dictionaries
            validation_summary: Validation summary dictionary
        
        Returns:
            Detailed report as string
        """
        lines = [
            "# Detailed Reorganization Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        
        # Add summary section
        lines.append("## Summary")
        lines.append(self.generate_summary_report(result))
        lines.append("")
        
        # File mappings
        if file_mappings:
            lines.append("## File Mappings")
            lines.append("")
            for mapping in file_mappings:
                old_path = mapping.get('old_path', 'unknown')
                new_path = mapping.get('new_path', 'unknown')
                category = mapping.get('category', 'unknown')
                lines.append(f"- `{old_path}` → `{new_path}` ({category})")
            lines.append("")
        
        # Validation results
        if validation_summary:
            lines.append("## Validation Results")
            lines.append("")
            
            # Links
            links = validation_summary.get('links', {})
            if links.get('valid'):
                lines.append("✅ All symbolic links are valid")
            else:
                lines.append(f"❌ {links.get('broken_count', 0)} broken links found")
                for broken_link in links.get('broken_links', []):
                    lines.append(f"  - {broken_link}")
            lines.append("")
            
            # Imports
            imports = validation_summary.get('imports', {})
            if imports.get('passed'):
                lines.append("✅ All imports successful")
            else:
                lines.append(f"❌ {imports.get('failed_count', 0)} failed imports")
                for failed_import in imports.get('failed_imports', []):
                    lines.append(f"  - {failed_import}")
            lines.append("")
            
            # Files
            files = validation_summary.get('files', {})
            if files.get('all_present'):
                lines.append("✅ All expected files present")
            else:
                lines.append(f"❌ {files.get('missing_count', 0)} missing files")
                for missing_file in files.get('missing_files', []):
                    lines.append(f"  - {missing_file}")
            lines.append("")
        
        # Backup information
        if result.backup_path:
            lines.append("## Backup")
            lines.append(f"Backup created at: `{result.backup_path}`")
            lines.append("")
        
        # Transaction log
        if result.transaction_log_path:
            lines.append("## Transaction Log")
            lines.append(f"Transaction log saved to: `{result.transaction_log_path}`")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_directory_tree(
        self,
        directory: Optional[str] = None,
        max_depth: int = 3,
        show_files: bool = True
    ) -> str:
        """
        Generate a visual directory tree.
        
        Args:
            directory: Directory to visualize (None for project root)
            max_depth: Maximum depth to traverse
            show_files: Whether to show files or only directories
        
        Returns:
            Directory tree as string
        """
        if directory:
            root_path = self.project_root / directory
        else:
            root_path = self.project_root
        
        if not root_path.exists():
            return f"Directory does not exist: {root_path}"
        
        lines = [f"{root_path.name}/"]
        
        def add_tree_lines(path: Path, prefix: str = "", depth: int = 0):
            """Recursively add tree lines."""
            if depth >= max_depth:
                return
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            except PermissionError:
                return
            
            # Filter items
            if not show_files:
                items = [item for item in items if item.is_dir()]
            
            # Skip hidden and special directories
            skip_names = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}
            items = [item for item in items if item.name not in skip_names]
            
            for i, item in enumerate(items):
                is_last = (i == len(items) - 1)
                
                # Determine the tree characters
                if is_last:
                    current_prefix = "└── "
                    next_prefix = "    "
                else:
                    current_prefix = "├── "
                    next_prefix = "│   "
                
                # Add item name
                if item.is_dir():
                    lines.append(f"{prefix}{current_prefix}{item.name}/")
                    # Recurse into directory
                    add_tree_lines(item, prefix + next_prefix, depth + 1)
                elif item.is_symlink():
                    # Show symbolic link with arrow
                    try:
                        target = item.readlink()
                        lines.append(f"{prefix}{current_prefix}{item.name} -> {target}")
                    except:
                        lines.append(f"{prefix}{current_prefix}{item.name} -> [broken]")
                else:
                    lines.append(f"{prefix}{current_prefix}{item.name}")
        
        add_tree_lines(root_path)
        
        return "\n".join(lines)
    
    def create_markdown_report(
        self,
        result: ReorgResult,
        output_path: Optional[str] = None,
        file_mappings: Optional[List[Dict]] = None,
        validation_summary: Optional[Dict] = None,
        include_tree: bool = True
    ) -> str:
        """
        Create a comprehensive Markdown report file.
        
        Args:
            result: ReorgResult object
            output_path: Path to save the report (None for default)
            file_mappings: List of file mapping dictionaries
            validation_summary: Validation summary dictionary
            include_tree: Whether to include directory tree
        
        Returns:
            Path to the created report file
        """
        if output_path is None:
            output_path = self.project_root / "REORGANIZATION_SUMMARY.md"
        else:
            output_path = Path(output_path)
        
        lines = [
            "# Project Reorganization Report",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Project**: {self.project_root.name}",
            "",
            "---",
            "",
        ]
        
        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        if result.success:
            lines.append("✅ **Reorganization completed successfully!**")
        else:
            lines.append("❌ **Reorganization failed or completed with errors.**")
        lines.append("")
        lines.append(f"The project reorganization took {result.duration:.2f} seconds and processed:")
        lines.append(f"- **{result.files_moved}** files moved to new locations")
        lines.append(f"- **{result.links_created}** symbolic links created for backward compatibility")
        lines.append(f"- **{result.files_deleted}** obsolete files removed")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Detailed statistics
        lines.append("## Detailed Statistics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Status | {'✅ Success' if result.success else '❌ Failed'} |")
        lines.append(f"| Duration | {result.duration:.2f}s |")
        lines.append(f"| Files Moved | {result.files_moved} |")
        lines.append(f"| Links Created | {result.links_created} |")
        lines.append(f"| Files Deleted | {result.files_deleted} |")
        lines.append(f"| Errors | {len(result.errors)} |")
        lines.append(f"| Warnings | {len(result.warnings)} |")
        lines.append("")
        
        # Directory tree
        if include_tree:
            lines.append("## New Directory Structure")
            lines.append("")
            lines.append("```")
            lines.append(self.generate_directory_tree(max_depth=3, show_files=False))
            lines.append("```")
            lines.append("")
        
        # File mappings
        if file_mappings:
            lines.append("## File Relocations")
            lines.append("")
            lines.append("The following files were moved to new locations:")
            lines.append("")
            
            # Group by category
            by_category: Dict[str, List[Dict]] = {}
            for mapping in file_mappings:
                category = mapping.get('category', 'unknown')
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(mapping)
            
            for category, mappings in sorted(by_category.items()):
                lines.append(f"### {category}")
                lines.append("")
                for mapping in mappings:
                    old_path = mapping.get('old_path', 'unknown')
                    new_path = mapping.get('new_path', 'unknown')
                    lines.append(f"- `{old_path}` → `{new_path}`")
                lines.append("")
        
        # Validation results
        if validation_summary:
            lines.append("## Validation Results")
            lines.append("")
            
            overall_status = "✅ PASSED" if validation_summary.get('all_passed') else "❌ FAILED"
            lines.append(f"**Overall Status**: {overall_status}")
            lines.append("")
            
            lines.append("### Symbolic Links")
            links = validation_summary.get('links', {})
            if links.get('valid'):
                lines.append("✅ All symbolic links are valid and accessible")
            else:
                lines.append(f"❌ Found {links.get('broken_count', 0)} broken symbolic links")
            lines.append("")
            
            lines.append("### Python Imports")
            imports = validation_summary.get('imports', {})
            if imports.get('passed'):
                lines.append("✅ All Python imports are working correctly")
            else:
                lines.append(f"❌ Found {imports.get('failed_count', 0)} failed imports")
            lines.append("")
            
            lines.append("### File Integrity")
            files = validation_summary.get('files', {})
            if files.get('all_present'):
                lines.append("✅ All expected files are present")
            else:
                lines.append(f"❌ Found {files.get('missing_count', 0)} missing files")
            lines.append("")
        
        # Errors and warnings
        if result.errors:
            lines.append("## Errors")
            lines.append("")
            for error in result.errors:
                lines.append(f"- ❌ {error}")
            lines.append("")
        
        if result.warnings:
            lines.append("## Warnings")
            lines.append("")
            for warning in result.warnings:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")
        
        # Next steps
        lines.append("## Next Steps")
        lines.append("")
        if result.success:
            lines.append("1. Review the validation results above")
            lines.append("2. Test your application to ensure everything works correctly")
            lines.append("3. Update any documentation that references old file paths")
            lines.append("4. Consider removing symbolic links once all code is updated")
            lines.append("5. Keep the backup for at least 7 days before deleting")
        else:
            lines.append("1. Review the errors listed above")
            lines.append("2. Check the transaction log for detailed operation history")
            lines.append("3. Consider rolling back using the backup")
            lines.append("4. Fix any issues and retry the reorganization")
        lines.append("")
        
        # Backup and rollback info
        lines.append("## Backup and Rollback")
        lines.append("")
        if result.backup_path:
            lines.append(f"**Backup Location**: `{result.backup_path}`")
            lines.append("")
            lines.append("To rollback the reorganization:")
            lines.append("```bash")
            lines.append(f"# Restore from backup")
            lines.append(f"cp -r {result.backup_path}/* {self.project_root}/")
            lines.append("```")
        lines.append("")
        
        if result.transaction_log_path:
            lines.append(f"**Transaction Log**: `{result.transaction_log_path}`")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append(f"*Report generated by File Reorganization System on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*")
        
        # Write to file
        report_content = "\n".join(lines)
        output_path.write_text(report_content, encoding='utf-8')
        
        return str(output_path)
    
    def generate_statistics_summary(self, result: ReorgResult) -> Dict:
        """
        Generate statistics summary as dictionary.
        
        Args:
            result: ReorgResult object
        
        Returns:
            Dictionary with statistics
        """
        return {
            'success': result.success,
            'duration_seconds': result.duration,
            'start_time': result.start_time.isoformat(),
            'end_time': result.end_time.isoformat(),
            'files_moved': result.files_moved,
            'links_created': result.links_created,
            'files_deleted': result.files_deleted,
            'phases_completed': [phase.value for phase in result.phases_completed],
            'error_count': len(result.errors),
            'warning_count': len(result.warnings),
            'backup_path': result.backup_path,
            'transaction_log_path': result.transaction_log_path,
        }
