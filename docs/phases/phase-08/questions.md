# Phase 8 — State questions

**Pattern / focus:** State.

**Read first:** [Guide 08](../../materials/guides/08-state.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example support-ticket states) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to actuator lifecycle, persisted state, and `allowed_commands` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of the State pattern in plain language. What problem appears when lifecycle is modelled as boolean flags and scattered `if` guards?

> [!NOTE]
> ***Your Answer***
>
> State lets an object change its behavior based on its current lifecycle state. With separate boolean flags and checks in many files, invalid combinations can appear and the same rule can be handled differently in different places.

2. Name the participants (**context**, **state interface**, **concrete states**, **client**). How does a successful command lead to a **transition**, and where do **guards** live?

> [!NOTE]
> ***Your Answer***
>
> ActuatorContext is the context, ActuatorState is the state interface, and the off, idle, running, error, and maintenance classes are the concrete states. The service is the client that loads the stored state and asks the context to transition. The current state contains the guard that decides if the target is legal.

3. What is `allowed_commands` (or equivalent) for? Why is exposing “what can I do **now**?” better than letting the UI guess from a raw state string?

> [!NOTE]
> ***Your Answer***
>
> allowed_commands lists the operations that are legal in the current state. The backend stays the source of truth, so the UI does not need its own copy of the transition rules and cannot accidentally show an action that the domain would reject.

## B. This phase of the application

4. Which actuator states did you implement (for example idle, running, error)? Sketch the **legal** transitions (which command or event moves idle → running, running → idle, into error, and out of error).

> [!NOTE]
> ***Your Answer***
>
> I implemented off, idle, running, error, and maintenance. Start moves idle to running, stop moves running to idle, and a reported fault can move the normal states into error. Reset moves error back to idle. Maintenance can be entered from idle or error and finished back to idle.

5. Why is actuator state stored in `actuator_states` (or equivalent) rather than only in process memory? What must still be true after you restart the backend?

> [!NOTE]
> ***Your Answer***
>
> Process memory is lost when the backend restarts and different backend processes would not share it. The actuator must still have the same state and allowed commands after a restart, so the state is stored in PostgreSQL by device id.

6. An **illegal** transition must raise a domain error and **must not** update the database. Why? Which HTTP status is reasonable for that case (400 or 409), and why should the rule live in the domain rather than in React?

> [!NOTE]
> ***Your Answer***
>
> Saving an illegal transition would make the stored lifecycle untrustworthy. I return 409 because the request conflicts with the actuator's current state. The guard belongs in the domain so every client follows the same rule, including API callers that do not use the React dashboard.

7. Device JSON gains `state` and `allowed_commands`. How does the dashboard use those fields (badges, disable illegal buttons)? How does this prepare **Phase 10 Command**?

> [!NOTE]
> ***Your Answer***
>
> The dashboard displays the state as a colored badge and shows allowed commands in the badge tooltip. Later controls can display or enable only those commands. Phase 10 can use the same command names and still let the domain verify the transition before execution.

## C. Compare, contrast, and scenarios

8. Contrast State with **Strategy**. Both look like “context delegates to an object.” Who typically **changes** the active object, and is the variation a **lifecycle** or a **selectable policy**? Give a greenhouse example of each (this phase vs Phase 6).

> [!NOTE]
> ***Your Answer***
>
> State changes as the object moves through its lifecycle, usually because the context handles an event or command. Strategy is a policy selected by a client or configuration. The pump changing from idle to running is State, while choosing conservative or aggressive irrigation for a location is Strategy.

9. Contrast State with a pile of booleans (`is_running`, `is_fault`, `is_maintenance`). Why do illegal combinations of flags appear, and how do explicit state objects (or a transition table) prevent that?

> [!NOTE]
> ***Your Answer***
>
> Separate booleans can all be changed independently, so the actuator could become running, faulted, and under maintenance at the same time. One explicit state gives only one valid value, and the transition rules control which value can come next.

10. A classmate puts HTTP status mapping or SQLAlchemy commits **inside** a concrete state class. Another state mutates a flag directly and skips `transition` / `set_state`. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> HTTP and database work inside a state class mixes domain rules with framework details and makes the states harder to test or reuse. Direct flag changes bypass the guards and can create an invalid lifecycle. State classes should describe behavior, while the service, repository, and router handle their own separate jobs.
