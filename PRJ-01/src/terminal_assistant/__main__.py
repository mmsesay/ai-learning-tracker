"""Allow: `python -m terminal_assistant`

Entry point that forwards to the Typer app in main.py.
"""

from terminal_assistant.main import app

if __name__ == "__main__":
    app()
