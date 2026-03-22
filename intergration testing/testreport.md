# Integration Test Report

## Execution Summary
- Test file: `tests/test_integration_system.py`
- Total test cases: 43
- Result: 43 passed, 0 failed
- Command: `PYTHONPATH=. pytest -q tests/test_integration_system.py`
- Intent: Validate end-to-end integration behaviour across all modules and confirm that all module interactions function correctly.

---

## Detailed Test Cases

### TC-01
- **Scenario:** Register a valid driver and create a race with a ready car.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management.
- **Input / Preconditions:** Register `Rina` as `driver`; assign crew role `driver`; add car `RX7-01`.
- **Expected Result:** Race is created with status `scheduled`.
- **Actual Result:** Passed. Race was created successfully with the expected status.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Covers the basic happy path where Registration, Crew Management, and Inventory all supply valid data to Race Management. Confirms that all four modules work together under normal conditions.

---

### TC-02
- **Scenario:** Attempt race creation with an unregistered driver.
- **Modules Involved:** Inventory, Race Management, Registration.
- **Input / Preconditions:** Car exists; member `Ghost` is not registered.
- **Expected Result:** `RaceManagementError` with message "Crew member 'Ghost' is not registered."
- **Actual Result:** Passed. The expected error was raised.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Ensures Race Management correctly queries Registration before allowing a race to be created. A race must never be created with an unknown crew member.

---

### TC-03
- **Scenario:** Registered non-driver tries to enter a race.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management.
- **Input / Preconditions:** `Miko` registered and assigned `mechanic`; car is ready.
- **Expected Result:** Race creation rejected with message "Crew member 'Miko' is not a driver."
- **Actual Result:** Passed. Role validation behaved as expected.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that Race Management reads the effective role from Crew Management and enforces the business rule that only drivers may race.

---

### TC-04
- **Scenario:** Driver attempts a race using a damaged car.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management.
- **Input / Preconditions:** Driver valid; car status set to `damaged` via Inventory.
- **Expected Result:** Race creation rejected with message "Car 'GTR-01' is not ready for racing."
- **Actual Result:** Passed. The system correctly blocked the race.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Checks that Race Management reads car status from Inventory before scheduling. A damaged car must not be entered into a race.

---

### TC-05
- **Scenario:** Mechanic-required mission should not start while a damaged car exists (for non-repair mission types).
- **Modules Involved:** Registration, Crew Management, Inventory, Mission Planning.
- **Input / Preconditions:** Driver and mechanic registered and assigned; one damaged car in Inventory; mission type is `rescue`.
- **Expected Result:** `start_mission` raises `MissionPlanningError`.
- **Actual Result:** Passed. Mission start was correctly prevented.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that `_has_available_mechanic` in Mission Planning queries Inventory for damaged cars and blocks non-repair missions when a mechanic may be needed for repairs. Repair-type missions (`repair`, `repair_support`, `maintenance`) are exempt from this check by design.

---

### TC-06
- **Scenario:** Attempt to start the same race twice.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management.
- **Input / Preconditions:** Race already started once.
- **Expected Result:** Second start attempt rejected with "Only scheduled races can be started."
- **Actual Result:** Passed. Second attempt was correctly rejected.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Verifies that Race Management enforces correct state transitions. A race that is already active cannot be started again.

---

### TC-07
- **Scenario:** Complete a race before it has been started.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management.
- **Input / Preconditions:** Race is in `scheduled` state.
- **Expected Result:** Completion rejected with "Only active races can be completed."
- **Actual Result:** Passed. Proper error was raised.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Ensures the lifecycle order (scheduled → active → completed) is strictly enforced by Race Management.

---

### TC-08
- **Scenario:** Member role is reassigned to driver before race entry.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management.
- **Input / Preconditions:** `Kai` initially assigned `mechanic`, then reassigned `driver`; ready car available.
- **Expected Result:** Race creation succeeds under the updated role.
- **Actual Result:** Passed. Role update was reflected correctly in Race Management.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that Crew Management role changes propagate immediately into Race Management validation. When both the registration role and the crew role are updated consistently, race entry is permitted.

---

