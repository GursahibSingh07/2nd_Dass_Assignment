"""Crew management module for StreetRace Manager."""

from __future__ import annotations

from dataclasses import dataclass

from .registration import RegistrationModule


@dataclass(frozen=True)
class CrewSkill:

    name: str
    level: int


class CrewManagementError(ValueError):
    pass


class CrewManagementModule:

    def __init__(self, registration: RegistrationModule) -> None:
        self._registration = registration
        self._roles: dict[str, str] = {}
        self._skills: dict[str, dict[str, int]] = {}

    def assign_role(self, member_name: str, role: str) -> str:
        key = self._validate_registered_member(member_name)
        cleaned_role = role.strip() if isinstance(role, str) else ""
        if not cleaned_role:
            raise CrewManagementError("Role is required.")

        self._roles[key] = cleaned_role
        return cleaned_role

    def get_role(self, member_name: str) -> str:
        key = self._validate_registered_member(member_name)
        if key in self._roles:
            return self._roles[key]
        return self._registration.get_member(member_name).role

    def set_skill(self, member_name: str, skill_name: str, level: int) -> CrewSkill:
        key = self._validate_registered_member(member_name)
        cleaned_skill = skill_name.strip() if isinstance(skill_name, str) else ""
        if not cleaned_skill:
            raise CrewManagementError("Skill name is required.")
        if not isinstance(level, int) or not 1 <= level <= 10:
            raise CrewManagementError("Skill level must be an integer between 1 and 10.")

        member_skills = self._skills.setdefault(key, {})
        member_skills[cleaned_skill.casefold()] = level
        return CrewSkill(name=cleaned_skill, level=level)

    def get_skill_level(self, member_name: str, skill_name: str) -> int:
        key = self._validate_registered_member(member_name)
        cleaned_skill = skill_name.strip() if isinstance(skill_name, str) else ""
        if not cleaned_skill:
            raise CrewManagementError("Skill name is required.")

        member_skills = self._skills.get(key, {})
        skill_level = member_skills.get(cleaned_skill.casefold())
        if skill_level is None:
            raise CrewManagementError(
                f"Skill '{cleaned_skill}' is not recorded for member '{member_name.strip()}'."
            )
        return skill_level

    def list_member_skills(self, member_name: str) -> list[CrewSkill]:
        key = self._validate_registered_member(member_name)
        member_skills = self._skills.get(key, {})
        return [
            CrewSkill(name=skill_name, level=member_skills[skill_name])
            for skill_name in sorted(member_skills.keys())
        ]

    def _validate_registered_member(self, member_name: str) -> str:
        cleaned_name = member_name.strip() if isinstance(member_name, str) else ""
        if not cleaned_name:
            raise CrewManagementError("Member name is required.")
        if not self._registration.is_registered(cleaned_name):
            raise CrewManagementError(f"Crew member '{cleaned_name}' is not registered.")
        return cleaned_name.casefold()
