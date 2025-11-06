"""
File classifier module for the reorganization system.

Classifies files into categories based on patterns and rules.
"""

import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict
from difflib import SequenceMatcher

from .models import FileInfo, FileCategory
from .exceptions import ReorgError


class FileClassifier:
    """Classifies files into categories based on rules and patterns."""
    
    def __init__(self):
        """Initialize the file classifier with default rules."""
        self.classification_rules = self._build_classification_rules()
    
    def _build_classification_rules(self) -> Dict[FileCategory, List[dict]]:
        """
        Build classification rules for each category.
        
        Returns:
            Dictionary mapping categories to rule lists
        """
        rules = {
            # Test files (check first to avoid conflicts)
            FileCategory.DEV_TEST: [
                {'name_pattern': r'^test_.*\.py$'},
                {'path_pattern': r'^tests/.*\.py$'},
            ],
            
            # Core API files
            FileCategory.CORE_API: [
                {'path_pattern': r'^api/.*\.py$'},
                {'name_pattern': r'^app\.py$', 'path_contains': 'api'},
            ],
            
            # Core model files
            FileCategory.CORE_MODEL: [
                {'name_exact': 'predictor.py'},
                {'name_exact': 'enhanced_predictor.py'},
                {'name_exact': 'domain_priors.py'},
                {'name_exact': 'feature_contribution_fast.py'},
                {'name_exact': 'correlation_analyzer.py'},
                {'name_exact': 'version_manager.py'},
                {'path_pattern': r'^models/.*\.py$'},
            ],
            
            # Core data files
            FileCategory.CORE_DATA: [
                {'path_pattern': r'^data/processed/.*\.csv$'},
                {'name_exact': 'hiv_data_processed.csv'},
            ],
            
            # Configuration files
            FileCategory.CONFIG: [
                {'name_exact': 'requirements.txt'},
                {'name_exact': 'Dockerfile'},
                {'name_exact': 'docker-compose.yml'},
                {'name_exact': '.dockerignore'},
                {'extension': '.yml'},
                {'extension': '.yaml'},
                {'extension': '.toml'},
            ],
            
            # User documentation
            FileCategory.DOC_USER: [
                {'name_exact': 'README.md'},
                {'name_exact': 'USER_MANUAL.md'},
                {'name_exact': 'API_DOCUMENTATION.md'},
                {'name_exact': 'API_USAGE_EXAMPLES.md'},
            ],
            
            # Deployment documentation
            FileCategory.DOC_DEPLOYMENT: [
                {'name_pattern': r'^DEPLOYMENT.*\.md$'},
                {'name_pattern': r'.*CHECKLIST\.md$'},
                {'name_exact': 'LOCAL_DEMO_GUIDE.md'},
                {'name_exact': 'SUBMISSION_GUIDE.md'},
                {'name_exact': 'WHAT_TO_SUBMIT.md'},
            ],
            
            # Technical documentation
            FileCategory.DOC_TECHNICAL: [
                {'name_exact': 'AI_INNOVATION.md'},
                {'name_exact': 'IMPLEMENTATION_LOG.md'},
                {'path_pattern': r'^docs/.*\.md$'},
            ],
            
            # Project documentation
            FileCategory.DOC_PROJECT: [
                {'name_pattern': r'^PROJECT.*\.md$'},
                {'name_exact': 'CORE_DELIVERY_FILES.md'},
                {'name_exact': 'PROJECT_STATUS.md'},
                {'name_exact': 'PROJECT_SUMMARY.md'},
            ],
            
            # Development scripts
            FileCategory.DEV_SCRIPT: [
                {'name_pattern': r'^evaluate_.*\.py$'},
                {'name_pattern': r'^visualize_.*\.py$'},
                {'name_pattern': r'^check_.*\.py$'},
                {'name_pattern': r'^verify_.*\.py$'},
                {'name_pattern': r'^generate_.*\.py$'},
                {'name_pattern': r'^run_.*\.py$'},
                {'name_pattern': r'^optimize_.*\.py$'},
                {'extension': '.sh'},
            ],
            
            # Utility files
            FileCategory.DEV_UTIL: [
                {'path_pattern': r'^utils/.*\.py$'},
            ],
            
            # Temporary files
            FileCategory.DEV_TEMP: [
                {'name_pattern': r'^fix_.*\.py$'},
                {'name_pattern': r'.*中文.*'},
                {'name_pattern': r'^temp_.*'},
                {'name_pattern': r'.*_temp\..*'},
                {'extension': '.tmp'},
                {'extension': '.bak'},
            ],
            
            # Duplicate files (will be detected separately)
            FileCategory.DUPLICATE: [],
            
            # Obsolete files
            FileCategory.OBSOLETE: [
                {'path_pattern': r'^docs_for_review/.*'},
                {'path_pattern': r'^deployment/.*'},
            ],
        }
        
        return rules
    
    def classify_file(self, file_info: FileInfo) -> FileCategory:
        """
        Classify a single file based on rules.
        
        Args:
            file_info: File information
        
        Returns:
            FileCategory enum value
        """
        # Check each category's rules
        for category, rules in self.classification_rules.items():
            if self._matches_rules(file_info, rules):
                return category
        
        # Default to unknown if no rules match
        return FileCategory.UNKNOWN
    
    def classify_batch(self, files: List[FileInfo]) -> Dict[FileCategory, List[FileInfo]]:
        """
        Classify multiple files at once.
        
        Args:
            files: List of file information
        
        Returns:
            Dictionary mapping categories to file lists
        """
        classified = defaultdict(list)
        
        for file_info in files:
            category = self.classify_file(file_info)
            classified[category].append(file_info)
        
        # Detect duplicates after initial classification
        duplicates = self.detect_duplicates(files)
        if duplicates:
            # Move duplicates to DUPLICATE category
            for dup_group in duplicates:
                for file_info in dup_group['files'][1:]:  # Keep first, mark rest as duplicates
                    # Remove from original category
                    original_category = self.classify_file(file_info)
                    if file_info in classified[original_category]:
                        classified[original_category].remove(file_info)
                    # Add to duplicates
                    classified[FileCategory.DUPLICATE].append(file_info)
        
        return dict(classified)
    
    def _matches_rules(self, file_info: FileInfo, rules: List[dict]) -> bool:
        """
        Check if file matches any of the rules.
        
        Args:
            file_info: File information
            rules: List of rule dictionaries
        
        Returns:
            True if any rule matches
        """
        for rule in rules:
            if self._matches_single_rule(file_info, rule):
                return True
        return False
    
    def _matches_single_rule(self, file_info: FileInfo, rule: dict) -> bool:
        """
        Check if file matches a single rule.
        
        Args:
            file_info: File information
            rule: Rule dictionary
        
        Returns:
            True if rule matches
        """
        # Exact name match
        if 'name_exact' in rule:
            if file_info.name == rule['name_exact']:
                return True
        
        # Name pattern match (regex)
        if 'name_pattern' in rule:
            if re.match(rule['name_pattern'], file_info.name):
                return True
        
        # Path pattern match (regex)
        if 'path_pattern' in rule:
            if re.match(rule['path_pattern'], file_info.path):
                return True
        
        # Path contains string
        if 'path_contains' in rule:
            if rule['path_contains'] in file_info.path:
                return True
        
        # Extension match
        if 'extension' in rule:
            if file_info.extension == rule['extension']:
                return True
        
        return False
    
    def detect_duplicates(self, files: List[FileInfo]) -> List[dict]:
        """
        Detect duplicate files based on name similarity.
        
        Args:
            files: List of file information
        
        Returns:
            List of duplicate groups, each containing similar files
        """
        duplicates = []
        processed = set()
        
        for i, file1 in enumerate(files):
            if file1.path in processed:
                continue
            
            similar_files = [file1]
            
            for j, file2 in enumerate(files):
                if i >= j or file2.path in processed:
                    continue
                
                # Calculate name similarity
                similarity = self._calculate_similarity(file1.name, file2.name)
                
                # If names are very similar (>0.8), consider as duplicates
                if similarity > 0.8:
                    similar_files.append(file2)
                    processed.add(file2.path)
            
            # If we found similar files, add to duplicates
            if len(similar_files) > 1:
                duplicates.append({
                    'files': similar_files,
                    'similarity': self._calculate_similarity(
                        similar_files[0].name,
                        similar_files[1].name
                    )
                })
                processed.add(file1.path)
        
        return duplicates
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two filenames.
        
        Args:
            name1: First filename
            name2: Second filename
        
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize names (lowercase, remove extensions)
        norm1 = Path(name1).stem.lower()
        norm2 = Path(name2).stem.lower()
        
        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def get_category_mapping(self, category: FileCategory) -> str:
        """
        Get the target directory path for a category.
        
        Args:
            category: File category
        
        Returns:
            Target directory path
        """
        mapping = {
            FileCategory.CORE_API: 'core/api',
            FileCategory.CORE_MODEL: 'core/models',
            FileCategory.CORE_DATA: 'core/data/processed',
            FileCategory.CONFIG: 'config',
            FileCategory.DOC_USER: 'docs/user',
            FileCategory.DOC_DEPLOYMENT: 'docs/deployment',
            FileCategory.DOC_TECHNICAL: 'docs/technical',
            FileCategory.DOC_PROJECT: 'docs/project',
            FileCategory.DEV_TEST: 'dev/tests',
            FileCategory.DEV_SCRIPT: 'dev/scripts',
            FileCategory.DEV_UTIL: 'dev/utils',
            FileCategory.DEV_TEMP: 'dev/temp',
            FileCategory.DUPLICATE: 'dev/temp/duplicates',
            FileCategory.OBSOLETE: 'dev/temp/obsolete',
            FileCategory.UNKNOWN: 'dev/temp/unknown',
        }
        
        return mapping.get(category, 'dev/temp/unknown')
    
    def generate_classification_report(
        self,
        classified: Dict[FileCategory, List[FileInfo]]
    ) -> str:
        """
        Generate a human-readable classification report.
        
        Args:
            classified: Dictionary of classified files
        
        Returns:
            Report string
        """
        report_lines = ["# File Classification Report\n"]
        
        total_files = sum(len(files) for files in classified.values())
        report_lines.append(f"Total files: {total_files}\n")
        
        for category, files in sorted(classified.items(), key=lambda x: x[0].value):
            if not files:
                continue
            
            report_lines.append(f"\n## {category.value.upper()} ({len(files)} files)")
            report_lines.append(f"Target: {self.get_category_mapping(category)}\n")
            
            for file_info in sorted(files, key=lambda f: f.path):
                size_kb = file_info.size / 1024
                report_lines.append(
                    f"  - {file_info.path} ({size_kb:.1f} KB)"
                )
        
        return "\n".join(report_lines)
