# Phase 10 — Command questions

**Pattern / focus:** Command.

**Read first:** [Guide 10](../../materials/guides/10-command.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example editor undo commands) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to command objects, the invoker, `command_log`, and the controls UI from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Command in plain language. What does it mean to **objectify a request**, and what can you do with that object that you cannot do with a bare `actuator.start()` call (queue, audit, undo, history)?

> [!NOTE]
> **_Your Answer_**
>
> Command changes an action request into an object with its own data and execute method. The object can be stored, queued, logged, retried, or possibly undone later. A direct actuator.start call performs the action immediately but does not give the application a request object to manage or keep in history.

2. Name the participants (**command**, **receiver**, **invoker**, **client**). Who creates the command, who triggers `execute()`, and who actually changes actuator/hardware state?

> [!NOTE]
> **_Your Answer_**
>
> StartPumpCommand, StopPumpCommand, and SetLightLevelCommand are the concrete commands. The command service is the client that asks the registry to create one, CommandInvoker triggers execute, and the decorated ActuatorPort is the receiver that finally reaches the simulation adapter. The service updates the stored lifecycle state after the receiver completes.

3. If a command supports undo, when must it capture the data needed to reverse the action? Why is “capture **before** mutate” critical?

> [!NOTE]
> **_Your Answer_**
>
> It must save the previous value or state before it changes anything. After the change, the old information might already be lost, so the command would not know what value it should restore during undo.

## B. This phase of the application

4. Which command types did you implement (for example `start_pump`, `stop_pump`, `set_light_level`)? Why does the HTTP handler create a command and pass it to an **invoker** (or application service) instead of calling the actuator adapter from the router?

> [!NOTE]
> **_Your Answer_**
>
> I implemented start_pump, stop_pump, and set_light_level. The route passes the request to the command service, where the invoker creates and runs the correct object from a registry. This keeps state checks, decorators, state updates, and logging in one reusable workflow instead of spreading them through HTTP code.

5. Walk through the execute path: (1) consult State / `allowed_commands`, (2) if illegal → **rejected**, (3) if legal → decorated `apply`, update `actuator_states`, log **success** or **failed**. Why must a rejected command **not** change actuator state and **not** reach inner `apply`?

> [!NOTE]
> **_Your Answer_**
>
> The service loads the saved state and checks whether the command type is allowed. An illegal request is saved as rejected and stops there. A legal request goes through the logging and max-run-time decorators, then its target state is saved only after apply succeeds. A rejected request must not reach apply or change state because State has already decided that the action is not valid from the current lifecycle state.

6. Distinguish **`rejected`** vs **`failed`** vs **`success`** in `command_log`. Give one greenhouse example of each. Why is “illegal in this state” not the same as “policy or adapter error after the command was accepted”?

> [!NOTE]
> **_Your Answer_**
>
> Rejected means the request was not legal, such as stopping a pump that is already idle. Failed means it was accepted by State but a later policy or adapter stopped it, such as the max-run-time policy returning an error. Success means the adapter completed and any required state transition was saved. Rejection happens before execution, while failure happens after the application has accepted the request for execution.

7. Why is `command_log` a **different** table from Phase 9 `actuator_execution_log`? What concern does each log record (operator intent vs policy/adapter attempt)?

> [!NOTE]
> **_Your Answer_**
>
> command_log records what command was requested, its payload, and the final result seen by the application. actuator_execution_log records the lower-level attempt through logging, policies, and the adapter. A rejected command appears only in command_log because it never reaches the decorated port.

## C. Compare, contrast, and scenarios

8. Contrast Command with **Strategy**. Strategy is an interchangeable **algorithm** (decide / quote). Command is a **side-effectful request** with history. How do they cooperate in this app (Phase 6 recommends; Phase 10 executes)?

> [!NOTE]
> **_Your Answer_**
>
> Strategy chooses an algorithm for deciding whether irrigation is recommended. It does not directly operate the actuator. Command represents the actual request that performs an action and creates history. The Phase 6 strategy can recommend irrigation, and a Phase 10 start_pump command can carry out that recommendation.

9. Contrast Command with **State**. Who **triggers** the action, and who **decides whether it is legal**? Why must commands not bypass state guards?

> [!NOTE]
> **_Your Answer_**
>
> A user or another application feature triggers a command, while the current State decides if that command is allowed. Commands must use the guard because performing an illegal action could make the hardware behavior and persisted lifecycle disagree.

10. The controls UI should disable actions that are not in `allowed_commands`. Why must the **backend** still reject illegal commands even if the UI is correct? What happens if a classmate’s command calls the raw adapter and skips State and Decorator?

> [!NOTE]
> **_Your Answer_**
>
> The browser is not a security or correctness boundary because someone can call the API directly or use an old page. The backend must always check the saved state again. Calling the raw adapter would allow illegal actions and would also skip max-run-time protection and the Phase 9 execution log.
