from __future__ import annotations

from .crew_management import CrewManagementModule
from .inventory import InventoryModule
from .leaderboard import LeaderboardModule
from .mission_planning import MissionPlanningModule
from .race_management import RaceManagementModule
from .registration import RegistrationModule
from .results import ResultsModule
from .vehicle_maintenance import VehicleMaintenanceModule


def _print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def run_demo() -> None:
    _print_section("Bootstrapping Modules")
    registration = RegistrationModule()
    crew = CrewManagementModule(registration)
    inventory = InventoryModule()
    races = RaceManagementModule(registration, crew, inventory)
    results = ResultsModule(registration, races, inventory)
    missions = MissionPlanningModule(registration, crew, inventory)
    maintenance = VehicleMaintenanceModule(registration, crew, inventory)
    leaderboard = LeaderboardModule(registration, results, races)
    print("Initialized registration, crew, inventory, races, results, missions, maintenance, leaderboard")

    _print_section("Crew Registration and Roles")
    rina = registration.register_member("Rina", "driver")
    miko = registration.register_member("Miko", "mechanic")
    ari = registration.register_member("Ari", "strategist")
    print(f"Registered: {rina.name} ({rina.role}), {miko.name} ({miko.role}), {ari.name} ({ari.role})")

    crew.assign_role("Rina", "driver")
    crew.assign_role("Miko", "mechanic")
    crew.assign_role("Ari", "strategist")
    print("Assigned roles: Rina=driver, Miko=mechanic, Ari=strategist")
    print("Current members:")
    for member in registration.list_members():
        print(f"- {member.name}: {crew.get_role(member.name)}")

    _print_section("Inventory Setup")
    inventory.add_car("RX7-01", "Mazda RX-7")
    inventory.add_spare_part("spark plug", 4)
    inventory.add_tool("jack", 1)
    print("Added car RX7-01, spare part spark plug x4, tool jack x1")
    print(f"Cars: {[f'{car.car_id} ({car.status})' for car in inventory.list_cars()]}")

    _print_section("Race Lifecycle")
    race = races.create_race("RACE-01", "Harbor Run", "Rina", "RX7-01")
    print(f"Created race: {race.race_id} | {race.name} | driver={race.driver_name} | status={race.status}")

    race = races.start_race(race.race_id)
    print(f"Started race: {race.race_id} -> status={race.status}")

    race = races.complete_race(race.race_id)
    print(f"Completed race: {race.race_id} -> status={race.status}")

    _print_section("Results and Leaderboard")
    result = results.record_result(race.race_id, 1, 1500, car_damaged=True)
    print(
        f"Recorded result: race={result.race_id}, driver={result.driver_name}, "
        f"position={result.position}, points={result.points_awarded}, prize=${result.prize_money:.2f}, "
        f"car_damaged={result.car_damaged}"
    )
    stats = leaderboard.sync_result(race.race_id)
    print(
        f"Leaderboard sync: {stats.driver_name} -> races={stats.races}, wins={stats.wins}, "
        f"points={stats.total_points}, best_position={stats.best_position}, prize_total=${stats.total_prize_money:.2f}"
    )

    rankings = leaderboard.list_rankings()
    print("Leaderboard rankings:")
    for index, row in enumerate(rankings, start=1):
        print(
            f"{index}. {row.driver_name} | points={row.total_points} | wins={row.wins} | "
            f"podiums={row.podiums} | best={row.best_position}"
        )

    _print_section("Mission Lifecycle")
    mission = missions.create_mission("MIS-01", "repair_support", ["driver", "mechanic"])
    print(
        f"Created mission: {mission.mission_id} | type={mission.mission_type} | "
        f"required_roles={list(mission.required_roles)} | status={mission.status}"
    )

    mission = missions.assign_members(mission.mission_id, ["Rina", "Miko"])
    print(f"Assigned mission members: {list(mission.assigned_members)} -> status={mission.status}")

    mission = missions.start_mission(mission.mission_id)
    print(f"Started mission: {mission.mission_id} -> status={mission.status}")

    mission = missions.complete_mission(mission.mission_id)
    print(f"Completed mission: {mission.mission_id} -> status={mission.status}")

    _print_section("Maintenance Lifecycle")
    job = maintenance.create_job(
        "JOB-01",
        "RX7-01",
        "Miko",
        {"spark plug": 2},
        {"jack": 1},
        300,
    )
    print(
        f"Created maintenance job: {job.job_id} | car={job.car_id} | mechanic={job.mechanic_name} | "
        f"parts={dict(job.required_parts)} | tools={dict(job.required_tools)} | labor=${job.labor_cost:.2f} | status={job.status}"
    )

    job = maintenance.start_job(job.job_id)
    print(f"Started maintenance job: {job.job_id} -> status={job.status}")

    job = maintenance.complete_job(job.job_id)
    print(f"Completed maintenance job: {job.job_id} -> status={job.status}")

    _print_section("Final Snapshots")
    print("Races:")
    for row in races.list_races():
        print(f"- {row.race_id}: {row.name} | driver={row.driver_name} | car={row.car_id} | status={row.status}")

    print("Results rankings:")
    for name, points in results.list_rankings():
        print(f"- {name}: {points} points")

    print("Missions:")
    for row in missions.list_missions():
        print(
            f"- {row.mission_id}: type={row.mission_type} | assigned={list(row.assigned_members)} | "
            f"required={list(row.required_roles)} | status={row.status}"
        )

    print("Maintenance jobs:")
    for row in maintenance.list_jobs():
        print(f"- {row.job_id}: car={row.car_id} | mechanic={row.mechanic_name} | status={row.status}")

    print("Inventory:")
    for car in inventory.list_cars():
        print(f"- Car {car.car_id}: {car.model} | status={car.status}")
    print(
        f"- Stock: spark plug={inventory.get_spare_part_quantity('spark plug')}, "
        f"jack={inventory.get_tool_quantity('jack')}"
    )
    print(f"- Cash balance: ${inventory.get_cash_balance():.2f}")


def main() -> None:
    print("[StreetRace] Running integration demo...")
    run_demo()
    print("[StreetRace] Demo completed successfully.")


if __name__ == "__main__":
    main()