### TC-09
- **Scenario:** Completed race result updates driver points and cash balance.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Results.
- **Input / Preconditions:** Completed race; position `1`; prize `1000`.
- **Expected Result:** 10 points awarded to driver; cash balance in Inventory increases by 1000.
- **Actual Result:** Passed. Points and cash were updated as expected.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Core integration test between Results and Inventory. Validates that prize money flows from Results into Inventory cash and that points are correctly stored in the rankings.

---

### TC-10
- **Scenario:** Duplicate (case-insensitive) requirement keys in a maintenance job are rejected.
- **Modules Involved:** Registration, Crew Management, Inventory, Vehicle Maintenance.
- **Input / Preconditions:** Requirements dict contains `{"bolt": 1, "BOLT": 2}`.
- **Expected Result:** `VehicleMaintenanceError` raised for the duplicated key.
- **Actual Result:** Passed. Duplicate keys were correctly rejected.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms Vehicle Maintenance normalises requirement keys to lowercase before insertion and raises an error on collision, preventing ambiguous part quantities from being stored.

---

### TC-11
- **Scenario:** Result cannot be recorded for a race that has not been completed.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Results.
- **Input / Preconditions:** Race created but not started or completed.
- **Expected Result:** `ResultsError` with message "Race 'RACE-11' is not completed."
- **Actual Result:** Passed. Error was raised correctly.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Verifies that Results queries Race Management for the race status before recording an outcome. Out-of-order result recording is correctly blocked.

---

### TC-12
- **Scenario:** Car marked damaged during a race blocks that car from the next race.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Results.
- **Input / Preconditions:** Race completed; `car_damaged=True` passed to `record_result`.
- **Expected Result:** Inventory shows car as `damaged`; subsequent race creation for that car fails.
- **Actual Result:** Passed. Car status updated and next race blocked.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Validates the cross-module chain: Results writes damage status to Inventory, and Race Management later reads that status to block the car. Three modules interact in sequence.

---

### TC-13
- **Scenario:** Zero prize race still awards points but does not change cash balance.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Results.
- **Input / Preconditions:** Completed race; position `2`; prize `0`.
- **Expected Result:** 6 points awarded; cash balance remains 0.
- **Actual Result:** Passed. Points and cash behaved correctly.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that Results correctly separates point calculation from cash updates, and that Inventory is not modified when prize money is zero.

---

### TC-14
- **Scenario:** Leaderboard syncs correctly from an existing Results entry.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Results, Leaderboard.
- **Input / Preconditions:** Result already recorded in Results module; leaderboard has not processed this race.
- **Expected Result:** `sync_result` returns stats with 10 points and 1 win.
- **Actual Result:** Passed. Stats were correctly read from Results and applied to Leaderboard.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Tests the Leaderboard's `sync_result` path, confirming it reads from an already-recorded Results entry and correctly updates internal driver stats without re-recording.

---

### TC-15
- **Scenario:** Result recording checks that the driver is still registered at time of recording.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Results.
- **Input / Preconditions:** Race completed in a fully populated system; Results module is wired to an empty Registration (simulating a removed member).
- **Expected Result:** `ResultsError` raised because the driver is not found in Registration.
- **Actual Result:** Passed. Error was raised correctly.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that Results validates driver registration at the point of recording. The test wires a Results instance to a separate empty Registration to simulate the member being absent, without accessing private module state.

---

### TC-16
- **Scenario:** Leaderboard rejects a duplicate `record_result` call that is not an improvement (case-insensitive race ID).
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Leaderboard.
- **Input / Preconditions:** First call records `RACE-16` at position `2`, prize `500`. Second call uses `race-16` (lowercase) with position `3`, prize `100` — worse on both dimensions.
- **Expected Result:** `LeaderboardError` with message "Leaderboard already processed race 'race-16'."
- **Actual Result:** Passed. Duplicate was rejected.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that Leaderboard uses case-insensitive race keys and rejects a second `record_result` call when the new result is not an improvement on either position or prize. Since position `3 > 2` and prize `100 < 500`, `is_improved` evaluates to `False` and the error is raised.

---

