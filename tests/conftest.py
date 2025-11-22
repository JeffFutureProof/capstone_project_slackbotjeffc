"""
Pytest configuration and shared fixtures.
This file is automatically loaded by pytest.
"""

import pytest
import os
from unittest.mock import Mock, patch


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to set up mock environment variables."""
    monkeypatch.setenv("DB_HOST", "test-host")
    monkeypatch.setenv("DB_USER", "test-user")
    monkeypatch.setenv("DB_PASS", "test-pass")
    monkeypatch.setenv("DB_NAME", "test-db")
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    return monkeypatch


@pytest.fixture
def mock_database_connection():
    """Fixture to mock database connections."""
    with patch('core.subsystem_2.pandas_agent._get_connection') as mock_conn:
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        
        yield mock_conn


@pytest.fixture
def sample_subscription_data():
    """Fixture providing sample subscription data."""
    return [
        (2023, 1, 100),
        (2023, 2, 110),
        (2023, 3, 120),
        (2023, 4, 130),
        (2023, 5, 140),
        (2023, 6, 150),
    ]

