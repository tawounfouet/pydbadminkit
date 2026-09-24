"""Distribution metadata contract for LOT-20."""

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _project() -> dict[str, object]:
    path = Path(__file__).parents[2] / "pyproject.toml"
    with path.open("rb") as stream:
        document = tomllib.load(stream)
    project = document["project"]
    assert isinstance(project, dict)
    return project


def test_distribution_identity_and_python_floor_are_frozen() -> None:
    project = _project()

    assert project["name"] == "pydbadminkit"
    assert project["requires-python"] == ">=3.11"
    assert project["readme"] == "README.md"
    assert project["dynamic"] == ["version"]


def test_console_script_and_repository_urls_are_declared() -> None:
    project = _project()

    assert project["scripts"] == {"pydbadmin": "pydbadminkit.cli.app:app"}
    assert project["urls"] == {
        "Homepage": "https://github.com/tawounfouet/pydbadminkit",
        "Repository": "https://github.com/tawounfouet/pydbadminkit",
        "Issues": "https://github.com/tawounfouet/pydbadminkit/issues",
        "Changelog": "https://github.com/tawounfouet/pydbadminkit/blob/main/CHANGELOG.md",
    }


def test_supported_python_versions_are_advertised() -> None:
    project = _project()
    classifiers = project["classifiers"]

    assert isinstance(classifiers, list)
    for version in ("3.11", "3.12", "3.13", "3.14"):
        assert f"Programming Language :: Python :: {version}" in classifiers


def test_runtime_dependency_major_bounds_are_explicit() -> None:
    project = _project()
    dependencies = project["dependencies"]

    assert isinstance(dependencies, list)
    assert "psycopg>=3.3,<4" in dependencies
    assert "platformdirs>=4,<5" in dependencies
    assert "PyYAML>=6,<7" in dependencies
    assert "rich>=13,<15" in dependencies
    assert "typer>=0.12,<1" in dependencies


def test_apache_2_license_is_declared_and_shipped() -> None:
    project = _project()

    assert project["license"] == "Apache-2.0"
    assert project["license-files"] == ["LICENSE"]
    assert (Path(__file__).parents[2] / "LICENSE").is_file()
