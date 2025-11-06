"""
Custom exceptions for the file reorganization system.
"""


class ReorgError(Exception):
    """Base exception for all reorganization errors."""
    pass


class FileOperationError(ReorgError):
    """Exception raised when file operations (move, copy, delete) fail."""
    pass


class DependencyError(ReorgError):
    """Exception raised when dependency analysis or resolution fails."""
    pass


class ValidationError(ReorgError):
    """Exception raised when validation checks fail."""
    pass


class RollbackError(ReorgError):
    """Exception raised when rollback operations fail."""
    pass
