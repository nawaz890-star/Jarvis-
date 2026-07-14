"""Tests for AI engine."""

import pytest
from core.ai_engine import AIEngine


def test_ai_engine_initialization():
    """Test AI engine initializes."""
    engine = AIEngine()
    assert engine is not None
    assert len(engine.conversation_history) > 0


def test_ai_engine_ask():
    """Test AI engine ask method."""
    engine = AIEngine()
    response = engine.ask("Hello")
    assert isinstance(response, str)
    assert len(response) > 0


def test_ai_engine_history():
    """Test AI engine maintains history."""
    engine = AIEngine()
    initial_len = len(engine.conversation_history)
    engine.ask("Hello")
    assert len(engine.conversation_history) > initial_len
