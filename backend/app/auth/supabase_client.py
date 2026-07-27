"""
Supabase client initialisation.

Provides a lazily-initialised Supabase client for server-side
operations (e.g. admin user lookups). All credentials are loaded
from environment variables.
"""

import os
from functools import lru_cache

from supabase import Client, create_client


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Return a cached Supabase client instance.

    Raises:
        ValueError: If required environment variables are missing.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables "
            "must be set to initialise the Supabase client."
        )

    return create_client(url, key)
