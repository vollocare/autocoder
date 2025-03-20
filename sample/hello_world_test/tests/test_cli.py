import subprocess

def test_custom_name_greeting():
    """Test the command-line interface with a custom name."""
    result = subprocess.run(
        ["python", "-m", "hello_world.cli", "--name", "Bob"],
        capture_output=True,
        text=True
    )
    assert result.stdout.strip() == "Hello, Bob!"

def test_default_greeting():
    """Test the command-line interface with no name provided."""
    result = subprocess.run(
        ["python", "-m", "hello_world.cli"],
        capture_output=True,
        text=True
    )
    assert result.stdout.strip() == "Hello, World!"