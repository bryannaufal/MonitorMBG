"""Test-wide defaults.

The API suites drive real review/fusion flows against the shared ``seed_data``
collections.  With write-through persistence enabled those mutations would land
in the developer's database and accumulate across runs, so persistence is off by
default and the tests keep their original in-memory semantics.

``tests/test_persistence.py`` opts back in via the ``persistent_db`` fixture,
which is the only place that is supposed to touch the database.
"""

from __future__ import annotations

import pytest

from app import persistence


@pytest.fixture(autouse=True)
def _no_persistence(monkeypatch):
    """Keep API tests from writing into the dev database."""
    monkeypatch.setattr(persistence, "_enabled", False)


@pytest.fixture
def persistent_db(monkeypatch):
    """Enable write-through and hydrate; skip if no seeded database is present."""
    monkeypatch.setattr(persistence, "_enabled", True)
    if not persistence.hydrate():
        pytest.skip("database unavailable or not seeded")
    yield persistence
