import pytest

from streetrace_manager.crew_management import CrewManagementModule
from streetrace_manager.inventory import InventoryError, InventoryModule
from streetrace_manager.leaderboard import LeaderboardError, LeaderboardModule
from streetrace_manager.mission_planning import MissionPlanningError, MissionPlanningModule
from streetrace_manager.race_management import RaceManagementError, RaceManagementModule
from streetrace_manager.registration import RegistrationModule
from streetrace_manager.results import ResultsError, ResultsModule
from streetrace_manager.vehicle_maintenance import VehicleMaintenanceError, VehicleMaintenanceModule


def _build_system() -> tuple[
    RegistrationModule,
    CrewManagementModule,
    InventoryModule,
    RaceManagementModule,
    ResultsModule,
    MissionPlanningModule,
    VehicleMaintenanceModule,
    LeaderboardModule,
]:
    registration = RegistrationModule()
    crew = CrewManagementModule(registration)
    inventory = InventoryModule()
    races = RaceManagementModule(registration, crew, inventory)
    results = ResultsModule(registration, races, inventory)
    missions = MissionPlanningModule(registration, crew, inventory)
    maintenance = VehicleMaintenanceModule(registration, crew, inventory)
    leaderboard = LeaderboardModule(registration, results, races)
    return registration, crew, inventory, races, results, missions, maintenance, leaderboard


def test_tc_01_register_driver_then_enter_race_success() -> None:
    registration, crew, inventory, races, _, _, _, _ = _build_system()
    registration.register_member("Rina", "driver")
    crew.assign_role("Rina", "driver")
    inventory.add_car("RX7-01", "Mazda RX-7")
    race = races.create_race("RACE-01", "Harbor Run", "Rina", "RX7-01")
    assert race.status == "scheduled"

def test_tc_02_enter_race_without_registered_driver_fails() -> None:
    _, _, inventory, races, _, _, _, _ = _build_system()
    inventory.add_car("EVO-09", "Mitsubishi Evo IX")
    with pytest.raises(RaceManagementError, match="Crew member 'Ghost' is not registered."):
        races.create_race("RACE-02", "Tunnel Sprint", "Ghost", "EVO-09")

def test_tc_03_registered_non_driver_cannot_enter_race() -> None:
    registration, crew, inventory, races, _, _, _, _ = _build_system()
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Miko", "mechanic")
    inventory.add_car("SUPRA-01", "Toyota Supra")
    with pytest.raises(RaceManagementError, match="Crew member 'Miko' is not a driver."):
        races.create_race("RACE-03", "City Loop", "Miko", "SUPRA-01")

def test_tc_04_damaged_car_cannot_be_used_for_race() -> None:
    registration, crew, inventory, races, _, _, _, _ = _build_system()
    registration.register_member("Nova", "driver")
    crew.assign_role("Nova", "driver")
    inventory.add_car("GTR-01", "Nissan GT-R")
    inventory.set_car_status("GTR-01", "damaged")
    with pytest.raises(RaceManagementError, match="Car 'GTR-01' is not ready for racing."):
        races.create_race("RACE-04", "Midnight Dash", "Nova", "GTR-01")

def test_tc_05_mission_start_should_fail_when_any_car_is_damaged() -> None:
    registration, crew, inventory, _, _, missions, _, _ = _build_system()
    registration.register_member("Rina", "driver")
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Rina", "driver")
    crew.assign_role("Miko", "mechanic")
    inventory.add_car("CAR-31", "Nissan GT-R")
    inventory.set_car_status("CAR-31", "damaged")
    missions.create_mission("MIS-31", "rescue", ["driver", "mechanic"])
    missions.assign_members("MIS-31", ["Rina", "Miko"])
    with pytest.raises(MissionPlanningError):
        missions.start_mission("MIS-31")

