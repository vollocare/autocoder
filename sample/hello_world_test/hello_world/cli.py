import argparse
import sys
from hello_world.greeting import get_greeting
from hello_world.config import DEFAULT_NAME

def main() -> None:
    """The main entry point for the Hello World CLI application."""
    parser = argparse.ArgumentParser(description="A simple Hello World command-line application.")
    parser.add_argument("--name", type=str, help="The name to greet")
    
    args = parser.parse_args()
    try:
        # Use the default name from config if none is provided
        name = args.name or DEFAULT_NAME
        greeting = get_greeting(name)
        print(greeting)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()