# Autocoder CLI Help

This document provides the help output you would see when running `autocoder --help`.

```
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
                 Shows detailed information including:
                 - Environment details (Python version, OS)
                 - Configuration settings
                 - Command execution with real-time output
                 - Execution time statistics
                 - Command history
  -q, --quiet    Minimize output
  --no-color     Disable colored output
  --help         Show this message and exit.
```

## Generate Command

```
Usage: autocoder generate [OPTIONS] SPEC_PATH

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
  --help                 Show this message and exit.
```

## Refactor Command

```
Usage: autocoder refactor [OPTIONS] CODE_PATH

  Refactor existing code to improve structure and performance.

Arguments:
  CODE_PATH  [required]

Options:
  -t, --target TEXT      Specific file or directory to refactor
  -o, --output-dir TEXT  Output directory for refactored code (will be created
                         if it doesn't exist)
  --help                 Show this message and exit.
```

## Test Command

```
Usage: autocoder test [OPTIONS] CODE_PATH

  Generate and run tests for existing code.

Arguments:
  CODE_PATH  [required]

Options:
  -o, --output-dir TEXT  Output directory for generated tests (will be created
                         if it doesn't exist)
  --help                 Show this message and exit.
```

## Understand Command

```
Usage: autocoder understand [OPTIONS] CODE_PATH

  Analyze existing code and generate documentation.

Arguments:
  CODE_PATH  [required]

Options:
  -o, --output-file TEXT  Output file for documentation
  --help                  Show this message and exit.
```

## Interactive Command

```
Usage: autocoder interactive [OPTIONS]

  Start interactive development mode.

Options:
  --help  Show this message and exit.
```

## Config Command

```
Usage: autocoder config [OPTIONS]

  Configure model settings.

Options:
  --model TEXT   Path to model or model identifier
  --api TEXT     API endpoint URL
  --list         List current configuration
  --global       Apply to global configuration
  --help         Show this message and exit.
```

## Verbose Mode (-v, --verbose)

When you run any command with the `-v` or `--verbose` flag, you'll see detailed information about the process:

```
[DEBUG] Python version: 3.9.10
[DEBUG] Operating system: darwin
[DEBUG] Working directory: /Users/username/projects/autocoder
[DEBUG] API endpoint: http://localhost:11434/v1
[DEBUG] Temperature: 0.6
[DEBUG] Top P: 0.9
[DEBUG] Max tokens: 8192
[DEBUG] Quantization: none
[DEBUG] Max iterations: 50
[DEBUG] Executing command: python /tmp/tempscript12345.py
[SUCCESS] Command completed successfully in 1.24s
[DEBUG] Executing command: python -m pytest test_file.py -v
... (detailed test output) ...
[SUCCESS] Command completed successfully in 3.45s
[SUCCESS] Code generated successfully in 25.67s
[INFO] Command execution history:
[✓] 1. python /tmp/tempscript12345.py (1.24s)
[✓] 2. python -m pytest test_file.py -v (3.45s)
``` 