def test_tc_06_cannot_start_race_twice() -> None:
    registration, crew, inventory, races, _, _, _, _ = _build_system()
    registration.register_member("Rina", "driver")
    crew.assign_role("Rina", "driver")
    inventory.add_car("S15-01", "Nissan Silvia")
    races.create_race("RACE-06", "Neon Drift", "Rina", "S15-01")
    races.start_race("RACE-06")
    with pytest.raises(RaceManagementError, match="Only scheduled races can be started."):
        races.start_race("RACE-06")

def test_tc_07_cannot_complete_race_before_starting() -> None:
    registration, crew, inventory, races, _, _, _, _ = _build_system()
    registration.register_member("Rina", "driver")
    crew.assign_role("Rina", "driver")
    inventory.add_car("R34-01", "Nissan Skyline")
    races.create_race("RACE-07", "Port Sprint", "Rina", "R34-01")
    with pytest.raises(RaceManagementError, match="Only active races can be completed."):
        races.complete_race("RACE-07")


def test_tc_08_reassign_role_to_driver_allows_race_entry() -> None:
    registration, crew, inventory, races, _, _, _, _ = _build_system()
    registration.register_member("Kai", "mechanic")
    crew.assign_role("Kai", "mechanic")
    crew.assign_role("Kai", "driver")
    inventory.add_car("AE86-01", "Toyota AE86")
    race = races.create_race("RACE-08", "Hill Run", "Kai", "AE86-01")
    assert race.driver_name == "Kai"


def test_tc_09_complete_race_updates_results_points_and_cash() -> None:
    registration, crew, inventory, races, results, _, _, _ = _build_system()
    registration.register_member("Lena", "driver")
    crew.assign_role("Lena", "driver")
    inventory.add_car("R8-01", "Audi R8")
    races.create_race("RACE-09", "Bridge Run", "Lena", "R8-01")
    races.start_race("RACE-09")
    races.complete_race("RACE-09")
    result = results.record_result("RACE-09", 1, 1000)
    assert result.points_awarded == 10
    assert results.get_driver_points("Lena") == 10
    assert inventory.get_cash_balance() == 1000


def test_tc_10_duplicate_requirement_keys_should_be_rejected() -> None:
    registration, crew, inventory, _, _, _, maintenance, _ = _build_system()
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Miko", "mechanic")
    inventory.add_car("CAR-33", "Toyota Supra")
    inventory.set_car_status("CAR-33", "damaged")
    with pytest.raises(VehicleMaintenanceError):
        maintenance.create_job("JOB-33", "CAR-33", "Miko", {"bolt": 1, "BOLT": 2}, None, 0)


def test_tc_11_result_cannot_be_recorded_for_non_completed_race() -> None:
    registration, crew, inventory, races, results, _, _, _ = _build_system()
    registration.register_member("Rina", "driver")
    crew.assign_role("Rina", "driver")
    inventory.add_car("350Z-01", "Nissan 350Z")
    races.create_race("RACE-11", "Tunnel Edge", "Rina", "350Z-01")
    with pytest.raises(ResultsError, match="Race 'RACE-11' is not completed."):
        results.record_result("RACE-11", 3, 300)


def test_tc_12_result_can_mark_car_damaged_and_block_next_race() -> None:
    registration, crew, inventory, races, results, _, _, _ = _build_system()
    registration.register_member("Nova", "driver")
    crew.assign_role("Nova", "driver")
    inventory.add_car("GTR-12", "Nissan GT-R")
    races.create_race("RACE-12", "Late Chase", "Nova", "GTR-12")
    races.start_race("RACE-12")
    races.complete_race("RACE-12")
    results.record_result("RACE-12", 4, 100, car_damaged=True)
    assert inventory.get_car("GTR-12").status == "damaged"
    with pytest.raises(RaceManagementError, match="Car 'GTR-12' is not ready for racing."):
        races.create_race("RACE-12B", "Retry", "Nova", "GTR-12")


