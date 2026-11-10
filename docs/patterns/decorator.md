# Decorator in Phase 9

## The problem

Actuator commands need extra policies without changing the actuator adapter or creating a subclass for every policy combination. The project also needs a database record for every successful or blocked attempt. Putting these checks in the HTTP router would couple the policy to one entry point and would be difficult for Phase 10 commands to reuse.

## The decorator chain

Every component implements the same `ActuatorPort.apply(device_id, command, payload)` method. The chain is composed in `actuator_dependencies.py` in this order:

```text
LoggingActuatorDecorator
  → MaxRunTimeActuatorDecorator
    → SimulationActuatorAdapter
```

`SimulationActuatorAdapter` is the concrete component. `LoggingActuatorDecorator` and `MaxRunTimeActuatorDecorator` are concrete decorators. Because all three present `ActuatorPort`, the application service calls one port without knowing how many wrappers are installed.

The order matters. Logging is outermost, so it records both successful calls and exceptions raised by an inner policy. Max run-time is inside logging, so it can stop the call before the simulation adapter is reached while still allowing the outer logger to persist the failed attempt.

## Max run-time policy

The max-run-time decorator reads the persisted Phase 8 state. It blocks when the actuator is `running` and `actuator_states.updated_at` is at least 30 minutes old. It raises `MaxRunTimeExceededError` and does not call the inner adapter. The decorator does not create its own lifecycle or validate the command string. State remains the lifecycle source of truth, and Phase 10 will decide whether a command is allowed.

## Persisted execution log

Migration `9d4f7c2b8a61` creates `actuator_execution_log`. A successful attempt stores `success=true`, policy `logging`, and a null message. A max-run-time rejection stores `success=false`, policies `maxRunTime` and `logging`, and the message `Max run time exceeded`.

`GET /api/actuators/executions?limit=20` returns recent rows for the dashboard. The small `POST /api/actuators/{device_id}/apply` route demonstrates the decorated port until Phase 10 introduces Command.

## Decorator compared with inheritance

Inheritance would require a new class for each combination such as logging only, max-run-time only, or logging plus max-run-time. Decorator uses composition, so a policy can be added, removed, or reordered without creating another combined subclass. It also keeps persistence and HTTP details outside the concrete actuator adapter.
