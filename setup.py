"""Editable install for the intent-drift skill."""

from setuptools import find_packages, setup

setup(
    name="claude-skill-intent-drift",
    version="1.0.0",
    description="Intent drift analyzer skill for Claude Code agents",
    packages=find_packages(exclude=("tests", "tests.*")),
    py_modules=["analyzer", "config", "history"],
    python_requires=">=3.10",
    install_requires=[
        "intent-drift>=0.1.0",
        "PyYAML>=6.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "intent-drift=analyzer:main",
        ],
    },
)
