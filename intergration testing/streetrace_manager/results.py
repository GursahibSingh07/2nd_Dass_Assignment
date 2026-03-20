from __future__ import annotations

from dataclasses import dataclass

from .inventory import InventoryModule
from .race_management import RaceManagementModule
from .registration import RegistrationModule


@dataclass(frozen=True)
class RaceResult:
    race_id: str
    driver_name: str
    car_id: str
    position: int
    points_awarded: int
    prize_money: float
    car_damaged: bool


class ResultsError(ValueError):
    pass


class ResultsModule:
    def __init__(
        self,
        registration: RegistrationModule,
        race_management: RaceManagementModule,
        inventory: InventoryModule,
    ) -> None:
        self._registration = registration
        self._race_management = race_management
        self._inventory = inventory
        self._results: dict[str, RaceResult] = {}
        self._rankings: dict[str, int] = {}
        self._display_names: dict[str, str] = {}

    def record_result(self, race_id: str, position: int, prize_money: float, car_damaged: bool = False) -> RaceResult:
        cleaned_race_id = race_id.strip() if isinstance(race_id, str) else ""
        if not cleaned_race_id:
            raise ResultsError("Race ID is required.")
        if not isinstance(position, int) or position <= 0:
            raise ResultsError("Position must be a positive integer.")
        if not isinstance(prize_money, (int, float)) or prize_money < 0:
            raise ResultsError("Prize money must be a non-negative number.")
        if not isinstance(car_damaged, bool):
            raise ResultsError("Car damaged flag must be a boolean.")

        race_key = cleaned_race_id.casefold()
        if race_key in self._results:
            raise ResultsError(f"Result for race '{cleaned_race_id}' is already recorded.")

        race = self._race_management.get_race(cleaned_race_id)
        if race.status != "completed":
            raise ResultsError(f"Race '{race.race_id}' is not completed.")

        points = self._calculate_points(position)

        if prize_money > 0:
            self._inventory.add_cash(float(prize_money))
        if car_damaged:
            self._inventory.set_car_status(race.car_id, "damaged")

        driver_key = race.driver_name.casefold()
        self._rankings[driver_key] = self._rankings.get(driver_key, 0) + points
        self._display_names[driver_key] = race.driver_name

        result = RaceResult(
            race_id=race.race_id,
            driver_name=race.driver_name,
            car_id=race.car_id,
            position=position,
            points_awarded=points,
            prize_money=float(prize_money),
            car_damaged=car_damaged,
        )
        self._results[race_key] = result
        return result

    def get_result(self, race_id: str) -> RaceResult:
        key = self._normalize_race_key(race_id)
        result = self._results.get(key)
        if result is None:
            raise ResultsError(f"Result for race '{race_id.strip()}' does not exist.")
        return result

    def get_driver_points(self, member_name: str) -> int:
        cleaned_name = member_name.strip() if isinstance(member_name, str) else ""
        if not cleaned_name:
            raise ResultsError("Member name is required.")
        if not self._registration.is_registered(cleaned_name):
            raise ResultsError(f"Crew member '{cleaned_name}' is not registered.")
        return self._rankings.get(cleaned_name.casefold(), 0)

    def list_rankings(self) -> list[tuple[str, int]]:
        ranked = [
            (self._display_names[member_key], points)
            for member_key, points in self._rankings.items()
        ]
        return sorted(ranked, key=lambda item: (-item[1], item[0].casefold()))

    def _normalize_race_key(self, race_id: str) -> str:
        cleaned = race_id.strip() if isinstance(race_id, str) else ""
        if not cleaned:
            raise ResultsError("Race ID is required.")
        return cleaned.casefold()

    def _calculate_points(self, position: int) -> int:
        if position == 1:
            return 10
        if position == 2:
            return 6
        if position == 3:
            return 4
        return 1