### TC-17
- **Scenario:** Leaderboard seed ordering places higher-scoring drivers first.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Leaderboard.
- **Input / Preconditions:** Two drivers race separately; Ari finishes 1st (10 pts), Rina finishes 3rd (4 pts).
- **Expected Result:** `seed_race_drivers()` returns `["Ari", "Rina"]`.
- **Actual Result:** Passed. Ordering was correct.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Validates that Leaderboard reads race data from Race Management and driver stats from its own internal store, then sorts correctly by total points descending.

---

### TC-18
- **Scenario:** Mission assignment succeeds when all required roles are covered.
- **Modules Involved:** Registration, Crew Management, Mission Planning.
- **Input / Preconditions:** Driver and mechanic both registered and assigned correct roles.
- **Expected Result:** Mission status becomes `ready` after assignment.
- **Actual Result:** Passed. Assignment succeeded.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Happy-path integration between Registration, Crew Management, and Mission Planning. Confirms role lookup flows correctly through all three modules.

---

### TC-19
- **Scenario:** Mission assignment fails when a required role is not covered by the assigned members.
- **Modules Involved:** Registration, Crew Management, Mission Planning.
- **Input / Preconditions:** Mission requires driver and mechanic; only a driver is assigned.
- **Expected Result:** `MissionPlanningError` with message "Required roles unavailable: mechanic."
- **Actual Result:** Passed. Correct error raised.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Verifies that Mission Planning cross-checks assigned member roles from Crew Management against the mission's required roles, and rejects the assignment if any role is missing.

---

### TC-20
- **Scenario:** Maintenance start does not consume parts or tools when cash is insufficient.
- **Modules Involved:** Registration, Crew Management, Inventory, Vehicle Maintenance.
- **Input / Preconditions:** Parts and tools in stock; no cash balance; job with non-zero labour cost.
- **Expected Result:** `VehicleMaintenanceError` raised; spare part and tool quantities unchanged.
- **Actual Result:** Passed. Inventory was not modified after the failure.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that `start_job` validates cash availability before consuming any Inventory stock, ensuring no partial deduction occurs when a job cannot be fully funded.

---

### TC-21
- **Scenario:** Mission cannot be started before members are assigned (still in `planned` state).
- **Modules Involved:** Registration, Crew Management, Mission Planning.
- **Input / Preconditions:** Mission created but `assign_members` never called.
- **Expected Result:** `MissionPlanningError` with message "Only ready missions can be started."
- **Actual Result:** Passed. Correct error raised.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that Mission Planning enforces the correct state progression: a mission must pass through `ready` before it can become `active`.

---

### TC-22
- **Scenario:** Full mission lifecycle runs from planned through to completed.
- **Modules Involved:** Registration, Crew Management, Mission Planning.
- **Input / Preconditions:** Driver registered and assigned; mission created and members assigned.
- **Expected Result:** `start_mission` returns status `active`; `complete_mission` returns status `completed`.
- **Actual Result:** Passed. All state transitions completed correctly.
- **Errors / Logical Issues Found:** None.
- **Explanation:** End-to-end test of the Mission Planning lifecycle, confirming that each state transition is correctly applied and persisted.

---

### TC-23
- **Scenario:** Mission assignment rejects the same member listed twice.
- **Modules Involved:** Registration, Crew Management, Mission Planning.
- **Input / Preconditions:** Single registered driver; `assign_members` called with `["Rina", "Rina"]`.
- **Expected Result:** `MissionPlanningError` with message "Crew member 'Rina' is duplicated in assignment."
- **Actual Result:** Passed. Duplicate was correctly rejected.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that Mission Planning validates member uniqueness during assignment, preventing the same person from filling multiple role slots in one mission.

---

### TC-24
- **Scenario:** Creating a maintenance job sets the car's Inventory status to `maintenance`.
- **Modules Involved:** Registration, Crew Management, Inventory, Vehicle Maintenance.
- **Input / Preconditions:** Mechanic registered; damaged car in Inventory.
- **Expected Result:** Job status is `planned`; car status in Inventory is `maintenance`.
- **Actual Result:** Passed. Both statuses were set correctly.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Validates the cross-module side effect: when Vehicle Maintenance creates a job, it immediately updates the car's status in Inventory to prevent conflicting operations on the same car.

