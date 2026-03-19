from __future__ import annotations

from dataclasses import dataclass

from .crew_management import CrewManagementModule
from .inventory import InventoryModule
from .registration import RegistrationModule


@dataclass(frozen=True)
class Race:
    race_id: str
    name: str
    driver_name: str
    car_id: str
    status: str


class RaceManagementError(ValueError):
    pass


class RaceManagementModule:
    def __init__(
        self,
        registration: RegistrationModule,
        crew_management: CrewManagementModule,
        inventory: InventoryModule,
    ) -> None:
        self._registration = registration
        self._crew_management = crew_management
        self._inventory = inventory
        self._races: dict[str, Race] = {}

    def create_race(self, race_id: str, name: str, driver_name: str, car_id: str) -> Race:
        cleaned_race_id = race_id.strip() if isinstance(race_id, str) else ""
        cleaned_name = name.strip() if isinstance(name, str) else ""
        cleaned_driver = driver_name.strip() if isinstance(driver_name, str) else ""
        cleaned_car_id = car_id.strip() if isinstance(car_id, str) else ""

        if not cleaned_race_id:
            raise RaceManagementError("Race ID is required.")
        if not cleaned_name:
            raise RaceManagementError("Race name is required.")
        if not cleaned_driver:
            raise RaceManagementError("Driver name is required.")
        if not cleaned_car_id:
            raise RaceManagementError("Car ID is required.")

        race_key = cleaned_race_id.casefold()
        if race_key in self._races:
            raise RaceManagementError(f"Race '{cleaned_race_id}' already exists.")

        if not self._registration.is_registered(cleaned_driver):
            raise RaceManagementError(f"Crew member '{cleaned_driver}' is not registered.")

        role = self._crew_management.get_role(cleaned_driver)
        if role.casefold() != "driver":
            raise RaceManagementError(f"Crew member '{cleaned_driver}' is not a driver.")

        car = self._inventory.get_car(cleaned_car_id)
        if car.status != "ready":
            raise RaceManagementError(f"Car '{car.car_id}' is not ready for racing.")

        race = Race(
            race_id=cleaned_race_id,
            name=cleaned_name,
            driver_name=cleaned_driver,
            car_id=car.car_id,
            status="scheduled",
        )
        self._races[race_key] = race
        return race

    def get_race(self, race_id: str) -> Race:
        key = self._normalize_race_key(race_id)
        race = self._races.get(key)
        if race is None:
            raise RaceManagementError(f"Race '{race_id.strip()}' does not exist.")
        return race

    def start_race(self, race_id: str) -> Race:
        race = self.get_race(race_id)
        if race.status != "scheduled":
            raise RaceManagementError("Only scheduled races can be started.")
        updated = Race(
            race_id=race.race_id,
            name=race.name,
            driver_name=race.driver_name,
            car_id=race.car_id,
            status="active",
        )
        self._races[race.race_id.casefold()] = updated
        return updated

    def complete_race(self, race_id: str) -> Race:
        race = self.get_race(race_id)
        if race.status != "active":
            raise RaceManagementError("Only active races can be completed.")
        updated = Race(
            race_id=race.race_id,
            name=race.name,
            driver_name=race.driver_name,
            car_id=race.car_id,
            status="completed",
        )
        self._races[race.race_id.casefold()] = updated
        return updated

    def list_races(self) -> list[Race]:
        return sorted(self._races.values(), key=lambda race: race.race_id.casefold())

    def _normalize_race_key(self, race_id: str) -> str:
        cleaned = race_id.strip() if isinstance(race_id, str) else ""
        if not cleaned:
            raise RaceManagementError("Race ID is required.")
        return cleaned.casefold()
