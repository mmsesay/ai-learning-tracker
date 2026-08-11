"""Tiny demo app used on Render to exercise DevAssist tools."""

APP_NAME = "sample-app"


def greet(name: str) -> str:
    """Return a greeting (search_code can find this)."""
    return f"Hello, {name}! Welcome to {APP_NAME}."


if __name__ == "__main__":
    print(greet("Maej"))
