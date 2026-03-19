"""Registration module for StreetRace Manager."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CrewMember:
    name: str
    role: str


class RegistrationError(ValueError):
    pass


class RegistrationModule:
    def __init__(self) -> None:
        self._members: dict[str, CrewMember] = {}

    def register_member(self, name: str, role: str) -> CrewMember:

        cleaned_name = name.strip() if isinstance(name, str) else ""
        cleaned_role = role.strip() if isinstance(role, str) else ""

        if not cleaned_name:
            raise RegistrationError("Member name is required.")
        if not cleaned_role:
            raise RegistrationError("Member role is required.")

        member_key = cleaned_name.casefold()
        if member_key in self._members:
            raise RegistrationError(f"Crew member '{cleaned_name}' is already registered.")

        member = CrewMember(name=cleaned_name, role=cleaned_role)
        self._members[member_key] = member
        return member

    def get_member(self, name: str) -> CrewMember:
        cleaned_name = name.strip() if isinstance(name, str) else ""
        if not cleaned_name:
            raise RegistrationError("Member name is required.")

        member = self._members.get(cleaned_name.casefold())
        if member is None:
            raise RegistrationError(f"Crew member '{cleaned_name}' is not registered.")
        return member

    def list_members(self) -> list[CrewMember]:
        return sorted(self._members.values(), key=lambda m: m.name.casefold())

    def is_registered(self, name: str) -> bool:
        if not isinstance(name, str):
            return False
        cleaned_name = name.strip()
        return bool(cleaned_name) and cleaned_name.casefold() in self._members
