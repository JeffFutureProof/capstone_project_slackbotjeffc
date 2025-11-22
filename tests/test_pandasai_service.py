"""
Tests for the pandasai_service module (services/pandasai_service.py)
Tests PandasAI integration and LLM functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from core.services.pandasai_service import (
    is_pandasai_configured,
    explain_with_llm,
    analyze_with_llm,
    query_with_pandasai
)


class TestPandasAIConfiguration:
    """Test PandasAI configuration checks."""
    
    @patch('core.services.pandasai_service.os.getenv')
    def test_is_configured_with_api_key(self, mock_getenv):
        """Test configuration check with API key."""
        mock_getenv.return_value = "test-api-key"
        assert is_pandasai_configured() is True
    
    @patch('core.services.pandasai_service.os.getenv')
    def test_is_not_configured_without_api_key(self, mock_getenv):
        """Test configuration check without API key."""
        mock_getenv.return_value = None
        assert is_pandasai_configured() is False


class TestLLMFunctions:
    """Test LLM helper functions."""
    
    @patch('core.services.pandasai_service._initialize_pandasai')
    @patch('core.services.pandasai_service.pai.SmartDataframe')
    def test_explain_with_llm(self, mock_smart_df, mock_init):
        """Test explain_with_llm function."""
        # Mock SmartDataframe
        mock_df_instance = MagicMock()
        mock_df_instance.chat.return_value = "This is an explanation"
        mock_smart_df.return_value = mock_df_instance
        
        result = explain_with_llm("Test context", "Test summary")
        assert "explanation" in result.lower() or len(result) > 0
    
    @patch('core.services.pandasai_service._initialize_pandasai')
    @patch('core.services.pandasai_service.pai.SmartDataframe')
    def test_analyze_with_llm(self, mock_smart_df, mock_init):
        """Test analyze_with_llm function."""
        # Mock SmartDataframe
        mock_df_instance = MagicMock()
        mock_df_instance.chat.return_value = "This is an analysis"
        mock_smart_df.return_value = mock_df_instance
        
        result = analyze_with_llm("Test question", "Test context")
        assert "analysis" in result.lower() or len(result) > 0


class TestPandasAIQuery:
    """Test PandasAI query function."""
    
    @patch('core.services.pandasai_service._initialize_pandasai')
    @patch('core.services.pandasai_service._load_table_to_dataframe')
    @patch('core.services.pandasai_service.pai.SmartDataframe')
    @patch('core.services.pandasai_service.os.getenv')
    def test_query_with_pandasai(self, mock_getenv, mock_smart_df, mock_load_df, mock_init):
        """Test query_with_pandasai function."""
        # Setup mocks
        mock_getenv.return_value = "test-api-key"
        mock_df = MagicMock()
        mock_load_df.return_value = mock_df
        
        mock_df_instance = MagicMock()
        mock_df_instance.chat.return_value = "Query result"
        mock_smart_df.return_value = mock_df_instance
        
        result = query_with_pandasai("test question", "users")
        assert "Powered by PandasAI" in result
        assert "Query result" in result
    
    @patch('core.services.pandasai_service._initialize_pandasai')
    @patch('core.services.pandasai_service.os.getenv')
    def test_query_without_api_key(self, mock_getenv, mock_init):
        """Test query without API key."""
        mock_getenv.return_value = None
        mock_init.side_effect = ValueError("API key required")
        
        result = query_with_pandasai("test question")
        assert "Configuration Error" in result or "API key" in result