---

### TC-25
- **Scenario:** Leaderboard rejects a duplicate `record_result` call that is not an improvement.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Leaderboard.
- **Input / Preconditions:** First result recorded at position `3`, prize `100`; second call uses position `5`, prize `50` (worse on both dimensions).
- **Expected Result:** `LeaderboardError` raised on the second call because the result is not an improvement.
- **Actual Result:** Passed. Duplicate was rejected.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Leaderboard's `record_result` allows a correction only when the new result is strictly better (lower position number or higher prize). When both values are worse, `is_improved` evaluates to `False` and the call is rejected with a `LeaderboardError`.

---

### TC-26
- **Scenario:** Starting a maintenance job correctly deducts parts, tools, and cash from Inventory.
- **Modules Involved:** Registration, Crew Management, Inventory, Vehicle Maintenance.
- **Input / Preconditions:** 600 cash, 2 clutch parts, 1 wrench in Inventory; job requires 1 clutch, 1 wrench, 200 labour.
- **Expected Result:** After `start_job`: 1 clutch remaining, 0 wrenches, 400 cash.
- **Actual Result:** Passed. All deductions were applied correctly.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Validates the full deduction flow from Vehicle Maintenance into Inventory, confirming parts, tools, and cash are all correctly consumed when a job starts.

---

### TC-27
- **Scenario:** Mission assignment fails when an unregistered member is provided.
- **Modules Involved:** Registration, Crew Management, Mission Planning.
- **Input / Preconditions:** `Ghost` is not registered; mission requires a driver.
- **Expected Result:** `MissionPlanningError` with message "Crew member 'Ghost' is not registered."
- **Actual Result:** Passed. Correct error raised.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms Mission Planning checks Registration for each member during assignment, not just at mission creation time.

---

### TC-28
- **Scenario:** Completed maintenance job sets the car to `ready`, allowing it to re-enter a race.
- **Modules Involved:** Registration, Crew Management, Inventory, Vehicle Maintenance, Race Management.
- **Input / Preconditions:** Car damaged; job created, started, and completed by mechanic.
- **Expected Result:** Car status is `ready`; Race Management accepts the car for a new race.
- **Actual Result:** Passed. Car was restored and race was created successfully.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Key integration test spanning Vehicle Maintenance, Inventory, and Race Management. Confirms the full repair cycle restores a car to race-ready condition.

---

### TC-29
- **Scenario:** Maintenance job cannot be created for a car that is already in `ready` status.
- **Modules Involved:** Registration, Crew Management, Inventory, Vehicle Maintenance.
- **Input / Preconditions:** Car is in `ready` status.
- **Expected Result:** `VehicleMaintenanceError` with message "Car 'CAR-29' does not require maintenance."
- **Actual Result:** Passed. Correct error raised.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms Vehicle Maintenance reads car status from Inventory and rejects unnecessary jobs, preventing maintenance from being scheduled on undamaged vehicles.

---

### TC-30
- **Scenario:** Member with only a mechanic role cannot enter a race.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management.
- **Input / Preconditions:** `Kai` registered as `mechanic` and crew-assigned as `mechanic`; ready car available.
- **Expected Result:** Race creation raises `RaceManagementError` with message "Crew member 'Kai' is not a driver."
- **Actual Result:** Passed. Race creation correctly rejected.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that Race Management reads the crew role from Crew Management and enforces the driver-only restriction. When both the registration role and the crew role agree on `mechanic`, race entry is correctly denied.

---

### TC-31
- **Scenario:** Full race lifecycle transitions from scheduled to active to completed.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management.
- **Input / Preconditions:** Driver and ready car exist; race created.
- **Expected Result:** `start_race` returns status `active`; `complete_race` returns status `completed`.
- **Actual Result:** Passed. All transitions applied correctly.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that Race Management state transitions work correctly end-to-end when all supporting modules supply valid data.

---

