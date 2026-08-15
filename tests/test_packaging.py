"""Packaging consistency tests (issue #12).

These guard the parts of #12 that were still broken after the earlier merged
fixes (console script + engine rename): the unused ``click``/``python-dateutil``
dependencies, the machine-local engine path in ``analyzer.py``/``__init__.py``,
and the package metadata living in ``setup.py`` with no ``[project]`` section in
``pyproject.toml``.
"""

from pathlib import Path

import tomllib

SKILL_DIR = Path(__file__).resolve().parent.parent


def _pyproject() -> dict:
    with (SKILL_DIR / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)


def test_project_metadata_lives_in_pyproject_toml():
    project = _pyproject()["project"]
    assert project["name"] == "claude-skill-intent-drift"
    assert project["version"] == "1.0.0"
    assert any("intent-drift" in d for d in project["dependencies"])
    assert any("PyYAML" in d for d in project["dependencies"])


def test_pyproject_version_matches_metadata_json():
    import json

    meta = json.loads((SKILL_DIR / "metadata.json").read_text())
    assert _pyproject()["project"]["version"] == meta["version"]


def test_no_unused_dependencies_declared():
    # click / python-dateutil were declared everywhere but never imported.
    project = _pyproject()["project"]
    deps = "\n".join(project["dependencies"])
    assert "click" not in deps
    assert "dateutil" not in deps

    requirements = (SKILL_DIR / "requirements.txt").read_text()
    assert "click" not in requirements
    assert "dateutil" not in requirements


def test_console_script_points_at_importable_main():
    scripts = _pyproject()["project"]["scripts"]
    assert scripts["intent-drift"] == "analyzer:main"

    import analyzer

    assert callable(analyzer.main)


def test_no_machine_local_engine_path():
    # The skill must resolve the engine from PyPI, not a ~/Projects checkout.
    for fname in ("analyzer.py", "__init__.py", "pyproject.toml", "setup.py"):
        text = (SKILL_DIR / fname).read_text()
        assert "Projects" not in text, f"{fname} still references a machine-local path"
        assert "Path.home" not in text, f"{fname} still references a machine-local path"


def test_setup_py_is_a_shim():
    # All metadata should live in pyproject.toml; setup.py must not duplicate it.
    setup = (SKILL_DIR / "setup.py").read_text()
    assert "version=" not in setup
    assert "install_requires" not in setup
    assert "entry_points" not in setup


def test_engine_imports_without_sys_path_hack():
    import sys

    import intent_alignment

    # The engine must come from an installed package, not a ~/Projects checkout
    # path inserted by the skill's own import machinery.
    assert "intent_alignment" in sys.modules
    engine_file = Path(intent_alignment.__file__).resolve()
    assert "site-packages" in str(engine_file) or "dist-packages" in str(engine_file)
    assert not any(str(Path.home() / "Projects") in p for p in sys.path)
