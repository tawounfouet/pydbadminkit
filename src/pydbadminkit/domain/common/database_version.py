"""Database version value object."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class DatabaseVersion:
    """Engine-independent semantic database version."""

    major: int
    minor: int = 0
    patch: int = 0

    def __post_init__(self) -> None:
        if self.major < 0:
            raise ValueError("major version must be >= 0")
        if self.minor < 0:
            raise ValueError("minor version must be >= 0")
        if self.patch < 0:
            raise ValueError("patch version must be >= 0")

    def __str__(self) -> str:
        if self.patch:
            return f"{self.major}.{self.minor}.{self.patch}"
        if self.minor:
            return f"{self.major}.{self.minor}"
        return str(self.major)
