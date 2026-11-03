# State in Phase 8

## The problem

An actuator can only perform some actions during each part of its lifecycle. If these rules are spread across routers and React components, one client may allow an action that another client rejects. Several boolean flags can also produce impossible combinations such as running and under maintenance at the same time.

## The solution

`ActuatorContext` is the context. It holds one `ActuatorState` object and asks that state whether a target is legal. The concrete states are `OffState`, `IdleState`, `RunningState`, `ErrorState`, and `MaintenanceState`. Each state owns its legal next states and the command names that are currently allowed. The application service loads the persisted state, asks the context to transition, and saves only after the domain accepts the change.

The API client is not responsible for lifecycle rules. It receives `state` and `allowed_commands` from the device API. The dashboard shows a state badge and lists the allowed commands in its tooltip. Phase 10 can use the same command names instead of reconstructing rules in the UI.

## Legal transitions and commands

| Current state | Legal target states | Allowed commands |
| --- | --- | --- |
| `off` | `idle`, `error` | `power_on`, `report_error` |
| `idle` | `running`, `maintenance`, `error`, `off` | `start`, `enter_maintenance`, `report_error`, `power_off` |
| `running` | `idle`, `error`, `off` | `stop`, `report_error`, `power_off` |
| `error` | `idle`, `maintenance`, `off` | `reset`, `enter_maintenance`, `power_off` |
| `maintenance` | `idle`, `error`, `off` | `finish_maintenance`, `report_error`, `power_off` |

For example, `idle` to `running` is legal, but `running` to `maintenance` is rejected. The domain raises `IllegalTransitionError` before the repository is asked to save, so a rejected request leaves the database unchanged.

## Persistence and API

Migration `8c6e2a1d9f30` creates `actuator_states` with one row per actuator and seeds all existing actuators to `idle`. New actuators receive an `idle` row when their device family is provisioned. The table is keyed by `device_id`, and deleting a device also deletes its lifecycle row.

`GET /api/devices` includes `state` and `allowed_commands`. Sensors use a null state and an empty command list. `POST /api/devices/{device_id}/transition` accepts a target state for the Phase 8 demonstration. A missing actuator returns 404, and an illegal transition returns 409 Conflict.

State objects contain no SQLAlchemy code or HTTP status mapping. The application service coordinates the use case, the repository owns database work, and the router maps domain/application errors to HTTP responses.
