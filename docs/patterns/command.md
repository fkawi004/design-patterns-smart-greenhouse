# Command in Phase 10

## Intent

Command turns an actuator request into an object. Each object stores the target device and payload and provides the same `execute(port)` operation. This lets the application validate, execute, and audit requests without putting start, stop, and light-level branches in the HTTP router.

## Participants

- `Command` is the common interface.
- `StartPumpCommand`, `StopPumpCommand`, and `SetLightLevelCommand` are concrete commands.
- `CommandInvoker` uses a registry to create the requested command class and calls `execute` without branching on the command type.
- The decorated `ActuatorPort` is the receiver. It applies logging and max-run-time policies before the simulation adapter.
- `CommandService` is the application client that coordinates State, the invoker, and persistence.

## Execution path

The service creates the command through the registry and loads the persisted actuator state. If the command type is not in `allowed_commands`, it writes a `rejected` command row and stops before the actuator port or state repository is called.

A legal command runs through this stack:

```text
CommandInvoker
  → concrete Command.execute
    → LoggingActuatorDecorator
      → MaxRunTimeActuatorDecorator
        → SimulationActuatorAdapter
```

After a completed apply, the service uses `ActuatorContext.transition` when the command has a different target state. Starting a pump moves `idle` to `running`, stopping moves `running` to `idle`, and setting a level on an already running light does not make an unnecessary transition.

If a decorator or adapter raises an error, the command is `failed` and the state stays unchanged. The Phase 9 decorator still writes its own execution attempt. A completed command is stored as `success`.

## Audit history

Migration `a7f3c1d5e902` creates `command_log` with the command type, device, payload, status, error, and time. `command_log` records the operator request and its outcome. Phase 9 `actuator_execution_log` separately records what happened while policies and the adapter tried to apply an accepted request.

`POST /api/commands` executes one registered command and `GET /api/commands?limit=50` returns newest history first. The dashboard controls use each actuator's `allowed_commands`, then refresh the actuator state and command history after a request.

## Why not call the port from the router

Calling the port directly from the router would duplicate state guards, state updates, and audit rules in every entry point. Command objects keep each request reusable, and the application service provides one ordered workflow that a future scheduler or observer can call without copying HTTP code.
