from __future__ import annotations

from dataclasses import dataclass

from .crew_management import CrewManagementModule
from .inventory import InventoryModule
from .registration import RegistrationModule


@dataclass(frozen=True)
class MaintenanceJob:
    job_id: str
    car_id: str
    mechanic_name: str
    required_parts: tuple[tuple[str, int], ...]
    required_tools: tuple[tuple[str, int], ...]
    labor_cost: float
    status: str


class VehicleMaintenanceError(ValueError):
    pass


class VehicleMaintenanceModule:
    def __init__(
        self,
        registration: RegistrationModule,
        crew_management: CrewManagementModule,
        inventory: InventoryModule,
    ) -> None:
        self._registration = registration
        self._crew_management = crew_management
        self._inventory = inventory
        self._jobs: dict[str, MaintenanceJob] = {}

    def create_job(
        self,
        job_id: str,
        car_id: str,
        mechanic_name: str,
        required_parts: dict[str, int] | None = None,
        required_tools: dict[str, int] | None = None,
        labor_cost: float = 0,
    ) -> MaintenanceJob:
        cleaned_job_id = job_id.strip() if isinstance(job_id, str) else ""
        cleaned_car_id = car_id.strip() if isinstance(car_id, str) else ""
        cleaned_mechanic = mechanic_name.strip() if isinstance(mechanic_name, str) else ""

        if not cleaned_job_id:
            raise VehicleMaintenanceError("Job ID is required.")
        if not cleaned_car_id:
            raise VehicleMaintenanceError("Car ID is required.")
        if not cleaned_mechanic:
            raise VehicleMaintenanceError("Mechanic name is required.")

        job_key = cleaned_job_id.casefold()
        if job_key in self._jobs:
            raise VehicleMaintenanceError(f"Maintenance job '{cleaned_job_id}' already exists.")

        if not self._registration.is_registered(cleaned_mechanic):
            raise VehicleMaintenanceError(f"Crew member '{cleaned_mechanic}' is not registered.")

        role = self._crew_management.get_role(cleaned_mechanic)
        if role.casefold() != "mechanic":
            raise VehicleMaintenanceError(f"Crew member '{cleaned_mechanic}' is not a mechanic.")

        car = self._inventory.get_car(cleaned_car_id)
        if car.status not in {"damaged", "maintenance"}:
            raise VehicleMaintenanceError(f"Car '{car.car_id}' does not require maintenance.")

        normalized_parts = self._normalize_requirements(required_parts, "Part")
        normalized_tools = self._normalize_requirements(required_tools, "Tool")

        if not isinstance(labor_cost, (int, float)) or labor_cost < 0:
            raise VehicleMaintenanceError("Labor cost must be a non-negative number.")

        job = MaintenanceJob(
            job_id=cleaned_job_id,
            car_id=car.car_id,
            mechanic_name=cleaned_mechanic,
            required_parts=normalized_parts,
            required_tools=normalized_tools,
            labor_cost=float(labor_cost),
            status="planned",
        )
        self._jobs[job_key] = job
        self._inventory.set_car_status(car.car_id, "maintenance")
        return job

    def start_job(self, job_id: str) -> MaintenanceJob:
        job = self.get_job(job_id)
        if job.status != "planned":
            raise VehicleMaintenanceError("Only planned maintenance jobs can be started.")

        for part_name, quantity in job.required_parts:
            available = self._inventory.get_spare_part_quantity(part_name)
            if quantity > available:
                raise VehicleMaintenanceError(f"Insufficient spare part quantity for '{part_name}'.")

        for tool_name, quantity in job.required_tools:
            available = self._inventory.get_tool_quantity(tool_name)
            if quantity > available:
                raise VehicleMaintenanceError(f"Insufficient tool quantity for '{tool_name}'.")

        if job.labor_cost > self._inventory.get_cash_balance():
            raise VehicleMaintenanceError("Insufficient cash balance for labor cost.")

        for part_name, quantity in job.required_parts:
            self._inventory.consume_spare_part(part_name, quantity)

        for tool_name, quantity in job.required_tools:
            self._inventory.consume_tool(tool_name, quantity)

        if job.labor_cost > 0:
            self._inventory.spend_cash(job.labor_cost)

        updated = MaintenanceJob(
            job_id=job.job_id,
            car_id=job.car_id,
            mechanic_name=job.mechanic_name,
            required_parts=job.required_parts,
            required_tools=job.required_tools,
            labor_cost=job.labor_cost,
            status="active",
        )
        self._jobs[job.job_id.casefold()] = updated
        return updated

    def complete_job(self, job_id: str) -> MaintenanceJob:
        job = self.get_job(job_id)
        if job.status != "active":
            raise VehicleMaintenanceError("Only active maintenance jobs can be completed.")

        updated = MaintenanceJob(
            job_id=job.job_id,
            car_id=job.car_id,
            mechanic_name=job.mechanic_name,
            required_parts=job.required_parts,
            required_tools=job.required_tools,
            labor_cost=job.labor_cost,
            status="completed",
        )
        self._jobs[job.job_id.casefold()] = updated
        self._inventory.set_car_status(job.car_id, "ready")
        return updated

    def get_job(self, job_id: str) -> MaintenanceJob:
        key = self._normalize_job_key(job_id)
        job = self._jobs.get(key)
        if job is None:
            raise VehicleMaintenanceError(f"Maintenance job '{job_id.strip()}' does not exist.")
        return job

    def list_jobs(self) -> list[MaintenanceJob]:
        return sorted(self._jobs.values(), key=lambda job: job.job_id.casefold())

    def _normalize_job_key(self, job_id: str) -> str:
        cleaned = job_id.strip() if isinstance(job_id, str) else ""
        if not cleaned:
            raise VehicleMaintenanceError("Job ID is required.")
        return cleaned.casefold()

    def _normalize_requirements(
        self,
        requirements: dict[str, int] | None,
        item_type: str,
    ) -> tuple[tuple[str, int], ...]:
        if requirements is None:
            return ()
        if not isinstance(requirements, dict):
            raise VehicleMaintenanceError(f"{item_type} requirements must be a dictionary.")

        normalized: list[tuple[str, int]] = []
        seen: set[str] = set()
        for name, quantity in requirements.items():
            cleaned_name = name.strip() if isinstance(name, str) else ""
            if not cleaned_name:
                raise VehicleMaintenanceError(f"{item_type} name is required.")
            if not isinstance(quantity, int) or quantity <= 0:
                raise VehicleMaintenanceError(f"{item_type} quantity must be a positive integer.")
            key = cleaned_name.casefold()
            if key in seen:
                raise VehicleMaintenanceError(f"Duplicate {item_type.lower()} requirement for '{cleaned_name}'.")
            normalized.append((cleaned_name, quantity))
            seen.add(key)
        return tuple(normalized)