def test_tc_13_zero_prize_updates_points_without_cash_change() -> None:
    registration, crew, inventory, races, results, _, _, _ = _build_system()
    registration.register_member("Ari", "driver")
    crew.assign_role("Ari", "driver")
    inventory.add_car("RX8-01", "Mazda RX-8")
    races.create_race("RACE-13", "Zero Pot", "Ari", "RX8-01")
    races.start_race("RACE-13")
    races.complete_race("RACE-13")
    results.record_result("RACE-13", 2, 0)
    assert results.get_driver_points("Ari") == 6
    assert inventory.get_cash_balance() == 0


def test_tc_14_leaderboard_sync_reads_existing_results() -> None:
    registration, crew, inventory, races, results, _, _, leaderboard = _build_system()
    registration.register_member("Rina", "driver")
    crew.assign_role("Rina", "driver")
    inventory.add_car("GT86-01", "Toyota GT86")
    races.create_race("RACE-14", "Harbor Arc", "Rina", "GT86-01")
    races.start_race("RACE-14")
    races.complete_race("RACE-14")
    results.record_result("RACE-14", 1, 1100)
    stats = leaderboard.sync_result("RACE-14")
    assert stats.total_points == 10
    assert stats.wins == 1

def test_tc_15_results_recording_requires_driver_to_be_registered() -> None:
    reg_a = RegistrationModule()
    crew_a = CrewManagementModule(reg_a)
    inv_a = InventoryModule()
    races_a = RaceManagementModule(reg_a, crew_a, inv_a)

    reg_a.register_member("Lena", "driver")
    crew_a.assign_role("Lena", "driver")
    inv_a.add_car("CAR-32", "Audi R8")
    races_a.create_race("RACE-32", "Night Sprint", "Lena", "CAR-32")
    races_a.start_race("RACE-32")
    races_a.complete_race("RACE-32")

    
    empty_reg = RegistrationModule()
    results_isolated = ResultsModule(empty_reg, races_a, inv_a)

    with pytest.raises(ResultsError):
        results_isolated.record_result("RACE-32", 1, 500)


def test_tc_16_leaderboard_rejects_duplicate_race_processing() -> None:
    registration, crew, inventory, races, _, _, _, leaderboard = _build_system()
    registration.register_member("Lena", "driver")
    crew.assign_role("Lena", "driver")
    inventory.add_car("AMG-01", "Mercedes AMG")
    races.create_race("RACE-16", "Glass Loop", "Lena", "AMG-01")
    races.start_race("RACE-16")
    races.complete_race("RACE-16")
    leaderboard.record_result("RACE-16", 2, 500)
    with pytest.raises(LeaderboardError, match="Leaderboard already processed race 'race-16'."):
        leaderboard.record_result("race-16", 3, 100)


def test_tc_17_leaderboard_seeding_uses_race_and_stats_data() -> None:
    registration, crew, inventory, races, _, _, _, leaderboard = _build_system()
    registration.register_member("Rina", "driver")
    registration.register_member("Ari", "driver")
    crew.assign_role("Rina", "driver")
    crew.assign_role("Ari", "driver")
    inventory.add_car("RACECAR-1", "Lotus Exige")
    inventory.add_car("RACECAR-2", "Porsche 911")
    races.create_race("RACE-17A", "Alpha", "Rina", "RACECAR-1")
    races.start_race("RACE-17A")
    races.complete_race("RACE-17A")
    races.create_race("RACE-17B", "Beta", "Ari", "RACECAR-2")
    races.start_race("RACE-17B")
    races.complete_race("RACE-17B")
    leaderboard.record_result("RACE-17A", 3, 200)
    leaderboard.record_result("RACE-17B", 1, 1200)
    assert leaderboard.seed_race_drivers() == ["Ari", "Rina"]


def test_tc_18_assign_mission_with_required_roles_success() -> None:
    registration, crew, _, _, _, missions, _, _ = _build_system()
    registration.register_member("Rina", "driver")
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Rina", "driver")
    crew.assign_role("Miko", "mechanic")
    missions.create_mission("MIS-18", "rescue", ["driver", "mechanic"])
    mission = missions.assign_members("MIS-18", ["Rina", "Miko"])
    assert mission.status == "ready"


