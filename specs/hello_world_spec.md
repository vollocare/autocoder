---
title: Hello World CLI
version: 0.1.0
author: Autocoder Team
---

# 功能描述

A simple Hello World command-line application that greets the user. The application should accept a name as a command-line argument and output a personalized greeting. If no name is provided, it should use a default greeting.

# 架構設計

The application will have a simple structure:
- Main module with command-line interface
- Greeting module with functions for generating greetings
- Configuration module for handling default settings
- Test module for unit tests

# 輸入/輸出規格

## Input
- Command-line argument: `--name` or `-n` followed by a string (optional)
- Command-line flag: `--version` or `-v` to display version information
- Command-line flag: `--help` or `-h` to display help information

## Output
- Standard output: Greeting message in the format "Hello, {name}!"
- If the `--version` flag is used, output the application version
- If the `--help` flag is used, output usage instructions

# 技術要求

- Programming language: Python 3.9+
- Command-line argument parsing: argparse
- Code style: PEP 8
- Documentation: Google-style docstrings
- Unit tests: pytest

# 測試案例

## Test Case 1: Default Greeting

```python
def test_default_greeting():
    from hello_world.greeting import get_greeting
    
    greeting = get_greeting()
    assert greeting == "Hello, World!"
```

## Test Case 2: Custom Name Greeting

```python
def test_custom_greeting():
    from hello_world.greeting import get_greeting
    
    greeting = get_greeting("Alice")
    assert greeting == "Hello, Alice!"
```

## Test Case 3: Command-line Interface

```python
import subprocess

def test_cli():
    # Test default greeting
    result = subprocess.run(["python", "-m", "hello_world"], capture_output=True, text=True)
    assert result.stdout.strip() == "Hello, World!"
    
    # Test custom name
    result = subprocess.run(["python", "-m", "hello_world", "--name", "Bob"], capture_output=True, text=True)
    assert result.stdout.strip() == "Hello, Bob!"
```

# 相依性

- pytest>=7.0.0
- argparse (standard library)

# 錯誤處理

- If an invalid argument is provided, display an appropriate error message and exit with a non-zero status code
- Handle potential Unicode issues in names gracefully

# 代碼生成提示規範

## API 設計

The main module should export the following functions:

```python
def main():
    """Entry point for the application."""
    pass

def parse_args():
    """Parse command-line arguments."""
    pass
```

The greeting module should export:

```python
def get_greeting(name=None):
    """Generate a greeting for the given name."""
    pass
```

## 目錄結構

```
hello_world/
├── __init__.py
├── __main__.py
├── greeting.py
├── config.py
└── tests/
    ├── __init__.py
    ├── test_greeting.py
    └── test_cli.py
``` 