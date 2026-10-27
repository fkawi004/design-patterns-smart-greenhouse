# Facade in Phase 7

## The problem

The dashboard overview needs location details, every zone, assigned devices, newest readings, the saved automation strategy, and its current recommendation. Without a facade, an HTTP handler or React component would have to repeat the same coordination across several repositories and services.

## The solution

LocationOverviewFacade gives the dashboard one `get_overview(location_id)` entry point. It hides the location, assigned-device, reading, and saved-strategy subsystems. The overview router calls only this facade, and the frontend receives one complete read DTO from one endpoint.

The facade does not contain irrigation policy or sensor translation. When a strategy key exists, it calls the existing AutomationService evaluate operation and copies its result into the read model. The recommendation is computed again on every overview request, so it reflects current readings and thresholds and is not cached in another table. When there is no saved key, the endpoint still returns 200 with a null strategy and recommendation.

## Query shape

The overview repository loads the location and all zones in one outer-join query, including empty zones. It then loads all devices that have this location id and a non-null zone id in one query. A third query uses a `row_number` window partitioned by device to fetch the newest reading for every assigned device id at once. This avoids a reading query inside the device loop. The existing automation evaluate service may still look up moisture once per zone because Strategy owns that context and decision path; the facade does not duplicate it.

No new table or SQL view was required. The existing `locations`, `zones`, `devices`, `sensor_readings`, and `automation_rules` tables already contain everything needed for this composed read model.

## Main files

- `backend/src/application/overview/dto.py` defines the overview read contract.
- `backend/src/application/overview/facade.py` coordinates the collaborators.
- `backend/src/infrastructure/persistence/overview_repository.py` contains the bounded read queries.
- `backend/src/interfaces/api/overview.py` exposes the single overview route.
- `frontend/src/components/overview/OverviewPanel.tsx` renders the returned snapshot.
