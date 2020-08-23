"""Pytest-codegen command line tool."""
from pytest_codegen.main import app


def entry() -> None:
    """Entrypoint of the cli."""
    app()


if __name__ == "__main__":
    app()
