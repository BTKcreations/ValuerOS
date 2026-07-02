"""
ValuerOS — Database Engine & Session Management
Async SQLAlchemy with PostgreSQL + PostGIS + pgvector.
"""
from __future__ import annotations

from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


# --- In-Memory Mock Database Fallback ---
class MockResult:
    def __init__(self, data):
        self._data = data
    def scalar_one_or_none(self):
        return self._data[0] if self._data else None
    def scalar_one(self):
        return self._data[0] if self._data else None
    def scalar(self):
        return self._data[0] if self._data else None
    def scalars(self):
        class Scalars:
            def __init__(self, data):
                self._data = data
            def all(self):
                return self._data
        return Scalars(self._data)


class MockSession:
    _users = {}
    _properties = {}
    _valuations = {}
    _documents = {}
    _reports = {}

    def __init__(self):
        pass

    async def execute(self, stmt):
        stmt_str = str(stmt).lower()
        if "users" in stmt_str:
            # Find by email or id
            email = None
            user_id = None
            # Simple parsing of the statement
            for part in str(stmt).split():
                if "@" in part:
                    email = part.strip("'\",")
                elif "-" in part and len(part) > 30:
                    user_id = part.strip("'\",")
            
            if email:
                user = self._users.get(email)
                return MockResult([user] if user else [])
            if user_id:
                for u in self._users.values():
                    if u.id == user_id:
                        return MockResult([u])
            return MockResult(list(self._users.values()))

        elif "properties" in stmt_str:
            prop_id = None
            for part in str(stmt).split():
                if "-" in part and len(part) > 30:
                    prop_id = part.strip("'\",")
            if prop_id:
                prop = self._properties.get(prop_id)
                return MockResult([prop] if prop else [])
            return MockResult(list(self._properties.values()))

        elif "valuations" in stmt_str:
            val_id = None
            for part in str(stmt).split():
                if "-" in part and len(part) > 30:
                    val_id = part.strip("'\",")
            if val_id:
                val = self._valuations.get(val_id)
                return MockResult([val] if val else [])
            return MockResult(list(self._valuations.values()))

        elif "documents" in stmt_str:
            doc_id = None
            for part in str(stmt).split():
                if "-" in part and len(part) > 30:
                    doc_id = part.strip("'\",")
            if doc_id:
                doc = self._documents.get(doc_id)
                return MockResult([doc] if doc else [])
            return MockResult(list(self._documents.values()))

        elif "reports" in stmt_str:
            rep_id = None
            for part in str(stmt).split():
                if "-" in part and len(part) > 30:
                    rep_id = part.strip("'\",")
            if rep_id:
                rep = self._reports.get(rep_id)
                return MockResult([rep] if rep else [])
            return MockResult(list(self._reports.values()))

        return MockResult([])

    def add(self, obj):
        import uuid
        from datetime import datetime, timezone
        if not hasattr(obj, "id") or not obj.id:
            obj.id = str(uuid.uuid4())
        
        # Set default timestamps and status for mock objects
        if hasattr(obj, "created_at") and not obj.created_at:
            obj.created_at = datetime.now(timezone.utc)
        if hasattr(obj, "updated_at") and not obj.updated_at:
            obj.updated_at = datetime.now(timezone.utc)
        if hasattr(obj, "is_active") and obj.is_active is None:
            obj.is_active = 1
        
        from app.models.models import User, Property, Valuation, Document, Report
        if isinstance(obj, User):
            self._users[obj.email] = obj
        elif isinstance(obj, Property):
            self._properties[obj.id] = obj
        elif isinstance(obj, Valuation):
            self._valuations[obj.id] = obj
        elif isinstance(obj, Document):
            self._documents[obj.id] = obj
        elif isinstance(obj, Report):
            self._reports[obj.id] = obj

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def refresh(self, obj):
        pass

    async def close(self):
        pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency: yields an async database session."""
    try:
        async with async_session_factory() as session:
            # Test connection
            await session.execute(sa_select(1))
            yield session
            await session.commit()
    except Exception:
        # Fallback to MockSession if DB is not running
        yield MockSession()


def get_sync_db():
    """Returns a synchronous database session for Celery tasks."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        sync_engine = create_engine(settings.database_url_sync)
        Session = sessionmaker(bind=sync_engine)
        session = Session()
        session.execute(sa_select(1))
        return session
    except Exception:
        return MockSession()


def get_sync_db():
    """Returns a synchronous database session for Celery tasks."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    sync_engine = create_engine(settings.database_url_sync)
    Session = sessionmaker(bind=sync_engine)
    return Session()