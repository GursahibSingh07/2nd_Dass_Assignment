# StreetRace Manager Report: Custom Modules

## Overview
This report documents the two custom modules implemented for the StreetRace Manager system:
1. Vehicle Maintenance Module
2. Leaderboard / Ranking Module

Both modules were designed to match the architecture and coding style of the existing modules (Registration, Crew Management, Inventory, Race Management, Results, Mission Planning). They are stateful, enforce business rules through explicit validation, and integrate with existing module data flows.

## 1. Vehicle Maintenance Module

### File and Public Types
- Module file: `streetrace_manager/vehicle_maintenance.py`
- Public dataclass: `MaintenanceJob`
- Public error type: `VehicleMaintenanceError`
- Public module class: `VehicleMaintenanceModule`

### Purpose
The Vehicle Maintenance Module manages damaged vehicle repair workflows and links technical repair operations with crew roles and inventory resources.

It addresses assignment requirements around:
- damaged cars,
- mechanic role enforcement,
- inventory consumption (parts/tools/cash),
- and lifecycle transitions from damaged to ready.

### Data Model
`MaintenanceJob` stores:
- `job_id`: unique maintenance job identifier
- `car_id`: car being repaired
- `mechanic_name`: assigned mechanic
- `required_parts`: immutable tuple of `(part_name, quantity)`
- `required_tools`: immutable tuple of `(tool_name, quantity)`
- `labor_cost`: maintenance labor expense
- `status`: `planned`, `active`, or `completed`

### Internal State
`VehicleMaintenanceModule` maintains:
- `_jobs: dict[str, MaintenanceJob]` keyed by case-insensitive `job_id`
- References to `RegistrationModule`, `CrewManagementModule`, and `InventoryModule`

### Core Behaviors

#### `create_job(...)`
Creates a new maintenance job with strict checks:
- Validates non-empty `job_id`, `car_id`, and `mechanic_name`
- Rejects duplicate job IDs (case-insensitive)
- Verifies mechanic is registered in Registration
- Verifies mechanic role is `mechanic` in Crew Management
- Verifies target car exists and status is either `damaged` or `maintenance`
- Normalizes and validates required parts/tools dictionaries
- Validates labor cost is non-negative
- Stores job with status `planned`
- Immediately sets car status to `maintenance` in Inventory

#### `start_job(job_id)`
Transitions a planned job to active:
- Only allows `planned` jobs
- Checks required spare parts availability before consumption
- Checks required tools availability before consumption
- Consumes parts and tools from Inventory
- Spends labor cash from Inventory if labor cost > 0
- Updates job status to `active`

#### `complete_job(job_id)`
Finalizes active jobs:
- Only allows `active` jobs
- Sets job status to `completed`
- Sets repaired car status to `ready` in Inventory

#### `get_job(job_id)` and `list_jobs()`
- Retrieves one job by ID with validation and clear error messages
- Lists all jobs sorted case-insensitively by `job_id`

### Validation and Error Rules
Business and input validation is enforced with `VehicleMaintenanceError`:
- Missing IDs/names
- Duplicate jobs
- Unregistered or non-mechanic crew members
- Cars that do not require maintenance
- Invalid requirement structure or quantities
- Insufficient parts/tools
- Invalid lifecycle transitions

### Integration Points
- **Registration Module**: ensures mechanic is registered before assignment
- **Crew Management Module**: enforces mechanic role assignment
- **Inventory Module**:
  - reads and updates car statuses,
  - checks and consumes parts/tools,
  - spends labor cost from cash balance
- **Race/Results Flow Compatibility**:
  - Results can mark cars as damaged,
  - Maintenance returns those cars to ready state for future race eligibility

### Test Coverage
Current validation is covered by the consolidated integration test suite:
- Test file: `tests/test_integration_system.py`
- Relevant maintenance paths: `TC-20`, `TC-24`, `TC-26`, `TC-28`, `TC-29`, `TC-34`, `TC-37`
- Relevant maintenance defect checks (currently failing by design): `TC-10`, `TC-20`

---

## 2. Leaderboard / Ranking Module

### File and Public Types
- Module file: `streetrace_manager/leaderboard.py`
- Public dataclass: `DriverStats`
- Public error type: `LeaderboardError`
- Public module class: `LeaderboardModule`

### Purpose
The Leaderboard Module tracks cumulative driver performance and ranking state over time.

It extends Results by adding persistent, queryable performance statistics and race seeding support.