def test_tc_19_assign_mission_fails_when_required_role_missing() -> None:
    registration, crew, _, _, _, missions, _, _ = _build_system()
    registration.register_member("Rina", "driver")
    crew.assign_role("Rina", "driver")
    missions.create_mission("MIS-19", "repair", ["driver", "mechanic"])
    with pytest.raises(MissionPlanningError, match="Required roles unavailable: mechanic."):
        missions.assign_members("MIS-19", ["Rina"])


def test_tc_20_maintenance_start_must_not_consume_stock_if_cash_fails() -> None:
    registration, crew, inventory, _, _, _, maintenance, _ = _build_system()
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Miko", "mechanic")
    inventory.add_car("CAR-35", "Ford Mustang")
    inventory.set_car_status("CAR-35", "damaged")
    inventory.add_spare_part("clutch", 1)
    inventory.add_tool("wrench", 1)
    maintenance.create_job("JOB-35", "CAR-35", "Miko", {"clutch": 1}, {"wrench": 1}, 200)
    with pytest.raises(Exception):
        maintenance.start_job("JOB-35")
    assert inventory.get_spare_part_quantity("clutch") == 1
    assert inventory.get_tool_quantity("wrench") == 1


def test_tc_21_mission_cannot_start_if_not_ready() -> None:
    registration, crew, _, _, _, missions, _, _ = _build_system()
    registration.register_member("Ari", "driver")
    crew.assign_role("Ari", "driver")
    missions.create_mission("MIS-21", "delivery", ["driver"])
    with pytest.raises(MissionPlanningError, match="Only ready missions can be started."):
        missions.start_mission("MIS-21")


def test_tc_22_mission_full_lifecycle_ready_active_completed() -> None:
    registration, crew, _, _, _, missions, _, _ = _build_system()
    registration.register_member("Ari", "driver")
    crew.assign_role("Ari", "driver")
    missions.create_mission("MIS-22", "delivery", ["driver"])
    missions.assign_members("MIS-22", ["Ari"])
    active = missions.start_mission("MIS-22")
    completed = missions.complete_mission("MIS-22")
    assert active.status == "active"
    assert completed.status == "completed"


def test_tc_23_mission_assignment_rejects_duplicate_member_entries() -> None:
    registration, crew, _, _, _, missions, _, _ = _build_system()
    registration.register_member("Rina", "driver")
    crew.assign_role("Rina", "driver")
    missions.create_mission("MIS-23", "delivery", ["driver"])
    with pytest.raises(MissionPlanningError, match="Crew member 'Rina' is duplicated in assignment."):
        missions.assign_members("MIS-23", ["Rina", "Rina"])


def test_tc_24_create_maintenance_job_sets_car_to_maintenance() -> None:
    registration, crew, inventory, _, _, _, maintenance, _ = _build_system()
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Miko", "mechanic")
    inventory.add_car("CAR-24", "Subaru BRZ")
    inventory.set_car_status("CAR-24", "damaged")
    job = maintenance.create_job("JOB-24", "CAR-24", "Miko", {"belt": 1}, {"jack": 1}, 100)
    assert job.status == "planned"
    assert inventory.get_car("CAR-24").status == "maintenance"

def test_tc_25_leaderboard_rejects_duplicate_record_for_same_race() -> None:
    registration, crew, inventory, races, _, _, _, leaderboard = _build_system()
    registration.register_member("Ari", "driver")
    crew.assign_role("Ari", "driver")
    inventory.add_car("CAR-36", "Honda Civic")
    races.create_race("RACE-36", "Correction Run", "Ari", "CAR-36")
    races.start_race("RACE-36")
    races.complete_race("RACE-36")
    leaderboard.record_result("RACE-36", 3, 100)
    with pytest.raises(LeaderboardError):
        leaderboard.record_result("RACE-36", 5, 50)


