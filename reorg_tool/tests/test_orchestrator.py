"""
Unit tests for the orchestrator module.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from reorg_tool.orchestrator import ReorganizationOrchestrator
from reorg_tool.models import ReorgConfig, ReorgPhase
from reorg_tool.exceptions import ReorgError


@pytest.fixture
def temp_project():
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create test directory structure
    project_root = Path(temp_dir) / "test_project"
    project_root.mkdir()
    
    # Create some test files
    (project_root / "app.py").write_text("# API file\ndef main(): pass")
    (project_root / "predictor.py").write_text("# Model file\nclass Predictor: pass")
    (project_root / "requirements.txt").write_text("flask==2.0.0")
    (project_root / "README.md").write_text("# Project README")
    (project_root / "test_app.py").write_text("# Test file\ndef test_main(): pass")
    
    # Create subdirectories
    (project_root / "models").mkdir()
    (project_root / "models" / "model.py").write_text("# Model\nclass Model: pass")
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def config(temp_project):
    """Create a ReorgConfig for testing."""
    return ReorgConfig(
        project_root=str(temp_project),
        backup_enabled=True,
        dry_run=False,
    )


@pytest.fixture
def orchestrator(config):
    """Create a ReorganizationOrchestrator instance for testing."""
    return ReorganizationOrchestrator(config)


class TestOrchestratorInit:
    """Test ReorganizationOrchestrator initialization."""
    
    def test_init_with_valid_config(self, config):
        """Test initialization with valid configuration."""
        orchestrator = ReorganizationOrchestrator(config)
        
        assert orchestrator.config == config
        assert orchestrator.project_root.exists()
        assert orchestrator.scanner is not None
        assert orchestrator.classifier is not None
        assert orchestrator.analyzer is not None
        assert orchestrator.mover is not None
        assert orchestrator.linker is not None
    
    def test_init_with_invalid_path(self):
        """Test initialization with invalid project root."""
        config = ReorgConfig(project_root="/nonexistent/path")
        
        with pytest.raises(ReorgError):
            ReorganizationOrchestrator(config)


class TestExecutePhase:
    """Test individual phase execution."""
    
    def test_phase_scan(self, orchestrator):
        """Test scan phase."""
        result = orchestrator.execute_phase(ReorgPhase.SCAN)
        
        assert result is True
        assert len(orchestrator.scanned_files) > 0
    
    def test_phase_classify(self, orchestrator):
        """Test classify phase."""
        # First scan
        orchestrator.execute_phase(ReorgPhase.SCAN)
        
        # Then classify
        result = orchestrator.execute_phase(ReorgPhase.CLASSIFY)
        
        assert result is True
        assert len(orchestrator.classified_files) > 0
    
    def test_phase_analyze(self, orchestrator):
        """Test analyze phase."""
        # First scan
        orchestrator.execute_phase(ReorgPhase.SCAN)
        
        # Then analyze
        result = orchestrator.execute_phase(ReorgPhase.ANALYZE)
        
        assert result is True
        assert orchestrator.dependency_graph is not None
    
    def test_phase_backup(self, orchestrator):
        """Test backup phase."""
        result = orchestrator.execute_phase(ReorgPhase.BACKUP)
        
        assert result is True
        assert orchestrator.config.backup_path is not None
        assert Path(orchestrator.config.backup_path).exists()
    
    def test_phase_backup_disabled(self, config):
        """Test backup phase when disabled."""
        config.backup_enabled = False
        orchestrator = ReorganizationOrchestrator(config)
        
        result = orchestrator.execute_phase(ReorgPhase.BACKUP)
        
        assert result is True
    
    def test_phase_create_structure(self, orchestrator):
        """Test create structure phase."""
        result = orchestrator.execute_phase(ReorgPhase.CREATE_STRUCTURE)
        
        assert result is True
        assert (orchestrator.project_root / "core").exists()
        assert (orchestrator.project_root / "docs").exists()
        assert (orchestrator.project_root / "dev").exists()
    
    def test_phase_move_core(self, orchestrator):
        """Test move core files phase."""
        # Setup
        orchestrator.execute_phase(ReorgPhase.SCAN)
        orchestrator.execute_phase(ReorgPhase.CLASSIFY)
        orchestrator.execute_phase(ReorgPhase.CREATE_STRUCTURE)
        
        # Execute
        result = orchestrator.execute_phase(ReorgPhase.MOVE_CORE)
        
        assert result is True
    
    def test_phase_create_links(self, orchestrator):
        """Test create links phase."""
        # Setup
        orchestrator.execute_phase(ReorgPhase.SCAN)
        orchestrator.execute_phase(ReorgPhase.CLASSIFY)
        orchestrator.execute_phase(ReorgPhase.CREATE_STRUCTURE)
        orchestrator.execute_phase(ReorgPhase.MOVE_CORE)
        
        # Execute
        result = orchestrator.execute_phase(ReorgPhase.CREATE_LINKS)
        
        assert result is True
    
    def test_phase_validate(self, orchestrator):
        """Test validate phase."""
        result = orchestrator.execute_phase(ReorgPhase.VALIDATE)
        
        assert result is True
    
    def test_phase_report(self, orchestrator):
        """Test report phase."""
        # Initialize result
        orchestrator.result = orchestrator.execute_reorganization.__wrapped__(orchestrator) if hasattr(orchestrator.execute_reorganization, '__wrapped__') else None
        if orchestrator.result is None:
            from reorg_tool.models import ReorgResult
            orchestrator.result = ReorgResult(
                success=True,
                start_time=datetime.now(),
                end_time=datetime.now(),
            )
        
        result = orchestrator.execute_phase(ReorgPhase.REPORT)
        
        assert result is True


class TestExecuteReorganization:
    """Test complete reorganization execution."""
    
    def test_execute_reorganization_basic(self, orchestrator):
        """Test basic reorganization execution."""
        result = orchestrator.execute_reorganization()
        
        assert result is not None
        assert result.start_time is not None
        assert result.end_time is not None
        assert len(result.phases_completed) > 0
    
    def test_execute_reorganization_creates_backup(self, orchestrator):
        """Test that reorganization creates backup."""
        result = orchestrator.execute_reorganization()
        
        if orchestrator.config.backup_enabled:
            assert result.backup_path is not None
            assert Path(result.backup_path).exists()
    
    def test_execute_reorganization_creates_transaction_log(self, orchestrator):
        """Test that reorganization creates transaction log."""
        result = orchestrator.execute_reorganization()
        
        assert result.transaction_log_path is not None
        assert Path(result.transaction_log_path).exists()
    
    def test_execute_reorganization_tracks_phases(self, orchestrator):
        """Test that reorganization tracks completed phases."""
        result = orchestrator.execute_reorganization()
        
        assert ReorgPhase.SCAN in result.phases_completed
        assert ReorgPhase.CLASSIFY in result.phases_completed
        assert ReorgPhase.BACKUP in result.phases_completed


class TestGetProgress:
    """Test progress tracking."""
    
    def test_get_progress_initial(self, orchestrator):
        """Test progress at initialization."""
        # Initialize result
        from reorg_tool.models import ReorgResult
        orchestrator.result = ReorgResult(
            success=False,
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        
        progress = orchestrator.get_progress()
        
        assert progress['total_phases'] == 12
        assert progress['completed_phases'] == 0
        assert progress['progress_percentage'] == 0
    
    def test_get_progress_after_phases(self, orchestrator):
        """Test progress after completing some phases."""
        from reorg_tool.models import ReorgResult
        orchestrator.result = ReorgResult(
            success=False,
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        
        # Complete some phases
        orchestrator.execute_phase(ReorgPhase.SCAN)
        orchestrator.result.phases_completed.append(ReorgPhase.SCAN)
        
        orchestrator.execute_phase(ReorgPhase.CLASSIFY)
        orchestrator.result.phases_completed.append(ReorgPhase.CLASSIFY)
        
        progress = orchestrator.get_progress()
        
        assert progress['completed_phases'] == 2
        assert progress['progress_percentage'] > 0
        assert progress['current_phase'] == ReorgPhase.CLASSIFY.value


class TestMoveFile:
    """Test file moving helper."""
    
    def test_move_file_success(self, orchestrator, temp_project):
        """Test successful file move."""
        # Create structure
        (temp_project / "target").mkdir()
        
        # Initialize result
        from reorg_tool.models import ReorgResult
        orchestrator.result = ReorgResult(
            success=False,
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        
        # Move file
        result = orchestrator._move_file("app.py", "target/app.py")
        
        assert result is True
        assert len(orchestrator.file_mappings) == 1
        assert orchestrator.file_mappings[0]['old_path'] == "app.py"
        assert orchestrator.file_mappings[0]['new_path'] == "target/app.py"
    
    def test_move_file_nonexistent(self, orchestrator):
        """Test moving nonexistent file."""
        from reorg_tool.models import ReorgResult
        orchestrator.result = ReorgResult(
            success=False,
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        
        result = orchestrator._move_file("nonexistent.py", "target/file.py")
        
        assert result is False
    
    def test_move_file_same_path(self, orchestrator):
        """Test moving file to same path."""
        from reorg_tool.models import ReorgResult
        orchestrator.result = ReorgResult(
            success=False,
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        
        result = orchestrator._move_file("app.py", "app.py")
        
        assert result is False


class TestErrorHandling:
    """Test error handling in orchestrator."""
    
    def test_phase_failure_stops_execution(self, orchestrator, monkeypatch):
        """Test that phase failure stops execution."""
        # Make scan phase fail
        def failing_scan():
            raise Exception("Scan failed")
        
        monkeypatch.setattr(orchestrator, '_phase_scan', failing_scan)
        
        result = orchestrator.execute_reorganization()
        
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_error_recorded_in_result(self, orchestrator, monkeypatch):
        """Test that errors are recorded in result."""
        def failing_classify():
            raise Exception("Classification failed")
        
        monkeypatch.setattr(orchestrator, '_phase_classify', failing_classify)
        
        result = orchestrator.execute_reorganization()
        
        assert len(result.errors) > 0
        assert "Classification failed" in result.errors[0]