### TC-32
- **Scenario:** Duplicate result recording for the same race is rejected (case-insensitive key).
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Results.
- **Input / Preconditions:** Result already recorded for `RACE-10`; second attempt uses `race-10`.
- **Expected Result:** `ResultsError` with message "Result for race 'race-10' is already recorded."
- **Actual Result:** Passed. Duplicate was rejected.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms Results uses case-insensitive deduplication for race IDs, preventing the same race outcome from being recorded twice under different casings.

---

### TC-33
- **Scenario:** `Leaderboard.record_result` delegates to Results and the prize updates Inventory cash.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Results, Leaderboard.
- **Input / Preconditions:** Completed race; position `1`; prize `1300`.
- **Expected Result:** Leaderboard stats show 10 points and 1300 prize; Inventory cash balance is 1300.
- **Actual Result:** Passed. All three modules updated correctly.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Validates that the Leaderboard correctly delegates result recording to Results, which in turn updates Inventory. Three modules update in the correct order from a single Leaderboard call.

---

### TC-34
- **Scenario:** Maintenance start fails when the required tool quantity is insufficient.
- **Modules Involved:** Registration, Crew Management, Inventory, Vehicle Maintenance.
- **Input / Preconditions:** Only 1 torque wrench in Inventory; job requires 2.
- **Expected Result:** `VehicleMaintenanceError` with message "Insufficient tool quantity for 'torque wrench'."
- **Actual Result:** Passed. Correct error raised.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms Vehicle Maintenance reads tool quantities from Inventory before consuming them, and blocks job start when stock is insufficient.

---

### TC-35
- **Scenario:** Inventory does not allow a direct transition from `damaged` to `ready` (boundary guard test).
- **Modules Involved:** Inventory.
- **Input / Preconditions:** Car status is `damaged`.
- **Expected Result:** `InventoryError` raised when attempting to set status directly to `ready`.
- **Actual Result:** Passed. Transition blocked correctly.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Boundary guard confirming Inventory enforces the rule that a damaged car must pass through `maintenance` status before returning to `ready`. This prevents any module from bypassing the Vehicle Maintenance repair workflow by writing directly to Inventory.

---

### TC-36
- **Scenario:** Full end-to-end chain across all modules: race → damage → mission → maintenance → new race.
- **Modules Involved:** All modules.
- **Input / Preconditions:** Driver and mechanic registered; 1000 cash, spare parts, and tools in Inventory.
- **Expected Result:** After race, mission, and repair: new race scheduled; cash is 1200; Rina leads leaderboard.
- **Actual Result:** Passed. All assertions held.
- **Errors / Logical Issues Found:** None.
- **Explanation:** The most comprehensive integration test in the suite. Validates that all eight modules interact correctly in sequence and that shared state (cash, car status, points) is consistent throughout the entire workflow.

---

### TC-37
- **Scenario:** Maintenance job creation is rejected when the assigned crew member is not a mechanic.
- **Modules Involved:** Registration, Crew Management, Inventory, Vehicle Maintenance.
- **Input / Preconditions:** `Rina` registered and assigned as `driver`; damaged car exists.
- **Expected Result:** `VehicleMaintenanceError` with message "Crew member 'Rina' is not a mechanic."
- **Actual Result:** Passed. Correct error raised.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms Vehicle Maintenance reads the crew role from Crew Management and enforces that only mechanics may be assigned to maintenance jobs.

---

### TC-38
- **Scenario:** Leaderboard `record_result` rolls back fully if `_apply_result` raises an exception.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Results, Leaderboard.
- **Input / Preconditions:** Completed race; `_apply_result` monkeypatched to raise `RuntimeError`.
- **Expected Result:** After crash: `results.get_result` raises `ResultsError` (result rolled back); Inventory cash balance unchanged.
- **Actual Result:** Passed. Rollback confirmed across Results and Inventory.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Validates transactional integrity across three modules. The Leaderboard's `record_result` calls `results.record_result` first (which also updates Inventory cash), then `_apply_result`. If the latter raises, the rollback path calls `results.remove_result`, which reverses the Results write and restores the Inventory cash balance, leaving all three modules in a clean state.

---

