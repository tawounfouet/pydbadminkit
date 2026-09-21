"""Safety planning models for administrative mutations."""

from dataclasses import dataclass
from enum import StrEnum

from pydbadminkit.domain.common import EnvironmentName, RiskLevel


class ConfirmationLevel(StrEnum):
    """Required proof of operator intent."""

    NONE = "none"
    SIMPLE = "simple"
    EXPLICIT = "explicit"
    TYPE_TARGET = "type_target"


@dataclass(frozen=True, slots=True)
class OperationPlan:
    """Immutable pre-execution plan exposed by dry-run."""

    operation: str
    target: str
    environment: EnvironmentName
    risk: RiskLevel
    confirmation: ConfirmationLevel
    effects: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    correlation_id: str = ""

    def __post_init__(self) -> None:
        if not self.operation or self.operation.isspace():
            raise ValueError("operation must not be blank")
        if not self.target or self.target.isspace():
            raise ValueError("target must not be blank")
        if not self.effects:
            raise ValueError("operation plan requires at least one effect")
        if not self.correlation_id or self.correlation_id.isspace():
            raise ValueError("correlation_id must not be blank")


@dataclass(frozen=True, slots=True)
class MutationOptions:
    """Caller-supplied execution approval; never prompts by itself."""

    dry_run: bool = False
    approved: bool = False
    confirmed_target: str | None = None
