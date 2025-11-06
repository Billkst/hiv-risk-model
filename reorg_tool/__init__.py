"""
HIV Risk Model - File Reorganization Tool

A safe, incremental file reorganization system that uses symbolic links
to maintain backward compatibility while restructuring the project.
"""

__version__ = "1.0.0"
__author__ = "HIV Risk Model Team"

from .models import (
    FileInfo,
    FileCategory,
    ReorgConfig,
    ReorgResult,
    FileMapping,
    TransactionEntry,
)

from .exceptions import (
    ReorgError,
    FileOperationError,
    DependencyError,
    ValidationError,
    RollbackError,
)

__all__ = [
    "FileInfo",
    "FileCategory",
    "ReorgConfig",
    "ReorgResult",
    "FileMapping",
    "TransactionEntry",
    "ReorgError",
    "FileOperationError",
    "DependencyError",
    "ValidationError",
    "RollbackError",
]
