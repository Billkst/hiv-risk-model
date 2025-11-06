"""
Unit tests for the configuration loader.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from reorg_tool.config_loader import ConfigLoader
from reorg_tool.models import ReorgConfig
from reorg_tool.exceptions import ReorgError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config_file(temp_dir):
    """Create a sample configuration file."""
    config_content = """
reorganization:
  project_root: "."
  backup:
    enabled: true
    retention_days: 7
  symbolic_links:
    enabled: true
  dry_run: false
  logging:
    level: "INFO"
"""
    config_path = temp_dir / "test_config.yaml"
    config_path.write_text(config_content)
    
    # Create a dummy project root
    project_root = temp_dir / "project"
    project_root.mkdir()
    
    return config_path


class TestLoadConfig:
    """Test configuration loading."""
    
    def test_load_config_from_file(self, sample_config_file, temp_dir):
        """Test loading configuration from file."""
        # Update config to use temp project root
        config_content = f"""
reorganization:
  project_root: "{temp_dir / 'project'}"
  backup:
    enabled: true
  dry_run: false
"""
        sample_config_file.write_text(config_content)
        
        config = ConfigLoader.load_config(str(sample_config_file))
        
        assert isinstance(config, ReorgConfig)
        assert config.backup_enabled is True
        assert config.dry_run is False
    
    def test_load_config_without_file(self, temp_dir):
        """Test loading default configuration."""
        # Change to temp dir so default "." works
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)
            config = ConfigLoader.load_config()
            
            assert isinstance(config, ReorgConfig)
            assert config.backup_enabled is True
        finally:
            os.chdir(original_dir)
    
    def test_load_config_nonexistent_file(self):
        """Test loading from nonexistent file."""
        with pytest.raises(ReorgError) as exc_info:
            ConfigLoader.load_config("/nonexistent/config.yaml")
        
        assert "not found" in str(exc_info.value)
    
    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading invalid YAML."""
        invalid_config = temp_dir / "invalid.yaml"
        invalid_config.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ReorgError) as exc_info:
            ConfigLoader.load_config(str(invalid_config))
        
        assert "Invalid YAML" in str(exc_info.value)
    
    def test_load_config_empty_file(self, temp_dir):
        """Test loading empty configuration file."""
        empty_config = temp_dir / "empty.yaml"
        empty_config.write_text("")
        
        # Should use defaults
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)
            config = ConfigLoader.load_config(str(empty_config))
            assert isinstance(config, ReorgConfig)
        finally:
            os.chdir(original_dir)


class TestValidateConfig:
    """Test configuration validation."""
    
    def test_validate_valid_config(self, temp_dir):
        """Test validating valid configuration."""
        config = ReorgConfig(
            project_root=str(temp_dir),
            backup_enabled=True,
        )
        
        result = ConfigLoader.validate_config(config)
        assert result is True
    
    def test_validate_missing_project_root(self):
        """Test validation with missing project root."""
        # ReorgConfig already validates in __post_init__, so we test that
        with pytest.raises(ValueError) as exc_info:
            config = ReorgConfig(
                project_root="",
                backup_enabled=True,
            )
        
        assert "project_root is required" in str(exc_info.value)
    
    def test_validate_nonexistent_project_root(self):
        """Test validation with nonexistent project root."""
        config = ReorgConfig(
            project_root="/nonexistent/path",
            backup_enabled=True,
        )
        
        with pytest.raises(ReorgError) as exc_info:
            ConfigLoader.validate_config(config)
        
        assert "does not exist" in str(exc_info.value)
    
    def test_validate_invalid_log_level(self, temp_dir):
        """Test validation with invalid log level."""
        config = ReorgConfig(
            project_root=str(temp_dir),
            log_level="INVALID",
        )
        
        with pytest.raises(ReorgError) as exc_info:
            ConfigLoader.validate_config(config)
        
        assert "invalid log_level" in str(exc_info.value)
    
    def test_validate_valid_log_levels(self, temp_dir):
        """Test validation with all valid log levels."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        for level in valid_levels:
            config = ReorgConfig(
                project_root=str(temp_dir),
                log_level=level,
            )
            assert ConfigLoader.validate_config(config) is True


class TestCreateDefaultConfig:
    """Test default configuration creation."""
    
    def test_create_default_config(self, temp_dir):
        """Test creating default configuration file."""
        output_path = temp_dir / "default_config.yaml"
        
        result_path = ConfigLoader.create_default_config(str(output_path))
        
        assert result_path == str(output_path)
        assert output_path.exists()
        
        # Verify content
        content = output_path.read_text()
        assert "reorganization:" in content
        assert "backup:" in content
        assert "symbolic_links:" in content
    
    def test_create_default_config_existing_file(self, temp_dir):
        """Test creating config when file already exists."""
        output_path = temp_dir / "existing.yaml"
        output_path.write_text("existing content")
        
        with pytest.raises(ReorgError) as exc_info:
            ConfigLoader.create_default_config(str(output_path))
        
        assert "already exists" in str(exc_info.value)
    
    def test_create_default_config_creates_directory(self, temp_dir):
        """Test that parent directories are created."""
        output_path = temp_dir / "subdir" / "config.yaml"
        
        ConfigLoader.create_default_config(str(output_path))
        
        assert output_path.exists()
        assert output_path.parent.exists()


class TestMergeConfigs:
    """Test configuration merging."""
    
    def test_merge_simple_configs(self):
        """Test merging simple configurations."""
        base = {'a': 1, 'b': 2}
        override = {'b': 3, 'c': 4}
        
        merged = ConfigLoader.merge_configs(base, override)
        
        assert merged['a'] == 1
        assert merged['b'] == 3  # Overridden
        assert merged['c'] == 4
    
    def test_merge_nested_configs(self):
        """Test merging nested configurations."""
        base = {
            'reorganization': {
                'backup': {'enabled': True, 'retention_days': 7},
                'dry_run': False,
            }
        }
        override = {
            'reorganization': {
                'backup': {'enabled': False},
                'dry_run': True,
            }
        }
        
        merged = ConfigLoader.merge_configs(base, override)
        
        assert merged['reorganization']['backup']['enabled'] is False
        assert merged['reorganization']['backup']['retention_days'] == 7
        assert merged['reorganization']['dry_run'] is True
    
    def test_merge_empty_override(self):
        """Test merging with empty override."""
        base = {'a': 1, 'b': 2}
        override = {}
        
        merged = ConfigLoader.merge_configs(base, override)
        
        assert merged == base
    
    def test_merge_empty_base(self):
        """Test merging with empty base."""
        base = {}
        override = {'a': 1, 'b': 2}
        
        merged = ConfigLoader.merge_configs(base, override)
        
        assert merged == override


class TestLoadConfigWithOverrides:
    """Test loading configuration with overrides."""
    
    def test_load_with_overrides(self, sample_config_file, temp_dir):
        """Test loading config with command-line overrides."""
        # Update config to use temp project root
        config_content = f"""
