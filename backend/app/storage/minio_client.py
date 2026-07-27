"""
MinIO client initialization.

Provides a configured MinIO client instance using environment variables.
"""

import os
from functools import lru_cache

from minio import Minio


@lru_cache(maxsize=1)
def get_minio_client() -> Minio:
    """
    Return a cached Minio client instance.

    Raises:
        ValueError: If required environment variables are missing.
    """
    endpoint = os.getenv("MINIO_ENDPOINT")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

    if not endpoint or not access_key or not secret_key:
        raise ValueError(
            "MINIO_ENDPOINT, MINIO_ACCESS_KEY, and MINIO_SECRET_KEY "
            "must be set to initialize the MinIO client."
        )

    return Minio(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )
