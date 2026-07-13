"""Basic tests for the LLM service."""
import os
import sys
from pathlib import Path

# Add src to path so we can import friday
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_llm_import():
    """Test that we can import the LLM service."""
    from friday.llm import LLMService, get_llm_callback
    service = LLMService()
    assert service is not None
    print("✓ LLMService imported successfully")

def test_callback():
    """Test that the callback function works."""
    from friday.llm import get_llm_callback
    callback = get_llm_callback()
    assert callable(callback)
    # Test with a simple input
    response = callback("Hello")
    assert isinstance(response, str)
    assert len(response) > 0
    print("✓ LLM callback works correctly")

def test_is_ready():
    """Test that is_ready returns a boolean."""
    from friday.llm import LLMService
    service = LLMService()
    ready = service.is_ready()
    assert isinstance(ready, bool)
    print(f"✓ is_ready() returns: {ready}")

if __name__ == "__main__":
    test_llm_import()
    test_callback()
    test_is_ready()
    print("All basic tests passed!")