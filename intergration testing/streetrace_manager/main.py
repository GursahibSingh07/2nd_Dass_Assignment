from __future__ import annotations

from streetrace_manager.crew_management import CrewManagementModule
from streetrace_manager.inventory import InventoryModule
from streetrace_manager.leaderboard import LeaderboardModule
from streetrace_manager.mission_planning import MissionPlanningModule
from streetrace_manager.race_management import RaceManagementModule
from streetrace_manager.registration import RegistrationModule
from streetrace_manager.results import ResultsModule
from streetrace_manager.vehicle_maintenance import VehicleMaintenanceModule


def run_demo() -> None:
    registration = RegistrationModule()
    crew = CrewManagementModule(registration)
    inventory = InventoryModule()
    races = RaceManagementModule(registration, crew, inventory)
    results = ResultsModule(registration, races, inventory)
    missions = MissionPlanningModule(registration, crew, inventory)
    maintenance = VehicleMaintenanceModule(registration, crew, inventory)
    leaderboard = LeaderboardModule(registration, results, races)

    registration.register_member("Rina", "driver")
    registration.register_member("Miko", "mechanic")
    registration.register_member("Ari", "strategist")

    crew.assign_role("Rina", "driver")
    crew.assign_role("Miko", "mechanic")
    crew.assign_role("Ari", "strategist")

    inventory.add_car("RX7-01", "Mazda RX-7")
    inventory.add_spare_part("spark plug", 4)
    inventory.add_tool("jack", 1)

    race = races.create_race("RACE-01", "Harbor Run", "Rina", "RX7-01")
    races.start_race(race.race_id)
    races.complete_race(race.race_id)

    result = results.record_result(race.race_id, 1, 1500, car_damaged=True)
    stats = leaderboard.sync_result(race.race_id)

    mission = missions.create_mission("MIS-01", "repair_support", ["driver", "mechanic"])
    missions.assign_members(mission.mission_id, ["Rina", "Miko"])
    missions.start_mission(mission.mission_id)
    missions.complete_mission(mission.mission_id)

    job = maintenance.create_job(
        "JOB-01",
        "RX7-01",
        "Miko",
        {"spark plug": 2},
        {"jack": 1},
        300,
    )
    maintenance.start_job(job.job_id)
    maintenance.complete_job(job.job_id)

    races.get_race(race.race_id)
    inventory.get_car("RX7-01")
    missions.get_mission("MIS-01")
    leaderboard.list_rankings()
    _ = result.points_awarded
    _ = stats.total_points


def main() -> None:
    run_demo()


if __name__ == "__main__":
    main()
