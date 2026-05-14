from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CHAR, MetaData
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.types import TypeDecorator


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, UUID):
            return value if dialect.name == "postgresql" else str(value)
        return str(UUID(str(value))) if dialect.name != "postgresql" else UUID(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return value if isinstance(value, UUID) else UUID(str(value))


class Base(DeclarativeBase):
    metadata = MetaData()

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
