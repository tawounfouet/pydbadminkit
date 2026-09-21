"""Immutable database catalog read models."""

from pydbadminkit.domain.catalog.column import ColumnInfo
from pydbadminkit.domain.catalog.database import DatabaseInfo
from pydbadminkit.domain.catalog.index import IndexDescription, IndexInfo
from pydbadminkit.domain.catalog.schema import SchemaInfo
from pydbadminkit.domain.catalog.server import ServerInfo
from pydbadminkit.domain.catalog.table import (
    ConstraintInfo,
    ConstraintType,
    TableDescription,
    TableInfo,
    TableKind,
)
from pydbadminkit.domain.catalog.view import ViewDescription, ViewInfo, ViewKind

__all__ = [
    "ColumnInfo",
    "ConstraintInfo",
    "ConstraintType",
    "DatabaseInfo",
    "IndexDescription",
    "IndexInfo",
    "SchemaInfo",
    "ServerInfo",
    "TableDescription",
    "TableInfo",
    "TableKind",
    "ViewDescription",
    "ViewInfo",
    "ViewKind",
]
