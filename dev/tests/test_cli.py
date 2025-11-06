"""
Unit tests for the CLI module.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys

from reorg_tool.cli import (
    create_parser,
    cmd_init,
    cmd_validate,
    cmd_report,
    main
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


class TestCreateParser:
    """Test argument parser creation."""
    
    def test_create_parser(self):
        """Test creating argument parser."""
        parser = create_parser()
        
        assert parser is not None
        assert parser.prog == 'reorg'
    
    def test_parser_has_subcommands(self):
        """Test that parser has all expected subcommands."""
        parser = create_parser()
        
        # Parse help to get subcommands
        with pytest.raises(SystemExit):
            parser.parse_args(['--help'])
    
    def test_parser_init_command(self):
        """Test init command parsing."""
        parser = create_parser()
        args = parser.parse_args(['init'])
        
        assert args.command == 'init'
        assert args.output == '.reorg_config.yaml'
    
    def test_parser_init_with_output(self):
        """Test init command with custom output."""
        parser = create_parser()
        args = parser.parse_args(['init', '--output', 'custom.yaml'])
        
        assert args.command == 'init'
        assert args.output == 'custom.yaml'
    
    def test_parser_reorganize_command(self):
        """Test reorganize command parsing."""
        parser = create_parser()
        args = parser.parse_args(['reorganize'])
        
        assert args.command == 'reorganize'
        assert args.dry_run is False
        assert args.no_backup is False
    
    def test_parser_reorganize_with_options(self):
        """Test reorganize command with options."""
        parser = create_parser()
        args = parser.parse_args([
            'reorganize',
            '--config', 'test.yaml',
            '--dry-run',
            '--no-backup'
        ])
        
        assert args.command == 'reorganize'
        assert args.config == 'test.yaml'
        assert args.dry_run is True
        assert args.no_backup is True
    
    def test_parser_rollback_command(self):
        """Test rollback command parsing."""
        parser = create_parser()
        args = parser.parse_args(['rollback'])
        
        assert args.command == 'rollback'
    
    def test_parser_validate_command(self):
        """Test validate command parsing."""
        parser = create_parser()
        args = parser.parse_args(['validate'])
        
        assert args.command == 'validate'
    
    def test_parser_report_command(self):
        """Test report command parsing."""
        parser = create_parser()
        args = parser.parse_args(['report'])
        
        assert args.command == 'report'


class TestCmdInit:
    """Test init command."""
    
    def test_cmd_init_success(self, temp_dir, capsys):
        """Test successful init command."""
        output_path = temp_dir / "test_config.yaml"
        
        args = MagicMock()
        args.output = str(output_path)
        
        result = cmd_init(args)
        
        assert result == 0
        assert output_path.exists()
        
        captured = capsys.readouterr()
        assert "Created default configuration file" in captured.out
    
    def test_cmd_init_existing_file(self, temp_dir, capsys):
        """Test init command with existing file."""
        output_path = temp_dir / "existing.yaml"
        output_path.write_text("existing content")
        
        args = MagicMock()
        args.output = str(output_path)
        
        result = cmd_init(args)
        
        assert result == 1
        
        captured = capsys.readouterr()
        assert "Error" in captured.err


class TestCmdValidate:
    """Test validate command."""
    
    def test_cmd_validate_success(self, temp_dir, capsys):
        """Test successful validate command."""
        args = MagicMock()
        args.project_root = str(temp_dir)
        
        result = cmd_validate(args)
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Validating" in captured.out
    
    def test_cmd_validate_nonexistent_project(self, capsys):
        """Test validate command with nonexistent project."""
        args = MagicMock()
        args.project_root = "/nonexistent/path"
        
        result = cmd_validate(args)
        
        assert result == 1
        
        captured = capsys.readouterr()
        assert "Error" in captured.err


class TestCmdReport:
    """Test report command."""
    
    def test_cmd_report_success(self, temp_dir, capsys):
        """Test successful report command."""
        # Create some directories
        (temp_dir / "subdir1").mkdir()
        (temp_dir / "subdir2").mkdir()
        
        args = MagicMock()
        args.project_root = str(temp_dir)
        args.output = None
        
        result = cmd_report(args)
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Directory Structure" in captured.out
    
    def test_cmd_report_with_output(self, temp_dir, capsys):
        """Test report command with output file."""
        output_path = temp_dir / "report.txt"
        
        args = MagicMock()
        args.project_root = str(temp_dir)
        args.output = str(output_path)
        
        result = cmd_report(args)
        
        assert result == 0
        assert output_path.exists()
        
        captured = capsys.readouterr()
        assert "Report saved" in captured.out


class TestMain:
    """Test main function."""
    
    def test_main_no_command(self, capsys):
        """Test main with no command."""
        result = main([])
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "usage:" in captured.out or "File Reorganization Tool" in captured.out
    
    def test_main_init_command(self, temp_dir):
        """Test main with init command."""
        output_path = temp_dir / "test.yaml"
        
        result = main(['init', '--output', str(output_path)])
        
        assert result == 0
        assert output_path.exists()
    
    def test_main_validate_command(self, temp_dir):
        """Test main with validate command."""
        result = main(['validate', '--project-root', str(temp_dir)])
        
        assert result == 0
    
    def test_main_report_command(self, temp_dir):
        """Test main with report command."""
        result = main(['report', '--project-root', str(temp_dir)])
        
        assert result == 0
    
    def test_main_unknown_command(self, capsys):
        """Test main with unknown command."""
        # This will fail at parsing stage
        with pytest.raises(SystemExit):
            main(['unknown_command'])


class TestCmdReorganize:
    """Test reorganize command."""
    
    @patch('reorg_tool.cli.ReorganizationOrchestrator')
    @patch('reorg_tool.cli.ConfigLoader')
    @patch('builtins.input', return_value='yes')
    def test_cmd_reorganize_with_confirmation(
        self,
        mock_input,
        mock_config_loader,
        mock_orchestrator,
        temp_dir
    ):
        """Test reorganize command with user confirmation."""
        from reorg_tool.cli import cmd_reorganize
        from reorg_tool.models import ReorgConfig, ReorgResult
        from datetime import datetime
        
        # Mock config
        mock_config = ReorgConfig(
            project_root=str(temp_dir),
            backup_enabled=True,
            dry_run=False
        )
        mock_config_loader.load_config.return_value = mock_config
        
        # Mock result
        mock_result = ReorgResult(
            success=True,
            start_time=datetime.now(),
            end_time=datetime.now(),
            files_moved=10,
            links_created=5,
            files_deleted=2
        )
        
        mock_orch_instance = MagicMock()
        mock_orch_instance.execute_reorganization.return_value = mock_result
        mock_orchestrator.return_value = mock_orch_instance
        
        args = MagicMock()
        args.config = None
        args.dry_run = False
        args.no_backup = False
        args.project_root = None
        
        result = cmd_reorganize(args)
        
        assert result == 0
        mock_input.assert_called_once()
        mock_orch_instance.execute_reorganization.assert_called_once()


class TestCmdRollback:
    """Test rollback command."""
    
    @patch('reorg_tool.cli.RollbackService')
    @patch('builtins.input', return_value='yes')
    def test_cmd_rollback_with_confirmation(
        self,
        mock_input,
        mock_rollback_service,
        temp_dir
    ):
        """Test rollback command with user confirmation."""
        from reorg_tool.cli import cmd_rollback
        
        # Create a dummy transaction log
        log_path = temp_dir / ".reorg_transaction_log.json"
        log_path.write_text('{"operations": []}')
        
        # Mock rollback result
        mock_result = {
            'success': True,
            'total_operations': 5,
            'reversed': 5,
            'failed': 0,
            'errors': []
        }
        
        mock_service_instance = MagicMock()
        mock_service_instance.execute_rollback.return_value = mock_result
        mock_rollback_service.return_value = mock_service_instance
        
        args = MagicMock()
        args.project_root = str(temp_dir)
        args.log = str(log_path)
        args.backup = None
        
        result = cmd_rollback(args)
        
        assert result == 0
        mock_input.assert_called_once()
        mock_service_instance.execute_rollback.assert_called_once()
