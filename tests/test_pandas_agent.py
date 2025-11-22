"""
Tests for the pandas_agent module (subsystem_2/pandas_agent.py)
Tests data querying, predictions, and SQL execution.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from core.subsystem_2.pandas_agent import (
    run_data_question,
    run_subscription_prediction,
    run_sql_query,
    _is_safe_sql_query,
    _extract_sql_from_message
)


class TestSQLSafety:
    """Test SQL query safety validation."""
    
    def test_safe_select_query(self):
        """Test that SELECT queries are considered safe."""
        assert _is_safe_sql_query("SELECT * FROM users") is True
    
    def test_safe_with_query(self):
        """Test that WITH queries are considered safe."""
        assert _is_safe_sql_query("WITH temp AS (SELECT * FROM users) SELECT * FROM temp") is True
    
    def test_unsafe_insert_query(self):
        """Test that INSERT queries are rejected."""
        assert _is_safe_sql_query("INSERT INTO users VALUES (1, 'test')") is False
    
    def test_unsafe_update_query(self):
        """Test that UPDATE queries are rejected."""
        assert _is_safe_sql_query("UPDATE users SET name = 'test'") is False
    
    def test_unsafe_delete_query(self):
        """Test that DELETE queries are rejected."""
        assert _is_safe_sql_query("DELETE FROM users WHERE id = 1") is False
    
    def test_unsafe_drop_query(self):
        """Test that DROP queries are rejected."""
        assert _is_safe_sql_query("DROP TABLE users") is False


class TestSQLExtraction:
    """Test SQL extraction from messages."""
    
    def test_extract_sql_from_code_block(self):
        """Test extracting SQL from code blocks."""
        sql = _extract_sql_from_message("```sql\nSELECT * FROM users\n```")
        assert sql == "SELECT * FROM users"
    
    def test_extract_sql_with_prefix(self):
        """Test extracting SQL with sql: prefix."""
        sql = _extract_sql_from_message("sql: SELECT * FROM users")
        assert sql == "SELECT * FROM users"
    
    def test_extract_plain_sql(self):
        """Test extracting plain SQL without markers."""
        sql = _extract_sql_from_message("SELECT * FROM users")
        assert sql == "SELECT * FROM users"
    
    def test_extract_none_for_invalid(self):
        """Test that invalid SQL returns None."""
        sql = _extract_sql_from_message("This is not SQL")
        assert sql is None


class TestDataQuestion:
    """Test data question handling."""
    
    @patch('core.subsystem_2.pandas_agent.query_with_pandasai')
    @patch('core.subsystem_2.pandas_agent.os.getenv')
    def test_data_question_with_pandasai(self, mock_getenv, mock_query):
        """Test data question with PandasAI available."""
        mock_getenv.return_value = "test-api-key"
        mock_query.return_value = "🤖 Powered by PandasAI v3 + LLM\n\n📊 Analysis Result:\nTest result"
        
        result = run_data_question("users", "how many users?")
        assert "PandasAI" in result
        mock_query.assert_called_once()
    
    @patch('core.subsystem_2.pandas_agent.query_with_pandasai')
    @patch('core.subsystem_2.pandas_agent.os.getenv')
    def test_data_question_no_api_key(self, mock_getenv, mock_query):
        """Test data question without API key."""
        mock_getenv.return_value = None
        
        result = run_data_question("users", "how many users?")
        assert "LLM API Key Required" in result
        mock_query.assert_not_called()


class TestPrediction:
    """Test subscription prediction."""
    
    @patch('core.subsystem_2.pandas_agent._get_historical_new_subscriptions')
    def test_prediction_insufficient_data(self, mock_get_data):
        """Test prediction with insufficient data."""
        mock_get_data.return_value = [(2024, 1, 10), (2024, 2, 15)]  # Only 2 months
        
        result = run_subscription_prediction("predict subscriptions")
        assert "Insufficient historical data" in result
    
    @patch('core.subsystem_2.pandas_agent._get_historical_new_subscriptions')
    @patch('core.subsystem_2.pandas_agent._calculate_linear_trend')
    @patch('core.subsystem_2.pandas_agent._predict_future_subscriptions')
    def test_prediction_success(self, mock_predict, mock_trend, mock_get_data):
        """Test successful prediction."""
        # Mock sufficient historical data
        mock_get_data.return_value = [
            (2023, 1, 100), (2023, 2, 110), (2023, 3, 120),
            (2023, 4, 130), (2023, 5, 140), (2023, 6, 150)
        ]
        mock_trend.return_value = (5.0, 95.0)  # slope, intercept
        mock_predict.return_value = [
            (2023, 7, 155), (2023, 8, 160), (2023, 9, 165)
        ]
        
        result = run_subscription_prediction("predict subscriptions")
        assert "Powered by PandasAI" in result
        assert "Prediction agent" in result


class TestSQLQuery:
    """Test SQL query execution."""
    
    @patch('core.subsystem_2.pandas_agent._get_connection')
    def test_sql_query_safe_execution(self, mock_conn):
        """Test safe SQL query execution."""
        # Mock database connection and cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = run_sql_query("SELECT * FROM users LIMIT 1")
        assert "Query Results" in result or "Powered by PandasAI" in result
    
    def test_sql_query_unsafe_rejected(self):
        """Test that unsafe SQL queries are rejected."""
        result = run_sql_query("DELETE FROM users")
        assert "Security Error" in result
    
    def test_sql_query_no_sql_found(self):
        """Test handling when no SQL is found."""
        result = run_sql_query("This is not SQL")
        assert "No SQL query found" in result

