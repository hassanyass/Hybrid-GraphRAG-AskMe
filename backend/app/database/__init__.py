"""
Database package.

Exposes the declarative Base, session factory, and dependency
for use throughout the application.
"""

from backend.app.database.base import Base
from backend.app.database.session import async_session_factory, get_db_session

__all__ = [
    "Base",
    "async_session_factory",
    "get_db_session",
]
