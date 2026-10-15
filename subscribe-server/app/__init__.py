"""Email subscription API for legendPerceptor.github.io.

The site itself is a static Jekyll build, so all state lives in this small
service: a FastAPI app on top of a single SQLite file.
"""

__all__ = ["__version__"]

__version__ = "1.0.0"