reorganization:
  project_root: "{temp_dir / 'project'}"
  dry_run: false
  backup:
    enabled: true
"""
        sample_config_file.write_text(config_content)
        
        overrides = {
            'reorganization': {
                'dry_run': True,
            }
        }
        
        config = ConfigLoader.load_config_with_overrides(
            str(sample_config_file),
            overrides
        )
        
        assert config.dry_run is True  # Overridden
        assert config.backup_enabled is True  # From file
    
    def test_load_with_no_overrides(self, sample_config_file, temp_dir):
        """Test loading config without overrides."""
        config_content = f"""
reorganization:
  project_root: "{temp_dir / 'project'}"
  dry_run: false
"""
        sample_config_file.write_text(config_content)
        
        config = ConfigLoader.load_config_with_overrides(str(sample_config_file))
        
        assert config.dry_run is False
    
    def test_load_defaults_with_overrides(self, temp_dir):
        """Test loading defaults with overrides."""
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            overrides = {
                'reorganization': {
                    'dry_run': True,
                }
            }
            
            config = ConfigLoader.load_config_with_overrides(None, overrides)
            
            assert config.dry_run is True
        finally:
            os.chdir(original_dir)


class TestGetConfigTemplate:
    """Test getting configuration template."""
    
    def test_get_config_template(self):
        """Test getting configuration template."""
        template = ConfigLoader.get_config_template()
        
        assert isinstance(template, str)
        assert "reorganization:" in template
        assert "backup:" in template
        assert "symbolic_links:" in template
        assert "logging:" in template
    
    def test_template_is_valid_yaml(self):
        """Test that template is valid YAML."""
        import yaml
        
        template = ConfigLoader.get_config_template()
        
        # Should not raise exception
        config_dict = yaml.safe_load(template)
        assert isinstance(config_dict, dict)
        assert 'reorganization' in config_dict


class TestConfigurationFields:
    """Test that all configuration fields are properly loaded."""
    
    def test_all_fields_loaded(self, temp_dir):
        """Test that all configuration fields are loaded correctly."""
        config_content = f"""
reorganization:
  project_root: "{temp_dir}"
  backup:
    enabled: false
    path: "/custom/backup"
    retention_days: 14
  symbolic_links:
    enabled: false
    use_relative_paths: false
  dry_run: true
  auto_confirm_deletes: true
  preserve_timestamps: false
  logging:
    level: "DEBUG"
"""
        config_path = temp_dir / "full_config.yaml"
        config_path.write_text(config_content)
        
        config = ConfigLoader.load_config(str(config_path))
        
        assert str(config.project_root) == str(temp_dir)
        assert config.backup_enabled is False
        assert config.backup_path == "/custom/backup"
        assert config.create_symbolic_links is False
        assert config.dry_run is True
        assert config.auto_confirm_deletes is True
        assert config.preserve_timestamps is False
        assert config.log_level == "DEBUG"
