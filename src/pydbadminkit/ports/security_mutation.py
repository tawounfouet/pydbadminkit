"""Security mutation port."""

from typing import Protocol

from pydbadminkit.domain.security.mutations import (
    AlterRoleCommand,
    CreateRoleCommand,
    MembershipCommand,
    RelationAccessCommand,
)


class SecurityMutationPort(Protocol):
    """Engine-specific execution contract for security mutations."""

    def create_role(self, command: CreateRoleCommand) -> None:
        ...

    def alter_role(self, command: AlterRoleCommand) -> None:
        ...

    def drop_role(self, name: str) -> None:
        ...

    def add_membership(self, command: MembershipCommand) -> None:
        ...

    def remove_membership(self, command: MembershipCommand) -> None:
        ...

    def grant_access(self, command: RelationAccessCommand) -> None:
        ...

    def revoke_access(self, command: RelationAccessCommand) -> None:
        ...