### Data Model
`DriverStats` stores:
- `driver_name`
- `races`
- `wins`
- `losses`
- `podiums`
- `total_points`
- `best_position`
- `total_prize_money`

### Internal State
`LeaderboardModule` maintains:
- `_stats: dict[str, DriverStats]` keyed by case-insensitive driver name
- `_processed_races: set[str]` to prevent duplicate leaderboard processing
- `_display_names: dict[str, str]` for stable driver display naming
- References to `RegistrationModule`, `ResultsModule`, and `RaceManagementModule`

### Core Behaviors

#### `record_result(race_id, position, prize_money, car_damaged=False)`
- Validates `race_id`
- Prevents duplicate processing for same race in leaderboard context
- Delegates result recording to `ResultsModule.record_result(...)`
- Updates leaderboard stats from the recorded result
- Returns updated `DriverStats`

This method ensures results and rankings can be updated in a single operation.

#### `sync_result(race_id)`
- Used when result is already recorded externally in `ResultsModule`
- Reads existing result via `ResultsModule.get_result(...)`
- Applies leaderboard updates without re-recording the race result
- Prevents duplicate leaderboard processing of the same race

#### `get_driver_stats(member_name)`
- Validates non-empty name and registration
- Returns existing stats if present
- If no stats exist yet, returns a zeroed `DriverStats` baseline for that registered member

#### `list_rankings()`
Returns ranked `DriverStats` sorted by:
1. total points (descending)
2. wins (descending)
3. best position (ascending)
4. driver name (case-insensitive)

#### `seed_race_drivers()`
Builds race driver seeding order from existing races in `RaceManagement` and sorts candidates using leaderboard priority:
1. higher points
2. more wins
3. better best finish
4. alphabetical name

Drivers without leaderboard stats are still seedable, with default lower priority.

### Validation and Error Rules
All leaderboard-specific failures raise `LeaderboardError`:
- missing race ID/member name
- duplicate race processing in leaderboard
- requesting stats for unregistered members

### Integration Points
- **Results Module**:
  - primary source for official race outcomes and points
  - `record_result` wraps results recording and then applies ranking updates
  - `sync_result` imports already-recorded result state
- **Race Management Module**:
  - provides known race participants for seeding logic
- **Registration Module**:
  - ensures only valid registered members are queried for stats

### Test Coverage
Current validation is covered by the consolidated integration test suite:
- Test file: `tests/test_integration_system.py`
- Relevant leaderboard paths: `TC-14`, `TC-16`, `TC-17`, `TC-25`, `TC-33`, `TC-38`
- Relevant leaderboard defect checks (currently failing by design): `TC-25`, `TC-38`

---

## Export and Package Integration
Both modules are exported via `streetrace_manager/__init__.py`.

Added exports:
- Vehicle Maintenance:
  - `MaintenanceJob`
  - `VehicleMaintenanceError`
  - `VehicleMaintenanceModule`
- Leaderboard:
  - `DriverStats`
  - `LeaderboardError`
  - `LeaderboardModule`

This keeps import usage consistent with existing project patterns.

## System-Level Integration Summary
Together, the two custom modules provide a complete extension of race outcomes into operational and competitive state:
- Results can mark cars damaged.
- Vehicle Maintenance consumes inventory resources and restores race readiness.
- Leaderboard accumulates result history into long-term rankings and seeding.

This creates end-to-end flows across core modules:
- `Race Management -> Results -> Vehicle Maintenance -> Race Management`
- `Race Management -> Results -> Leaderboard -> Race seeding decisions`

## Current Integration Test Status
Based on `tests/test_integration_system.py` and `testreport.md`:
- Total integration tests: `38`
- Current result: `30 passed`, `8 failed`
- Failing tests are intentionally spec-driven and distributed across the suite IDs:
  - `TC-05`: mission start with damaged-car mechanic check
  - `TC-10`: duplicate maintenance requirements handling
  - `TC-15`: results driver registration revalidation
  - `TC-20`: maintenance start atomicity on cash failure
  - `TC-25`: leaderboard correction/reprocess support
  - `TC-30`: conflicting role source handling
  - `TC-35`: damaged-to-ready workflow enforcement
  - `TC-38`: transactional integrity across leaderboard/results

These failures are currently expected and document unresolved defects pending explicit fix approval.

## Conclusion
The two custom modules are fully integrated, stateful, and test-backed. They satisfy assignment goals for meaningful module interaction, business rule enforcement, and integration-focused behavior beyond isolated unit logic.
