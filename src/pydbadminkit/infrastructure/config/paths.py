"""Cross-platform application paths."""

from pathlib import Path

from platformdirs import user_config_path


def default_config_path() -> Path:
    """Return the default PyDBAdminKit TOML configuration path."""

    return user_config_path("pydbadminkit") / "config.toml"
