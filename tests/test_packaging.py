"""Packaging consistency tests (issue #12).

These guard the parts of #12 that were still broken after the earlier merged
fixes (console script + engine rename): the unused ``click``/``python-dateutil``
dependencies, the machine-local engine path in ``analyzer.py``/``__init__.py``,
and the package metadata living in ``setup.py`` with no ``[project]`` section in
``pyproject.toml``.
"""

import re
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

SKILL_DIR = Path(__file__).resolve().parent.parent


def _pyproject() -> dict:
    text = (SKILL_DIR / "pyproject.toml").read_text(encoding="utf-8")
    if tomllib is not None:
        return tomllib.loads(text)
    # Python 3.10 has no tomllib; parse just the [project] fields the tests
    # assert on. The full structure is covered on 3.11+ CI runners.
    return _pyproject_fallback(text)


def _pyproject_fallback(text: str) -> dict:
    _m = re.MULTILINE
    project = re.search(r"^\[project\]\n(.*?)(?=\n\[)", text, re.S | _m).group(1)
    scripts = re.search(r"^\[project\.scripts\]\n(.*?)(?=\n\[)", text, re.S | _m).group(1)
    return {
        "project": {
            "name": re.search(r'^name = "([^"]+)"', project, _m).group(1),
            "version": re.search(r'^version = "([^"]+)"', project, _m).group(1),
            "dependencies": re.findall(r'^    "([^"]+)"', project, _m),
            "scripts": dict(re.findall(r'^(\S+) = "([^"]+)"', scripts, _m)),
        }
    }


def test_project_metadata_lives_in_pyproject_toml():
    project = _pyproject()["project"]
    assert project["name"] == "intent-drift"
    assert project["version"] == "1.0.0"
    assert any("intent-drift" in d for d in project["dependencies"])
    assert any("PyYAML" in d for d in project["dependencies"])


def test_pyproject_version_matches_metadata_json():
    import json

    meta = json.loads((SKILL_DIR / "metadata.json").read_text(encoding="utf-8"))
    assert _pyproject()["project"]["version"] == meta["version"]


def test_no_unused_dependencies_declared():
    # click / python-dateutil were declared everywhere but never imported.
    project = _pyproject()["project"]
    deps = "\n".join(project["dependencies"])
    assert "click" not in deps
    assert "dateutil" not in deps

    requirements = (SKILL_DIR / "requirements.txt").read_text(encoding="utf-8")
    assert "click" not in requirements
    assert "dateutil" not in requirements


def test_console_script_points_at_importable_main():
    scripts = _pyproject()["project"]["scripts"]
    assert scripts["intent-drift"] == "analyzer:main"

    import analyzer

    assert callable(analyzer.main)


def test_no_machine_local_engine_path():
    # The skill must resolve the engine from the installed package, not a
    # ~/Projects checkout.
    for fname in ("analyzer.py", "__init__.py", "pyproject.toml", "setup.py"):
        text = (SKILL_DIR / fname).read_text(encoding="utf-8")
        assert "Projects" not in text, f"{fname} still references a machine-local path"
        assert "Path.home" not in text, f"{fname} still references a machine-local path"


def test_setup_py_is_a_shim():
    # All metadata should live in pyproject.toml; setup.py must not duplicate it.
    setup = (SKILL_DIR / "setup.py").read_text(encoding="utf-8")
    assert "version=" not in setup
    assert "install_requires" not in setup
    assert "entry_points" not in setup


def test_engine_imports_without_sys_path_hack():
    """Importing the skill must not inject engine paths into sys.path."""
    import subprocess
    import sys

    script = (
        "import sys; before = list(sys.path); "
        "import analyzer; "
        "assert sys.path == before, 'skill mutated sys.path'; "
        "print('ok')"
    )
    # Fresh interpreter: an inherited, already-imported sys.path can't mask
    # (or falsely trigger) a skill-injected path. The environment is inherited,
    # so a dev engine on PYTHONPATH still resolves.
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=SKILL_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"skill import failed or mutated sys.path:\n{result.stderr}"
