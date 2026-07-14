"""Tests for memory manager."""

import pytest
from core.memory import MemoryManager


def test_memory_manager_initialization():
    """Test memory manager initializes."""
    memory = MemoryManager()
    assert memory is not None


def test_memory_save_conversation():
    """Test saving conversations."""
    memory = MemoryManager()
    result = memory.save_conversation("Hello", "Hi there")
    assert result is True


def test_memory_retrieve_history():
    """Test retrieving conversation history."""
    memory = MemoryManager()
    memory.save_conversation("Test", "Response")
    history = memory.get_conversation_history()
    assert isinstance(history, list)
