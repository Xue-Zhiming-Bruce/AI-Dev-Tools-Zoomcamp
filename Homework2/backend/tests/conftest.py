"""Shared test fixture (issue #13).

Every test gets a fresh in-memory SQLite engine swapped into the store module,
so the module-level function API is exercised exactly as the route handlers
use it.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app import store


@pytest.fixture(autouse=True)
def memory_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    store.set_engine(engine)
    store.reset()  # fresh schema + default board per test
    yield
    engine.dispose()
