"""
Storage exception classes.

Centralizes errors related to object storage operations.
"""


class StorageError(Exception):
    """Base exception for all storage-related errors."""
    pass


class StorageConnectionError(StorageError):
    """Raised when the storage backend cannot be reached."""
    pass


class FileUploadError(StorageError):
    """Raised when a file fails to upload to storage."""
    pass


class FileNotFoundError(StorageError):
    """Raised when a requested file does not exist in storage."""
    pass
