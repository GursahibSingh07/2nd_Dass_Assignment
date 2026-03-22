from __future__ import annotations

from dataclasses import dataclass

from .crew_management import CrewManagementModule
from .inventory import InventoryModule
from .registration import RegistrationModule


@dataclass(frozen=True)
class Mission:
    mission_id: str
    mission_type: str
    assigned_members: tuple[str, ...]
    required_roles: tuple[str, ...]
    status: str


class MissionPlanningError(ValueError):
    pass


class MissionPlanningModule:
    def __init__(
        self,
        registration: RegistrationModule,
        crew_management: CrewManagementModule,
        inventory: InventoryModule,
    ) -> None:
        self._registration = registration
        self._crew_management = crew_management
        self._inventory = inventory
        self._missions: dict[str, Mission] = {}

    def create_mission(self, mission_id: str, mission_type: str, required_roles: list[str] | tuple[str, ...]) -> Mission:
        cleaned_mission_id = mission_id.strip() if isinstance(mission_id, str) else ""
        cleaned_mission_type = mission_type.strip() if isinstance(mission_type, str) else ""

        if not cleaned_mission_id:
            raise MissionPlanningError("Mission ID is required.")
        if not cleaned_mission_type:
            raise MissionPlanningError("Mission type is required.")

        mission_key = cleaned_mission_id.casefold()
        if mission_key in self._missions:
            raise MissionPlanningError(f"Mission '{cleaned_mission_id}' already exists.")

        normalized_roles = self._normalize_roles(required_roles)

        mission = Mission(
            mission_id=cleaned_mission_id,
            mission_type=cleaned_mission_type,
            assigned_members=(),
            required_roles=normalized_roles,
            status="planned",
        )
        self._missions[mission_key] = mission
        return mission

    def assign_members(self, mission_id: str, member_names: list[str] | tuple[str, ...]) -> Mission:
        mission = self.get_mission(mission_id)
        if mission.status != "planned":
            raise MissionPlanningError("Members can only be assigned to planned missions.")

        if not isinstance(member_names, (list, tuple)) or not member_names:
            raise MissionPlanningError("At least one member is required.")

        normalized_members: list[str] = []
        seen: set[str] = set()
        available_roles: set[str] = set()

        for member_name in member_names:
            cleaned_member = member_name.strip() if isinstance(member_name, str) else ""
            if not cleaned_member:
                raise MissionPlanningError("Member name is required.")
            member_key = cleaned_member.casefold()
            if member_key in seen:
                raise MissionPlanningError(f"Crew member '{cleaned_member}' is duplicated in assignment.")
            if not self._registration.is_registered(cleaned_member):
                raise MissionPlanningError(f"Crew member '{cleaned_member}' is not registered.")

            role = self._crew_management.get_role(cleaned_member)
            available_roles.add(role.casefold())
            normalized_members.append(cleaned_member)
            seen.add(member_key)

        missing_roles = [role for role in mission.required_roles if role.casefold() not in available_roles]
        if missing_roles:
            missing = ", ".join(missing_roles)
            raise MissionPlanningError(f"Required roles unavailable: {missing}.")

        updated = Mission(
            mission_id=mission.mission_id,
            mission_type=mission.mission_type,
            assigned_members=tuple(normalized_members),
            required_roles=mission.required_roles,
            status="ready",
        )
        self._missions[mission.mission_id.casefold()] = updated
        return updated

    def start_mission(self, mission_id: str) -> Mission:
        mission = self.get_mission(mission_id)
        if mission.status != "ready":
            raise MissionPlanningError("Only ready missions can be started.")

        for member_name in mission.assigned_members:
            if not self._registration.is_registered(member_name):
                raise MissionPlanningError(f"Crew member '{member_name}' is no longer registered.")

        if "mechanic" in {role.casefold() for role in mission.required_roles} and not self._has_available_mechanic(mission):
            raise MissionPlanningError("Missions requiring mechanic cannot start without an available mechanic.")

        updated = Mission(
            mission_id=mission.mission_id,
            mission_type=mission.mission_type,
            assigned_members=mission.assigned_members,
            required_roles=mission.required_roles,
            status="active",
        )
        self._missions[mission.mission_id.casefold()] = updated
        return updated

    def complete_mission(self, mission_id: str) -> Mission:
        mission = self.get_mission(mission_id)
        if mission.status != "active":
            raise MissionPlanningError("Only active missions can be completed.")

        updated = Mission(
            mission_id=mission.mission_id,
            mission_type=mission.mission_type,
            assigned_members=mission.assigned_members,
            required_roles=mission.required_roles,
            status="completed",
        )
        self._missions[mission.mission_id.casefold()] = updated
        return updated

    def get_mission(self, mission_id: str) -> Mission:
        key = self._normalize_mission_key(mission_id)
        mission = self._missions.get(key)
        if mission is None:
            raise MissionPlanningError(f"Mission '{mission_id.strip()}' does not exist.")
        return mission

    def list_missions(self) -> list[Mission]:
        return sorted(self._missions.values(), key=lambda mission: mission.mission_id.casefold())

    def _normalize_mission_key(self, mission_id: str) -> str:
        cleaned = mission_id.strip() if isinstance(mission_id, str) else ""
        if not cleaned:
            raise MissionPlanningError("Mission ID is required.")
        return cleaned.casefold()

    def _normalize_roles(self, required_roles: list[str] | tuple[str, ...]) -> tuple[str, ...]:
        if not isinstance(required_roles, (list, tuple)) or not required_roles:
            raise MissionPlanningError("At least one required role is needed.")

        normalized: list[str] = []
        seen: set[str] = set()
        for role in required_roles:
            cleaned_role = role.strip() if isinstance(role, str) else ""
            if not cleaned_role:
                raise MissionPlanningError("Required role is invalid.")
            key = cleaned_role.casefold()
            if key not in seen:
                normalized.append(cleaned_role)
                seen.add(key)
        return tuple(normalized)

    def _has_available_mechanic(self, mission: Mission) -> bool:
        has_mechanic = False
        for member_name in mission.assigned_members:
            if self._crew_management.get_role(member_name).casefold() == "mechanic":
                has_mechanic = True
                break
        if not has_mechanic:
            return False
        if mission.mission_type.casefold() in {"repair", "repair_support", "maintenance"}:
            return True
        for car in self._inventory.list_cars():
            if car.status == "damaged":
                return False
        return True