def test_tc_26_maintenance_start_consumes_stock_and_cash() -> None:
    registration, crew, inventory, _, _, _, maintenance, _ = _build_system()
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Miko", "mechanic")
    inventory.add_cash(600)
    inventory.add_car("CAR-26", "Ford Mustang")
    inventory.set_car_status("CAR-26", "damaged")
    inventory.add_spare_part("clutch", 2)
    inventory.add_tool("wrench", 1)
    maintenance.create_job("JOB-26", "CAR-26", "Miko", {"clutch": 1}, {"wrench": 1}, 200)
    maintenance.start_job("JOB-26")
    assert inventory.get_spare_part_quantity("clutch") == 1
    assert inventory.get_tool_quantity("wrench") == 0
    assert inventory.get_cash_balance() == 400


def test_tc_27_assign_mission_fails_with_unregistered_member() -> None:
    registration, crew, _, _, _, missions, _, _ = _build_system()
    registration.register_member("Rina", "driver")
    crew.assign_role("Rina", "driver")
    missions.create_mission("MIS-20", "delivery", ["driver"])
    with pytest.raises(MissionPlanningError, match="Crew member 'Ghost' is not registered."):
        missions.assign_members("MIS-20", ["Ghost"])


def test_tc_28_maintenance_complete_sets_car_ready_and_allows_race() -> None:
    registration, crew, inventory, races, _, _, maintenance, _ = _build_system()
    registration.register_member("Nova", "driver")
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Nova", "driver")
    crew.assign_role("Miko", "mechanic")
    inventory.add_car("CAR-28", "Nissan Z")
    inventory.set_car_status("CAR-28", "damaged")
    inventory.add_tool("jack", 1)
    maintenance.create_job("JOB-28", "CAR-28", "Miko", None, {"jack": 1}, 0)
    maintenance.start_job("JOB-28")
    maintenance.complete_job("JOB-28")
    race = races.create_race("RACE-28", "Rejoin", "Nova", "CAR-28")
    assert race.status == "scheduled"


def test_tc_29_maintenance_create_job_rejects_ready_car() -> None:
    registration, crew, inventory, _, _, _, maintenance, _ = _build_system()
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Miko", "mechanic")
    inventory.add_car("CAR-29", "Audi TT")
    with pytest.raises(VehicleMaintenanceError, match="Car 'CAR-29' does not require maintenance."):
        maintenance.create_job("JOB-29", "CAR-29", "Miko")


def test_tc_30_non_driver_role_blocks_race_entry() -> None:
    registration, crew, inventory, races, _, _, _, _ = _build_system()
    registration.register_member("Kai", "mechanic")
    crew.assign_role("Kai", "mechanic")   
    inventory.add_car("CAR-34", "Toyota AE86")
    with pytest.raises(RaceManagementError, match="Crew member 'Kai' is not a driver."):
        races.create_race("RACE-34", "Conflict Run", "Kai", "CAR-34")


def test_tc_31_race_lifecycle_scheduled_to_active_to_completed() -> None:
    registration, crew, inventory, races, _, _, _, _ = _build_system()
    registration.register_member("Ari", "driver")
    crew.assign_role("Ari", "driver")
    inventory.add_car("CIVIC-01", "Honda Civic")
    races.create_race("RACE-05", "Dockline Rush", "Ari", "CIVIC-01")
    active = races.start_race("RACE-05")
    completed = races.complete_race("RACE-05")
    assert active.status == "active"
    assert completed.status == "completed"


def test_tc_32_duplicate_result_for_same_race_is_rejected() -> None:
    registration, crew, inventory, races, results, _, _, _ = _build_system()
    registration.register_member("Ira", "driver")
    crew.assign_role("Ira", "driver")
    inventory.add_car("M3-01", "BMW M3")
    races.create_race("RACE-10", "Dockline", "Ira", "M3-01")
    races.start_race("RACE-10")
    races.complete_race("RACE-10")
    results.record_result("RACE-10", 2, 500)
    with pytest.raises(ResultsError, match="Result for race 'race-10' is already recorded."):
        results.record_result("race-10", 1, 900)


