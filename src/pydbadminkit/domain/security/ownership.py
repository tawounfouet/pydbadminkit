"""Database object ownership models."""

from dataclasses import dataclass

from pydbadminkit.domain.common import DatabaseObjectRef


@dataclass(frozen=True, slots=True)
class OwnershipInfo:
    """One ownership relationship between a principal and a database object."""

    owner: str
    object: DatabaseObjectRef

    def __post_init__(self) -> None:
        if not self.owner or self.owner.isspace():
            raise ValueError("owner must not be blank")
