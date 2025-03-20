import pytest
from hello_world.greeting import get_greeting

def test_default_greeting():
    """Test the default greeting."""
    assert get_greeting() == "Hello, World!"

def test_custom_name_greeting():
    """Test the greeting with a custom name."""
    assert get_greeting("Alice") == "Hello, Alice!"

def test_unicode_name():
    """Test the greeting with a name containing Unicode characters."""
    assert get_greeting("José") == "Hello, José!"

def test_invalid_name():
    """Test the greeting with invalid characters."""
    with pytest.raises(ValueError):
        get_greeting("\x80")