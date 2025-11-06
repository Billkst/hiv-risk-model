"""
Orchestrator module for the reorganization system.

Coordinates the complete reorganization workflow.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from .models import ReorgConfig, ReorgResult, ReorgPhase, FileCategory
from .scanner import FileScanner
from .classifier import FileClassifier
from .analyzer import DependencyAnalyzer
from .backup import BackupService
from .transaction_log import TransactionLog
from .mover import FileMover
from .linker import SymbolicLinker
from .validator import ReorganizationValidator
from .reporter import ReorganizationReporter
from .rollback import RollbackService
from .exceptions import ReorgError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReorganizationOrchestrator:
    """Orchestrates the complete reorganization workflow."""
    
    def __init__(self, config: ReorgConfig):
        """
        Initialize the orchestrator.
        
        Args:
            config: Reorganization configuration
        """
        self.config = config
        self.project_root = Path(config.project_root).resolve()
        
        if not self.project_root.exists():
            raise ReorgError(f"Project root does not exist: {config.project_root}")
        
        # Initialize components
        self.scanner = FileScanner(str(self.project_root))
        self.classifier = FileClassifier()
        self.analyzer = DependencyAnalyzer(str(self.project_root))
        self.backup_service = BackupService(str(self.project_root))
        self.reporter = ReorganizationReporter(str(self.project_root))
        self.rollback_service = RollbackService(str(self.project_root))
        
        # Transaction log
        log_path = self.project_root / ".reorg_transaction_log.json"
        self.transaction_log = TransactionLog(str(log_path))
        
        # File mover and linker with transaction log
        self.mover = FileMover(str(self.project_root), self.transaction_log)
        self.linker = SymbolicLinker(str(self.project_root), self.transaction_log)
        self.validator = ReorganizationValidator(str(self.project_root))
        
        # State
        self.scanned_files = []
        self.classified_files = {}
        self.dependency_graph = None
        self.file_mappings = []
        
        # Result
        self.result = None
    
    def execute_reorganization(self) -> ReorgResult:
        """
        Execute the complete reorganization workflow.
        
        Returns:
            ReorgResult with reorganization results
        """
        start_time = datetime.now()
        
        # Initialize result
        self.result = ReorgResult(
            success=False,
            start_time=start_time,
            end_time=start_time,  # Will be updated
        )
        
        logger.info("=" * 60)
        logger.info("Starting Project Reorganization")
        logger.info("=" * 60)
        
        try:
            # Execute phases in order
            phases = [
                ReorgPhase.SCAN,
                ReorgPhase.CLASSIFY,
                ReorgPhase.ANALYZE,
                ReorgPhase.BACKUP,
                ReorgPhase.CREATE_STRUCTURE,
                ReorgPhase.MOVE_CORE,
                ReorgPhase.MOVE_DOCS,
                ReorgPhase.MOVE_DEV,
                ReorgPhase.CREATE_LINKS,
                ReorgPhase.VALIDATE,
                ReorgPhase.CLEANUP,
                ReorgPhase.REPORT,
            ]
            
            for phase in phases:
                if not self.execute_phase(phase):
                    logger.error(f"Phase {phase.value} failed")
                    self.result.success = False
                    break
                
                self.result.phases_completed.append(phase)
            else:
                # All phases completed successfully
                self.result.success = True
                logger.info("✅ Reorganization completed successfully!")
        
        except Exception as e:
            logger.error(f"Reorganization failed: {e}")
            self.result.add_error(str(e))
            self.result.success = False
        
        finally:
            self.result.end_time = datetime.now()
            self.result.transaction_log_path = str(self.transaction_log.log_path)
            
            if self.config.backup_enabled:
                self.result.backup_path = self.config.backup_path
        
        logger.info("=" * 60)
        logger.info(f"Reorganization {'SUCCESS' if self.result.success else 'FAILED'}")
        logger.info(f"Duration: {self.result.duration:.2f} seconds")
        logger.info("=" * 60)
        
        return self.result
    
    def execute_phase(self, phase: ReorgPhase) -> bool:
        """
        Execute a single reorganization phase.
        
        Args:
            phase: Phase to execute
        
        Returns:
            True if phase succeeded, False otherwise
        """
        # Initialize result if not exists
        if self.result is None:
            self.result = ReorgResult(
                success=False,
                start_time=datetime.now(),
                end_time=datetime.now(),
            )
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Phase: {phase.value.upper()}")
        logger.info(f"{'='*60}")
        
        try:
            if phase == ReorgPhase.SCAN:
                return self._phase_scan()
            elif phase == ReorgPhase.CLASSIFY:
                return self._phase_classify()
            elif phase == ReorgPhase.ANALYZE:
                return self._phase_analyze()
            elif phase == ReorgPhase.BACKUP:
                return self._phase_backup()
            elif phase == ReorgPhase.CREATE_STRUCTURE:
                return self._phase_create_structure()
            elif phase == ReorgPhase.MOVE_CORE:
                return self._phase_move_core()
            elif phase == ReorgPhase.MOVE_DOCS:
                return self._phase_move_docs()
            elif phase == ReorgPhase.MOVE_DEV:
                return self._phase_move_dev()
            elif phase == ReorgPhase.CREATE_LINKS:
                return self._phase_create_links()
            elif phase == ReorgPhase.VALIDATE:
                return self._phase_validate()
            elif phase == ReorgPhase.CLEANUP:
                return self._phase_cleanup()
            elif phase == ReorgPhase.REPORT:
                return self._phase_report()
            else:
                logger.error(f"Unknown phase: {phase}")
                return False
        
        except Exception as e:
            logger.error(f"Phase {phase.value} failed: {e}")
            self.result.add_error(f"Phase {phase.value}: {str(e)}")
            return False
    
    def _phase_scan(self) -> bool:
        """Scan project files."""
        logger.info("Scanning project files...")
        
        self.scanned_files = self.scanner.scan_directory()
        
        logger.info(f"Found {len(self.scanned_files)} files")
        logger.info(f"Total size: {self.scanner.get_total_size() / 1024 / 1024:.2f} MB")
        
        return True
    
    def _phase_classify(self) -> bool:
        """Classify files by category."""
        logger.info("Classifying files...")
        
        self.classified_files = self.classifier.classify_batch(self.scanned_files)
        
        # Log classification results
        for category, files in self.classified_files.items():
            logger.info(f"  {category.value}: {len(files)} files")
        
        return True
    
    def _phase_analyze(self) -> bool:
        """Analyze dependencies."""
        logger.info("Analyzing dependencies...")
        
        # Build dependency graph
        self.dependency_graph = self.analyzer.build_dependency_graph(self.scanned_files)
        
        logger.info(f"Found {len(self.dependency_graph.import_edges)} import dependencies")
        logger.info(f"Found {len(self.dependency_graph.path_edges)} path dependencies")
        
        return True
    
    def _phase_backup(self) -> bool:
        """Create backup."""
        if not self.config.backup_enabled:
            logger.info("Backup disabled, skipping...")
            return True
        
        logger.info("Creating backup...")
        
        backup_path = self.backup_service.create_backup(self.config.backup_path)
        self.config.backup_path = backup_path
        
        # Verify backup
        if self.backup_service.verify_backup(backup_path):
            logger.info(f"✅ Backup created and verified: {backup_path}")
            return True
        else:
            logger.error("❌ Backup verification failed")
            return False
    
    def _phase_create_structure(self) -> bool:
        """Create new directory structure."""
        logger.info("Creating directory structure...")
        
        directories = [
            "core",
            "core/api",
            "core/models",
            "core/data",
            "config",
            "docs",
            "docs/user",
            "docs/deployment",
            "docs/technical",
            "docs/project",
            "dev",
            "dev/tests",
            "dev/scripts",
            "dev/utils",
            "dev/temp",
            "scripts",
        ]
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"  Created: {dir_path}/")
        
        return True
    
    def _phase_move_core(self) -> bool:
        """Move core files."""
        logger.info("Moving core files...")
        
        moved_count = 0
        
        # Move API files
        if FileCategory.CORE_API in self.classified_files:
            for file_info in self.classified_files[FileCategory.CORE_API]:
                new_path = f"core/api/{file_info.name}"
                if self._move_file(file_info.path, new_path):
                    moved_count += 1
        
        # Move model files
        if FileCategory.CORE_MODEL in self.classified_files:
            for file_info in self.classified_files[FileCategory.CORE_MODEL]:
                new_path = f"core/models/{file_info.name}"
                if self._move_file(file_info.path, new_path):
                    moved_count += 1
        
        # Move config files
        if FileCategory.CONFIG in self.classified_files:
            for file_info in self.classified_files[FileCategory.CONFIG]:
                new_path = f"config/{file_info.name}"
                if self._move_file(file_info.path, new_path):
                    moved_count += 1
        
        logger.info(f"Moved {moved_count} core files")
        self.result.files_moved += moved_count
        
        return True
    
    def _phase_move_docs(self) -> bool:
        """Move documentation files."""
        logger.info("Moving documentation files...")
        
        moved_count = 0
        
        doc_categories = {
            FileCategory.DOC_USER: "docs/user",
            FileCategory.DOC_DEPLOYMENT: "docs/deployment",
            FileCategory.DOC_TECHNICAL: "docs/technical",
            FileCategory.DOC_PROJECT: "docs/project",
        }
        
        for category, target_dir in doc_categories.items():
            if category in self.classified_files:
                for file_info in self.classified_files[category]:
                    new_path = f"{target_dir}/{file_info.name}"
                    if self._move_file(file_info.path, new_path):
                        moved_count += 1
        
        logger.info(f"Moved {moved_count} documentation files")
        self.result.files_moved += moved_count
        
        return True
    
    def _phase_move_dev(self) -> bool:
        """Move development files."""
        logger.info("Moving development files...")
        
        moved_count = 0
        
        dev_categories = {
            FileCategory.DEV_TEST: "dev/tests",
            FileCategory.DEV_SCRIPT: "dev/scripts",
            FileCategory.DEV_UTIL: "dev/utils",
            FileCategory.DEV_TEMP: "dev/temp",
        }
        
        for category, target_dir in dev_categories.items():
            if category in self.classified_files:
                for file_info in self.classified_files[category]:
                    new_path = f"{target_dir}/{file_info.name}"
                    if self._move_file(file_info.path, new_path):
                        moved_count += 1
        
        logger.info(f"Moved {moved_count} development files")
        self.result.files_moved += moved_count
        
        return True
    
    def _phase_create_links(self) -> bool:
        """Create symbolic links."""
        logger.info("Creating symbolic links...")
        
        links_created = 0
        
        # Create links for moved files
        for mapping in self.file_mappings:
            try:
                self.linker.create_link(mapping['old_path'], mapping['new_path'])
                links_created += 1
                logger.info(f"  Link: {mapping['old_path']} -> {mapping['new_path']}")
            except Exception as e:
                logger.warning(f"  Failed to create link: {mapping['old_path']} - {e}")
                self.result.add_warning(f"Link creation failed: {mapping['old_path']}")
        
        logger.info(f"Created {links_created} symbolic links")
        self.result.links_created = links_created
        
        return True
    
    def _phase_validate(self) -> bool:
        """Validate reorganization results."""
        logger.info("Validating reorganization...")
        
        # Validate links
        self.validator.validate_links()
        
        # Validate file integrity
        expected_files = [mapping['new_path'] for mapping in self.file_mappings]
        self.validator.validate_file_integrity(expected_files)
        
        # Generate validation report
        validation_report = self.validator.generate_validation_report()
        logger.info("\n" + validation_report)
        
        if not self.validator.validation_checks.all_passed:
            logger.warning("⚠️ Some validation checks failed")
            self.result.add_warning("Validation checks failed")
        else:
            logger.info("✅ All validation checks passed")
        
        return True
    
    def _phase_cleanup(self) -> bool:
        """Cleanup phase."""
        logger.info("Cleanup phase...")
        
        # This phase can be used for removing empty directories, etc.
        # For now, just log
        logger.info("Cleanup completed")
        
        return True
    
    def _phase_report(self) -> bool:
        """Generate final report."""
        logger.info("Generating final report...")
        
        # Get validation summary
        validation_summary = self.validator.get_validation_summary()
        
        # Create markdown report
        report_path = self.reporter.create_markdown_report(
            self.result,
            file_mappings=self.file_mappings,
            validation_summary=validation_summary,
            include_tree=True
        )
        
        logger.info(f"Report saved to: {report_path}")
        
        return True
    
    def _move_file(self, old_path: str, new_path: str) -> bool:
        """
        Move a file and record the mapping.
        
        Args:
            old_path: Original file path
            new_path: New file path
        
        Returns:
            True if successful
        """
        try:
            # Skip if file doesn't exist
            if not (self.project_root / old_path).exists():
                return False
            
            # Skip if already at destination
            if old_path == new_path:
                return False
            
            # Move file
            self.mover.move_file(old_path, new_path)
            
            # Record mapping
            self.file_mappings.append({
                'old_path': old_path,
                'new_path': new_path,
                'category': 'unknown',
            })
            
            return True
        
        except Exception as e:
            logger.warning(f"Failed to move {old_path}: {e}")
            self.result.add_warning(f"Move failed: {old_path}")
            return False
    
    def get_progress(self) -> Dict:
        """
        Get current progress information.
        
        Returns:
            Dictionary with progress information
        """
        total_phases = 12
        completed_phases = 0
        current_phase = None
        
        if self.result and hasattr(self.result, 'phases_completed'):
            completed_phases = len(self.result.phases_completed)
            if self.result.phases_completed:
                current_phase = self.result.phases_completed[-1].value
        
        return {
            'total_phases': total_phases,
            'completed_phases': completed_phases,
            'progress_percentage': (completed_phases / total_phases) * 100 if total_phases > 0 else 0,
            'current_phase': current_phase,
        }