### TC-39
- **Scenario:** Recording a result for a race that is not yet completed prevents Inventory and Leaderboard from updating.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Results, Leaderboard.
- **Input / Preconditions:** Race is `active` (not completed); `leaderboard.record_result` is called.
- **Expected Result:** Exception raised; Inventory cash balance unchanged; Leaderboard rankings empty.
- **Actual Result:** Passed. No state was changed after the failure.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that the Results module's completion check blocks the entire downstream update chain — neither Inventory nor Leaderboard are modified when the race has not been properly finished.

---

### TC-40
- **Scenario:** Changing a crew member's role after a race is created does not affect the recorded result.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Results.
- **Input / Preconditions:** Race created and completed with `Kai` as driver; role then changed to `mechanic`.
- **Expected Result:** Result still records `Kai` as the driver.
- **Actual Result:** Passed. Result was unaffected by the role change.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that race and result records snapshot the driver name at creation/completion time and are not retroactively altered by subsequent Crew Management changes.

---

### TC-41
- **Scenario:** Maintenance job failure due to insufficient cash does not consume spare parts from Inventory.
- **Modules Involved:** Registration, Crew Management, Inventory, Vehicle Maintenance.
- **Input / Preconditions:** 1 filter part in Inventory; no cash balance; job requires 1 filter and 100 labour cost.
- **Expected Result:** Exception raised; filter quantity in Inventory remains 1.
- **Actual Result:** Passed. Parts were not consumed.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that `start_job` checks cash balance before consuming any Inventory resources. Since the cash check fails first, no parts or tools are deducted, leaving Inventory in a clean state.

---

### TC-42
- **Scenario:** Mission start validates that assigned members are still registered at runtime.
- **Modules Involved:** Registration, Crew Management, Mission Planning.
- **Input / Preconditions:** Mission assigned to `Rina`; at start time the module is wired to an empty Registration, simulating a member that is no longer present.
- **Expected Result:** `MissionPlanningError` raised because the assigned member is not found in Registration.
- **Actual Result:** Passed. Exception was raised correctly.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that Mission Planning re-validates member registration inside `start_mission`, not only at `assign_members`. The test wires a separate MissionPlanning instance to an empty Registration to simulate this condition without accessing private state.

---

### TC-43
- **Scenario:** Maintenance job cannot be created for a car that is currently in an active race.
- **Modules Involved:** Registration, Crew Management, Inventory, Race Management, Vehicle Maintenance.
- **Input / Preconditions:** Race started with `CAR-43`; car status remains `ready` in Inventory since Race Management does not change car status when a race starts.
- **Expected Result:** `VehicleMaintenanceError` raised because the car is not in `damaged` or `maintenance` status.
- **Actual Result:** Passed. Job creation was blocked.
- **Errors / Logical Issues Found:** None.
- **Explanation:** Confirms that Vehicle Maintenance reads the current car status from Inventory and refuses to create a job for a car that does not require repair, preventing maintenance from being scheduled on a car that is actively racing.

---

## Overall Findings
- **Failing tests:** None.
- **Passed tests:** All 43 integration test cases.
- **Current state:** All module interactions function correctly. No errors or logical issues were detected during integration testing.

---

## Key Integration Scenarios Verified

| TC | Integration Scenario | Modules Crossed |
|----|---------------------|-----------------|
| TC-01 | Driver registered and race created end-to-end | Registration → Crew Management → Inventory → Race Management |
| TC-05 | Damaged car blocks mechanic-required non-repair mission | Mission Planning → Inventory |
| TC-09 | Race result updates driver points and cash balance | Results → Inventory |
| TC-12 | Car damage from result blocks the same car in the next race | Results → Inventory → Race Management |
| TC-20 | Cash validated before parts and tools are consumed in maintenance | Vehicle Maintenance → Inventory |
| TC-25 | Non-improving duplicate result rejected by leaderboard | Leaderboard (improvement check) → Results |
| TC-28 | Full repair cycle restores car to race-ready condition | Vehicle Maintenance → Inventory → Race Management |
| TC-33 | Leaderboard delegates result recording and prize flows to Inventory | Leaderboard → Results → Inventory |
| TC-36 | Full eight-module end-to-end chain | All modules |
| TC-38 | Leaderboard rollback undoes Results write and Inventory cash on failure | Leaderboard → Results → Inventory (rollback) |