"""
Tests for the router module (subsystem_1/router.py)
Tests message routing and intent classification.
"""

import pytest
from core.subsystem_1.router import route_message, Intent


class TestRouter:
    """Test cases for message routing."""
    
    def test_help_intent(self):
        """Test that help messages are correctly identified."""
        decision = route_message("help")
        assert decision.intent == "help"
    
    def test_small_talk_intent(self):
        """Test that small talk messages are correctly identified."""
        decision = route_message("hello")
        assert decision.intent == "small_talk"
    
    def test_data_question_users(self):
        """Test that user-related questions are routed correctly."""
        decision = route_message("how many users do we have?")
        assert decision.intent == "data_question"
        assert decision.dataset == "users"
    
    def test_data_question_payments(self):
        """Test that payment-related questions are routed correctly."""
        decision = route_message("what is our total revenue?")
        assert decision.intent == "data_question"
        assert decision.dataset == "payments"
    
    def test_data_question_subscriptions(self):
        """Test that subscription-related questions are routed correctly."""
        decision = route_message("show me subscription data")
        assert decision.intent == "data_question"
        assert decision.dataset == "subscriptions"
    
    def test_prediction_intent(self):
        """Test that prediction requests are correctly identified."""
        decision = route_message("predict subscriptions for next year")
        assert decision.intent == "prediction"
        assert decision.dataset == "subscriptions"
    
    def test_sql_query_intent(self):
        """Test that SQL queries are correctly identified."""
        decision = route_message("SELECT * FROM users LIMIT 10")
        assert decision.intent == "sql_query"
    
    def test_unknown_intent(self):
        """Test that unrecognized messages default to unknown."""
        decision = route_message("random gibberish xyz123")
        assert decision.intent == "unknown"

