"""
A simple script to display the CLI help text.
"""

import os
import sys
import click

# Add description about output directories being created
help_text = """
Autocoder: AI-powered automatic code generation tool.

Generate, test, and validate code automatically using AI models.
All output directories specified with --output-dir will be created if they don't exist.

Commands:
  config     Configure model settings.
  generate   Generate code from a specification file.
  interactive Start interactive development mode.
  refactor   Refactor existing code to improve structure and...
  test       Generate and run tests for existing code.
  understand Analyze existing code and generate documentation.

Options:
  --version      Show the version and exit.
  -v, --verbose  Enable verbose output
  -q, --quiet    Minimize output
  --no-color     Disable colored output
  --help         Show this message and exit.

Generate command:
  Generate code from a specification file.

  Arguments:
    SPEC_PATH  [required]

  Options:
    -o, --output-dir TEXT  Output directory for generated code (will be created
                          if it doesn't exist)
    --api-endpoint TEXT    API endpoint for the model
    --temperature FLOAT    Model temperature (0.0-1.0)
    --max-iterations INTEGER
                          Maximum number of generation/test iterations
    --help                Show this message and exit.

Refactor command:
  Refactor existing code to improve structure and performance.

  Arguments:
    CODE_PATH  [required]

  Options:
    -t, --target TEXT      Specific file or directory to refactor
    -o, --output-dir TEXT  Output directory for refactored code (will be created
                          if it doesn't exist)
    --help                Show this message and exit.

Test command:
  Generate and run tests for existing code.

  Arguments:
    CODE_PATH  [required]

  Options:
    -o, --output-dir TEXT  Output directory for generated tests (will be created
                          if it doesn't exist)
    --help                Show this message and exit.
"""

print(help_text) 