# Strategy in Phase 6

## The problem

The greenhouse can use different irrigation policies for the same reading. Putting every policy in one router or a large `if/elif` block would mix HTTP handling, database work, and irrigation decisions. It would also make new policies harder to add and test.

## The solution

AutomationStrategy defines one `decide(context)` operation. ConservativeMoistureStrategy irrigates only when moisture is below a zone's low threshold. AggressiveMoistureStrategy starts earlier when moisture is below the high threshold. Both return a recommendation with an action and reason, but they do not start an actuator.

The application service loads the saved strategy key, asks the repository for a plain LocationAutomationContext for every zone, selects the strategy, and runs it. Every context uses the latest reading from a moisture sensor assigned to that exact zone. A zone with no matching reading returns a wait recommendation instead of borrowing another zone's value. The location response is `irrigate` if any zone needs irrigation, and its reason lists every zone decision.

The project uses a dedicated `automation_rules` table because automation settings can grow without adding unrelated columns to locations. Its unique `location_id` keeps one active strategy per location. Existing locations are backfilled with conservative, and new locations receive the same default when they are created.

## Main files

- `backend/src/domain/automation/context.py` contains the plain evaluation context.
- `backend/src/domain/automation/strategy.py` contains the interface and both policies.
- `backend/src/application/automation/service.py` coordinates selection and evaluation.
- `backend/src/infrastructure/persistence/automation_repository.py` loads saved rules, zone thresholds, and latest readings.
- `backend/src/interfaces/api/automation.py` exposes the save and evaluate endpoints.
- `frontend/src/features/automation/StrategyPanel.tsx` provides the dashboard controls.

## Add a third strategy

Create another AutomationStrategy class with a unique key and its own `decide` calculation, then register one instance in `STRATEGIES`. The API, repository, and panel can keep the same contracts; the new key only needs to be added to the frontend dropdown.
