"""
Database base module.

Provides the declarative base class for all SQLAlchemy ORM models.
All models must inherit from Base to participate in migrations and
schema management.
"""

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(DeclarativeBase):
    """
    Declarative base for all ORM models.

    All database models inherit from this class. Alembic uses this
    base's metadata to auto-detect schema changes during migration
    generation.
    """

    pass
