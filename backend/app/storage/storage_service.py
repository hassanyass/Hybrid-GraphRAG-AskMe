"""
Storage service.

Abstracts the MinIO implementation details and provides high-level
operations for uploading, retrieving, and deleting files.
"""

import io
import os
import uuid
from datetime import timedelta
from typing import BinaryIO

from minio.error import S3Error
from urllib3.exceptions import MaxRetryError

from backend.app.storage.exceptions import (
    FileNotFoundError,
    FileUploadError,
    StorageConnectionError,
    StorageError,
)
from backend.app.storage.minio_client import get_minio_client

# Environment variable for the main document bucket
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "documents")


class StorageService:
    """Service for interacting with MinIO Object Storage."""

    def __init__(self) -> None:
        try:
            self._client = get_minio_client()
            self._ensure_bucket_exists()
        except MaxRetryError:
            raise StorageConnectionError("Could not connect to MinIO.")
        except Exception as e:
            if not isinstance(e, StorageConnectionError):
                raise StorageError(f"Failed to initialize StorageService: {e}")

    def _ensure_bucket_exists(self) -> None:
        """Ensure the default application bucket exists."""
        try:
            if not self._client.bucket_exists(MINIO_BUCKET_NAME):
                self._client.make_bucket(MINIO_BUCKET_NAME)
        except S3Error as e:
            raise StorageConnectionError(f"MinIO bucket error: {e}")
        except Exception as e:
            raise StorageConnectionError(f"MinIO connection failed: {e}")

    def upload_file(
        self,
        user_id: uuid.UUID,
        file_stream: BinaryIO,
        filename: str,
        content_type: str,
        file_size: int,
    ) -> str:
        """
        Upload a file to MinIO.

        Uses the pattern: {user_id}/{uuid}_{filename} for secure isolation.

        Args:
            user_id: The ID of the uploading user.
            file_stream: The binary stream of the file.
            filename: The original filename.
            content_type: The MIME type of the file.
            file_size: The size of the file in bytes.

        Returns:
            str: The storage path (object key) in MinIO.

        Raises:
            FileUploadError: If the upload fails.
        """
        # Generate a unique secure object key
        unique_id = str(uuid.uuid4())
        # Replace spaces or risky characters in filename (simplified here)
        safe_filename = filename.replace(" ", "_")
        object_key = f"{user_id}/{unique_id}_{safe_filename}"

        try:
            # MinIO requires stream to be at position 0
            file_stream.seek(0)
            self._client.put_object(
                bucket_name=MINIO_BUCKET_NAME,
                object_name=object_key,
                data=file_stream,
                length=file_size,
                content_type=content_type,
            )
            return object_key
        except S3Error as e:
            raise FileUploadError(f"Failed to upload file to MinIO: {e}")
        except Exception as e:
            raise FileUploadError(f"Unexpected error during upload: {e}")

    def delete_file(self, object_key: str) -> None:
        """
        Delete a file from MinIO by its object key.

        Args:
            object_key: The storage path of the file.
        """
        try:
            self._client.remove_object(MINIO_BUCKET_NAME, object_key)
        except S3Error:
            pass  # If it fails to delete, we swallow it or log it (logging omitted here)
        except Exception as e:
            raise StorageError(f"Error deleting file: {e}")

    def get_file_url(self, object_key: str, expires: int = 3600) -> str:
        """
        Generate a presigned URL to securely download a file.

        Args:
            object_key: The storage path of the file.
            expires: Link expiration time in seconds (default 1 hour).

        Returns:
            str: The presigned URL.
        """
        try:
            return self._client.get_presigned_url(
                "GET",
                MINIO_BUCKET_NAME,
                object_key,
                expires=timedelta(seconds=expires),
            )
        except S3Error as e:
            raise StorageError(f"Failed to generate URL: {e}")

    def check_file_exists(self, object_key: str) -> bool:
        """Check if a file exists in storage."""
        try:
            self._client.stat_object(MINIO_BUCKET_NAME, object_key)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise StorageError(f"Error checking file existence: {e}")