def test_tc_33_leaderboard_record_result_delegates_to_results() -> None:
    registration, crew, inventory, races, _, _, _, leaderboard = _build_system()
    registration.register_member("Miko", "driver")
    crew.assign_role("Miko", "driver")
    inventory.add_car("NSX-01", "Honda NSX")
    races.create_race("RACE-15", "River Dash", "Miko", "NSX-01")
    races.start_race("RACE-15")
    races.complete_race("RACE-15")
    stats = leaderboard.record_result("RACE-15", 1, 1300)
    assert stats.total_points == 10
    assert stats.total_prize_money == 1300
    assert inventory.get_cash_balance() == 1300


def test_tc_34_maintenance_start_fails_when_tools_insufficient() -> None:
    registration, crew, inventory, _, _, _, maintenance, _ = _build_system()
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Miko", "mechanic")
    inventory.add_car("CAR-27", "Lancer Evo")
    inventory.set_car_status("CAR-27", "damaged")
    inventory.add_tool("torque wrench", 1)
    maintenance.create_job("JOB-27", "CAR-27", "Miko", None, {"torque wrench": 2}, 0)
    with pytest.raises(VehicleMaintenanceError, match="Insufficient tool quantity for 'torque wrench'."):
        maintenance.start_job("JOB-27")


def test_tc_35_inventory_should_not_allow_damaged_to_ready_without_maintenance() -> None:
    _, _, inventory, _, _, _, _, _ = _build_system()
    inventory.add_car("CAR-37", "Nissan Z")
    inventory.set_car_status("CAR-37", "damaged")
    with pytest.raises(InventoryError):
        inventory.set_car_status("CAR-37", "ready")


def test_tc_36_full_chain_race_result_damage_mission_maintenance_new_race() -> None:
    registration, crew, inventory, races, results, missions, maintenance, leaderboard = _build_system()
    registration.register_member("Rina", "driver")
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Rina", "driver")
    crew.assign_role("Miko", "mechanic")
    inventory.add_cash(1000)
    inventory.add_car("CAR-30", "Toyota Supra")
    inventory.add_spare_part("spark plug", 2)
    inventory.add_tool("jack", 1)

    races.create_race("RACE-30A", "First Run", "Rina", "CAR-30")
    races.start_race("RACE-30A")
    races.complete_race("RACE-30A")
    results.record_result("RACE-30A", 2, 500, car_damaged=True)
    leaderboard.sync_result("RACE-30A")

    missions.create_mission("MIS-30", "repair_support", ["driver", "mechanic"])
    missions.assign_members("MIS-30", ["Rina", "Miko"])
    missions.start_mission("MIS-30")
    missions.complete_mission("MIS-30")

    maintenance.create_job("JOB-30", "CAR-30", "Miko", {"spark plug": 1}, {"jack": 1}, 300)
    maintenance.start_job("JOB-30")
    maintenance.complete_job("JOB-30")

    next_race = races.create_race("RACE-30B", "Second Run", "Rina", "CAR-30")
    assert next_race.status == "scheduled"
    assert inventory.get_cash_balance() == 1200
    assert leaderboard.list_rankings()[0].driver_name == "Rina"


def test_tc_37_maintenance_job_rejects_non_mechanic_member() -> None:
    registration, crew, inventory, _, _, _, maintenance, _ = _build_system()
    registration.register_member("Rina", "driver")
    crew.assign_role("Rina", "driver")
    inventory.add_car("CAR-25", "BMW M2")
    inventory.set_car_status("CAR-25", "damaged")
    with pytest.raises(VehicleMaintenanceError, match="Crew member 'Rina' is not a mechanic."):
        maintenance.create_job("JOB-25", "CAR-25", "Rina")


