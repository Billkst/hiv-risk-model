"""
Core data models for the file reorganization system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime
from pathlib import Path


class FileCategory(Enum):
    """File classification categories."""
    CORE_API = "core_api"
    CORE_MODEL = "core_model"
    CORE_DATA = "core_data"
    CONFIG = "config"
    DOC_USER = "doc_user"
    DOC_DEPLOYMENT = "doc_deployment"
    DOC_TECHNICAL = "doc_technical"
    DOC_PROJECT = "doc_project"
    DEV_TEST = "dev_test"
    DEV_SCRIPT = "dev_script"
    DEV_UTIL = "dev_util"
    DEV_TEMP = "dev_temp"
    DUPLICATE = "duplicate"
    OBSOLETE = "obsolete"
    UNKNOWN = "unknown"


class ReorgPhase(Enum):
    """Reorganization execution phases."""
    SCAN = "scan"
    CLASSIFY = "classify"
    ANALYZE = "analyze"
    BACKUP = "backup"
    CREATE_STRUCTURE = "structure"
    MOVE_CORE = "move_core"
    MOVE_DOCS = "move_docs"
    MOVE_DEV = "move_dev"
    CREATE_LINKS = "create_links"
    VALIDATE = "validate"
    CLEANUP = "cleanup"
    REPORT = "report"


@dataclass
class FileInfo:
    """Information about a file in the project."""
    path: str
    name: str
    size: int
    extension: str
    modified_time: datetime
    has_non_ascii_name: bool = False
    is_executable: bool = False
    
    @property
    def relative_path(self) -> str:
        """Get the relative path from project root."""
        return self.path
    
    def __str__(self) -> str:
        return f"FileInfo({self.path}, {self.size} bytes)"


@dataclass

class ReorgConfig:
    """Configuration for reorganization process."""
    project_root: str
    backup_enabled: bool = True
    dry_run: bool = False
    auto_confirm_deletes: bool = False
    preserve_timestamps: bool = True
    create_symbolic_links: bool = True
    backup_path: Optional[str] = None
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.project_root:
            raise ValueError("project_root is required")
        
        # Convert to absolute path
        self.project_root = str(Path(self.project_root).resolve())
        
        # Set default backup path if not provided
        if self.backup_enabled and not self.backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_path = f"{self.project_root}_backup_{timestamp}"


@dataclass
class ReorgResult:
    """Result of reorganization process."""
    success: bool
    start_time: datetime
    end_time: datetime
    phases_completed: List[ReorgPhase] = field(default_factory=list)
    files_moved: int = 0
    links_created: int = 0
    files_deleted: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    backup_path: Optional[str] = None
    transaction_log_path: str = ""
    
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
    
    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"ReorgResult({status}, "
            f"{self.files_moved} moved, "
            f"{self.links_created} links, "
            f"{self.files_deleted} deleted, "
            f"{len(self.errors)} errors)"
        )


@dataclass
class FileMapping:
    """Mapping of file from old path to new path."""
    old_path: str
    new_path: str
    category: FileCategory
    requires_link: bool = True
    link_path: Optional[str] = None
    
    def __post_init__(self):
        """Set link path if not provided."""
        if self.requires_link and not self.link_path:
            self.link_path = self.old_path


@dataclass
class TransactionEntry:
    """Entry in the transaction log."""
    timestamp: datetime
    operation: str  # 'move', 'link', 'delete'
    source: str
    destination: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    checksum_before: Optional[str] = None
    checksum_after: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "source": self.source,
            "destination": self.destination,
            "success": self.success,
            "error_message": self.error_message,
            "checksum_before": self.checksum_before,
            "checksum_after": self.checksum_after,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TransactionEntry':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ImportDependency:
    """Python import dependency."""
    source_file: str
    import_statement: str
    imported_module: str
    line_number: int
    is_relative: bool = False


@dataclass
class PathDependency:
    """File path dependency in code."""
    source_file: str
    referenced_path: str
    line_number: int
    context: str = ""


@dataclass
class DependencyGraph:
    """Graph of file dependencies."""
    nodes: Dict[str, FileInfo] = field(default_factory=dict)
    import_edges: List[ImportDependency] = field(default_factory=list)
    path_edges: List[PathDependency] = field(default_factory=list)
    critical_paths: List[List[str]] = field(default_factory=list)
    
    def add_node(self, file_info: FileInfo):
        """Add a file node to the graph."""
        self.nodes[file_info.path] = file_info
    
    def add_import_edge(self, dependency: ImportDependency):
        """Add an import dependency edge."""
        self.import_edges.append(dependency)
    
    def add_path_edge(self, dependency: PathDependency):
        """Add a path dependency edge."""
        self.path_edges.append(dependency)
    
    def get_dependencies(self, file_path: str) -> List[str]:
        """Get all files that depend on the given file."""
        dependencies = []
        
        # Check import dependencies
        for edge in self.import_edges:
            if edge.imported_module in file_path:
                dependencies.append(edge.source_file)
        
        # Check path dependencies
        for edge in self.path_edges:
            if edge.referenced_path in file_path:
                dependencies.append(edge.source_file)
        
        return list(set(dependencies))


@dataclass
class ValidationChecks:
    """Results of validation checks."""
    all_links_valid: bool = True
    broken_links: List[str] = field(default_factory=list)
    import_tests_passed: bool = True
    failed_imports: List[str] = field(default_factory=list)
    api_startable: bool = False
    model_loadable: bool = False
    predictions_working: bool = False
    no_missing_files: bool = True
    missing_files: List[str] = field(default_factory=list)
    
    @property
    def all_passed(self) -> bool:
        """Check if all validations passed."""
        return (
            self.all_links_valid and
            self.import_tests_passed and
            self.no_missing_files
        )
