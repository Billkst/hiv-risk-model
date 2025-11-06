"""
Configuration loader for the reorganization system.

Loads and validates YAML configuration files.
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any

from .models import ReorgConfig
from .exceptions import ReorgError


# Default configuration template
DEFAULT_CONFIG = """
# File Reorganization Configuration

reorganization:
  # Project root directory (required)
  project_root: "."
  
  # Backup settings
  backup:
    enabled: true
    path: null  # Auto-generated if null
    retention_days: 7
  
  # Symbolic link settings
  symbolic_links:
    enabled: true
    use_relative_paths: true
  
  # Dry run mode (no actual changes)
  dry_run: false
  
  # Auto-confirm file deletions
  auto_confirm_deletes: false
  
  # Preserve file timestamps
  preserve_timestamps: true
  
  # Logging settings
  logging:
    level: "INFO"  # DEBUG, INFO, WARNING, ERROR
    console: true
    file: true
    file_path: ".reorg_log_{timestamp}.log"
"""


class ConfigLoader:
    """Loads and validates reorganization configuration."""
    
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> ReorgConfig:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file (YAML)
        
        Returns:
            ReorgConfig object
        """
        if config_path:
            config_dict = ConfigLoader._load_yaml(config_path)
        else:
            config_dict = ConfigLoader._get_default_config()
        
        # Extract reorganization settings
        reorg_settings = config_dict.get('reorganization', {})
        
        # Create ReorgConfig
        config = ReorgConfig(
            project_root=reorg_settings.get('project_root', '.'),
            backup_enabled=reorg_settings.get('backup', {}).get('enabled', True),
            dry_run=reorg_settings.get('dry_run', False),
            auto_confirm_deletes=reorg_settings.get('auto_confirm_deletes', False),
            preserve_timestamps=reorg_settings.get('preserve_timestamps', True),
            create_symbolic_links=reorg_settings.get('symbolic_links', {}).get('enabled', True),
            backup_path=reorg_settings.get('backup', {}).get('path'),
            log_level=reorg_settings.get('logging', {}).get('level', 'INFO'),
        )
        
        # Validate configuration
        ConfigLoader.validate_config(config)
        
        return config
    
    @staticmethod
    def _load_yaml(config_path: str) -> Dict[str, Any]:
        """
        Load YAML configuration file.
        
        Args:
            config_path: Path to YAML file
        
        Returns:
            Dictionary with configuration
        """
        path = Path(config_path)
        
        if not path.exists():
            raise ReorgError(f"Configuration file not found: {config_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            
            if config_dict is None:
                config_dict = {}
            
            return config_dict
        
        except yaml.YAMLError as e:
            raise ReorgError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ReorgError(f"Failed to load configuration: {e}")
    
    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """
        Get default configuration.
        
        Returns:
            Dictionary with default configuration
        """
        try:
            return yaml.safe_load(DEFAULT_CONFIG)
        except yaml.YAMLError as e:
            raise ReorgError(f"Failed to parse default configuration: {e}")
    
    @staticmethod
    def validate_config(config: ReorgConfig) -> bool:
        """
        Validate configuration.
        
        Args:
            config: ReorgConfig to validate
        
        Returns:
            True if valid
        
        Raises:
            ReorgError: If configuration is invalid
        """
        # Check required fields
        if not config.project_root:
            raise ReorgError("Configuration error: project_root is required")
        
        # Check project root exists
        project_path = Path(config.project_root)
        if not project_path.exists():
            raise ReorgError(f"Configuration error: project_root does not exist: {config.project_root}")
        
        # Check log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config.log_level.upper() not in valid_log_levels:
            raise ReorgError(f"Configuration error: invalid log_level: {config.log_level}")
        
        return True
    
    @staticmethod
    def create_default_config(output_path: str) -> str:
        """
        Create a default configuration file.
        
        Args:
            output_path: Path where to save the configuration file
        
        Returns:
            Path to created configuration file
        """
        path = Path(output_path)
        
        # Check if file already exists
        if path.exists():
            raise ReorgError(f"Configuration file already exists: {output_path}")
        
        # Create parent directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write default configuration
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(DEFAULT_CONFIG)
            
            return str(path)
        
        except Exception as e:
            raise ReorgError(f"Failed to create configuration file: {e}")
    
    @staticmethod
    def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries.
        
        Override values take precedence over base values.
        
        Args:
            base_config: Base configuration
            override_config: Override configuration
        
        Returns:
            Merged configuration dictionary
        """
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                merged[key] = ConfigLoader.merge_configs(merged[key], value)
            else:
                # Override value
                merged[key] = value
        
        return merged
    
    @staticmethod
    def load_config_with_overrides(
        config_path: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None
    ) -> ReorgConfig:
        """
        Load configuration with command-line overrides.
        
        Priority: overrides > config_file > defaults
        
        Args:
            config_path: Path to configuration file
            overrides: Dictionary with override values
        
        Returns:
            ReorgConfig object
        """
        # Load base configuration
        if config_path:
            base_dict = ConfigLoader._load_yaml(config_path)
        else:
            base_dict = ConfigLoader._get_default_config()
        
        # Apply overrides
        if overrides:
            config_dict = ConfigLoader.merge_configs(base_dict, overrides)
        else:
            config_dict = base_dict
        
        # Extract reorganization settings
        reorg_settings = config_dict.get('reorganization', {})
        
        # Create ReorgConfig
        config = ReorgConfig(
            project_root=reorg_settings.get('project_root', '.'),
            backup_enabled=reorg_settings.get('backup', {}).get('enabled', True),
            dry_run=reorg_settings.get('dry_run', False),
            auto_confirm_deletes=reorg_settings.get('auto_confirm_deletes', False),
            preserve_timestamps=reorg_settings.get('preserve_timestamps', True),
            create_symbolic_links=reorg_settings.get('symbolic_links', {}).get('enabled', True),
            backup_path=reorg_settings.get('backup', {}).get('path'),
            log_level=reorg_settings.get('logging', {}).get('level', 'INFO'),
        )
        
        # Validate configuration
        ConfigLoader.validate_config(config)
        
        return config
    
    @staticmethod
    def get_config_template() -> str:
        """
        Get the default configuration template as string.
        
        Returns:
            Configuration template string
        """
        return DEFAULT_CONFIG