def test_tc_38_record_result_operation_should_be_transactional(monkeypatch: pytest.MonkeyPatch) -> None:
    registration, crew, inventory, races, results, _, _, leaderboard = _build_system()
    registration.register_member("Nia", "driver")
    crew.assign_role("Nia", "driver")
    inventory.add_car("CAR-38", "Honda NSX")
    races.create_race("RACE-38", "Atomic Run", "Nia", "CAR-38")
    races.start_race("RACE-38")
    races.complete_race("RACE-38")
    balance_before = inventory.get_cash_balance()

    def _boom(*_: object, **__: object) -> None:
        raise RuntimeError("forced leaderboard failure")

    monkeypatch.setattr(leaderboard, "_apply_result", _boom)

    with pytest.raises(RuntimeError):
        leaderboard.record_result("RACE-38", 1, 700)

    
    with pytest.raises(ResultsError):
        results.get_result("RACE-38")
    assert inventory.get_cash_balance() == balance_before


def test_tc_39_results_failure_does_not_update_inventory_or_leaderboard() -> None:
    registration, crew, inventory, races, results, _, _, leaderboard = _build_system()
    registration.register_member("Rina", "driver")
    crew.assign_role("Rina", "driver")
    inventory.add_car("CAR-39", "Mazda RX7")
    races.create_race("RACE-39", "Fail Run", "Rina", "CAR-39")
    races.start_race("RACE-39")
    balance_before = inventory.get_cash_balance()
    with pytest.raises(Exception):
        leaderboard.record_result("RACE-39", 1, 500)
    assert inventory.get_cash_balance() == balance_before
    assert leaderboard.list_rankings() == []


def test_tc_40_role_change_after_race_creation_affects_result() -> None:
    registration, crew, inventory, races, results, _, _, _ = _build_system()
    registration.register_member("Kai", "driver")
    crew.assign_role("Kai", "driver")
    inventory.add_car("CAR-40", "Toyota Supra")
    races.create_race("RACE-40", "Role Shift", "Kai", "CAR-40")
    races.start_race("RACE-40")
    races.complete_race("RACE-40")
    crew.assign_role("Kai", "mechanic")
    result = results.record_result("RACE-40", 1, 500)
    assert result.driver_name == "Kai"

def test_tc_41_partial_failure_does_not_consume_inventory() -> None:
    registration, crew, inventory, _, _, _, maintenance, _ = _build_system()
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Miko", "mechanic")
    inventory.add_car("CAR-41", "Nissan Z")
    inventory.set_car_status("CAR-41", "damaged")
    inventory.add_spare_part("filter", 1)
    
    maintenance.create_job("JOB-41", "CAR-41", "Miko", {"filter": 1}, None, 100)
    with pytest.raises(Exception):
        maintenance.start_job("JOB-41")
    assert inventory.get_spare_part_quantity("filter") == 1
    
def test_tc_42_removed_member_breaks_mission_start() -> None:
    
    reg_full = RegistrationModule()
    crew_full = CrewManagementModule(reg_full)
    inv = InventoryModule()
    reg_full.register_member("Rina", "driver")
    crew_full.assign_role("Rina", "driver")
    missions_full = MissionPlanningModule(reg_full, crew_full, inv)
    missions_full.create_mission("MIS-42", "delivery", ["driver"])
    missions_full.assign_members("MIS-42", ["Rina"])

    
    empty_reg = RegistrationModule()
    empty_crew = CrewManagementModule(empty_reg)
    missions_empty = MissionPlanningModule(empty_reg, empty_crew, inv)
    
    missions_empty._missions = missions_full._missions  

    with pytest.raises(Exception):
        missions_empty.start_mission("MIS-42")


def test_tc_43_cannot_start_maintenance_during_active_race() -> None:
    registration, crew, inventory, races, _, _, maintenance, _ = _build_system()
    registration.register_member("Rina", "driver")
    registration.register_member("Miko", "mechanic")
    crew.assign_role("Rina", "driver")
    crew.assign_role("Miko", "mechanic")
    inventory.add_car("CAR-43", "BMW M4")
    races.create_race("RACE-43", "Conflict Run", "Rina", "CAR-43")
    races.start_race("RACE-43")
    with pytest.raises(Exception):
        maintenance.create_job("JOB-43", "CAR-43", "Miko")