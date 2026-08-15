"""Editable install for the intent-drift skill.

All package metadata lives in pyproject.toml; this shim exists so legacy
`pip install -e .` / `python setup.py` invocations keep working.
"""

from setuptools import setup

if __name__ == "__main__":
    setup()
