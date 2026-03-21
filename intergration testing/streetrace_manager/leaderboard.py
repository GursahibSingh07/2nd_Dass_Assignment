from __future__ import annotations

from dataclasses import dataclass

from .race_management import RaceManagementModule
from .registration import RegistrationModule
from .results import ResultsModule


@dataclass(frozen=True)
class DriverStats:
    driver_name: str
    races: int
    wins: int
    losses: int
    podiums: int
    total_points: int
    best_position: int | None
    total_prize_money: float


class LeaderboardError(ValueError):
    pass


class LeaderboardModule:
    def __init__(
        self,
        registration: RegistrationModule,
        results: ResultsModule,
        race_management: RaceManagementModule,
    ) -> None:
        self._registration = registration
        self._results = results
        self._race_management = race_management
        self._stats: dict[str, DriverStats] = {}
        self._display_names: dict[str, str] = {}
        self._processed_races: set[str] = set()

    def record_result(
        self,
        race_id: str,
        position: int,
        prize_money: float,
        car_damaged: bool = False,
    ) -> DriverStats:
        cleaned_race_id = race_id.strip() if isinstance(race_id, str) else ""
        if not cleaned_race_id:
            raise LeaderboardError("Race ID is required.")

        race_key = cleaned_race_id.casefold()
        if race_key in self._processed_races:
            raise LeaderboardError(f"Leaderboard already processed race '{cleaned_race_id}'.")

        result = self._results.record_result(cleaned_race_id, position, prize_money, car_damaged)
        self._processed_races.add(race_key)
        return self._apply_result(result.driver_name, result.position, result.points_awarded, result.prize_money)

    def sync_result(self, race_id: str) -> DriverStats:
        cleaned_race_id = race_id.strip() if isinstance(race_id, str) else ""
        if not cleaned_race_id:
            raise LeaderboardError("Race ID is required.")

        race_key = cleaned_race_id.casefold()
        if race_key in self._processed_races:
            raise LeaderboardError(f"Leaderboard already processed race '{cleaned_race_id}'.")

        result = self._results.get_result(cleaned_race_id)
        self._processed_races.add(race_key)
        return self._apply_result(result.driver_name, result.position, result.points_awarded, result.prize_money)

    def get_driver_stats(self, member_name: str) -> DriverStats:
        cleaned_name = member_name.strip() if isinstance(member_name, str) else ""
        if not cleaned_name:
            raise LeaderboardError("Member name is required.")
        if not self._registration.is_registered(cleaned_name):
            raise LeaderboardError(f"Crew member '{cleaned_name}' is not registered.")

        key = cleaned_name.casefold()
        existing = self._stats.get(key)
        if existing is not None:
            return existing

        member = self._registration.get_member(cleaned_name)
        return DriverStats(
            driver_name=member.name,
            races=0,
            wins=0,
            losses=0,
            podiums=0,
            total_points=0,
            best_position=None,
            total_prize_money=0.0,
        )

    def list_rankings(self) -> list[DriverStats]:
        return sorted(
            self._stats.values(),
            key=lambda item: (-item.total_points, -item.wins, item.best_position or 9999, item.driver_name.casefold()),
        )

    def seed_race_drivers(self) -> list[str]:
        seen: set[str] = set()
        candidates: list[str] = []
        for race in self._race_management.list_races():
            key = race.driver_name.casefold()
            if key not in seen:
                candidates.append(race.driver_name)
                seen.add(key)

        return [
            item[0]
            for item in sorted(
                [(name, self._stats.get(name.casefold())) for name in candidates],
                key=lambda item: self._seed_sort_key(item[0], item[1]),
            )
        ]

    def _apply_result(self, driver_name: str, position: int, points_awarded: int, prize_money: float) -> DriverStats:
        key = driver_name.casefold()
        existing = self._stats.get(
            key,
            DriverStats(
                driver_name=driver_name,
                races=0,
                wins=0,
                losses=0,
                podiums=0,
                total_points=0,
                best_position=None,
                total_prize_money=0.0,
            ),
        )

        best_position = existing.best_position
        if best_position is None or position < best_position:
            best_position = position

        updated = DriverStats(
            driver_name=driver_name,
            races=existing.races + 1,
            wins=existing.wins + (1 if position == 1 else 0),
            losses=existing.losses + (1 if position != 1 else 0),
            podiums=existing.podiums + (1 if position <= 3 else 0),
            total_points=existing.total_points + points_awarded,
            best_position=best_position,
            total_prize_money=existing.total_prize_money + float(prize_money),
        )
        self._stats[key] = updated
        self._display_names[key] = driver_name
        return updated

    def _seed_sort_key(self, driver_name: str, stats: DriverStats | None) -> tuple[int, int, int, str]:
        if stats is None:
            return (0, 0, 9999, driver_name.casefold())
        return (-stats.total_points, -stats.wins, stats.best_position or 9999, stats.driver_name.casefold())
