# Phase 9 — Decorator questions

**Pattern / focus:** Decorator.

**Read first:** [Guide 09](../../materials/guides/09-decorator.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example HTTP client wrappers) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to `ActuatorPort`, policy decorators, and `actuator_execution_log` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Decorator in plain language. Why is stacking wrappers a flexible alternative to a combinatorial explosion of subclasses (`LoggingRetryMaxRuntimeActuator`, …)?

> [!NOTE]
> ***Your Answer***
>
> Decorator adds behavior by wrapping an object that keeps the same interface. Wrappers can be combined or removed when needed, so I do not need a separate subclass for every possible group of policies.

2. Name the participants (**component**, **concrete component**, **decorator**, **concrete decorators**). What interface does every decorator present to the caller, and why must that match the wrapped component?

> [!NOTE]
> ***Your Answer***
>
> ActuatorPort is the component interface and SimulationActuatorAdapter is the concrete component. The logging and max-run-time classes are concrete decorators around that component. They all provide the same apply method, which lets the caller use the complete chain like one normal actuator port.

3. **Order matters.** Using logging and retry (or logging and max-run-time) as an example, explain how wrapping A around B can change what you observe compared with wrapping B around A.

> [!NOTE]
> ***Your Answer***
>
> An outer wrapper sees everything that happens inside it. Logging is outside max run-time in my chain, so it records both accepted calls and policy rejections. If logging was inside the blocking policy, a rejected call would never reach logging and the failed attempt would be missing.

## B. This phase of the application

4. What is `ActuatorPort` here, and which **at least two** decorators did you stack around the real adapter (for example logging and max run-time)? Where is the chain wired (composition root / factory), and why not inside the HTTP router?

> [!NOTE]
> ***Your Answer***
>
> ActuatorPort is the shared interface for applying a command to a device. I wrapped SimulationActuatorAdapter with MaxRunTimeActuatorDecorator and then LoggingActuatorDecorator. The chain is built in the API dependency composition file, not in the router, so other entry points can reuse the same configured port without copying policy logic.

5. Max run-time can **short-circuit**: the inner adapter is never called. Why must a blocked attempt still produce a row in `actuator_execution_log` with `success=false` and the policy named in `policy_applied`?

> [!NOTE]
> ***Your Answer***
>
> A blocked request is still an important attempt that the user should be able to see and investigate. Saving success=false with maxRunTime shows that the adapter did not fail randomly. It was intentionally stopped by a known policy.

6. How does max run-time know the actuator has been running too long (for example `actuator_states.updated_at` from Phase 8)? Why is that data from **State**, not something the decorator should invent as a second lifecycle?

> [!NOTE]
> ***Your Answer***
>
> The decorator reads the stored actuator state and compares its updated_at value with the current time. If running started at least 30 minutes ago, it blocks the call. Phase 8 State already owns the lifecycle, so creating another running flag or timer inside the decorator could disagree with the database.

7. `GET /api/actuators/executions` feeds the dashboard execution log. Why persist attempts in the database instead of only printing to stdout? What should the UI show after a blocked attempt and a refresh?

> [!NOTE]
> ***Your Answer***
>
> Database rows remain available after a restart and can be queried by the API, while console output can disappear or be difficult for users to access. After a blocked attempt, the UI shows a blocked result, the maxRunTime and logging policies, and the message Max run time exceeded.

## C. Compare, contrast, and scenarios

8. Contrast Decorator with **Adapter**. Both wrap. One **keeps** the interface and **adds** behaviour; the other **changes** the interface and **translates**. Which is which in this greenhouse (Phase 9 vs Phase 5)?

> [!NOTE]
> ***Your Answer***
>
> Decorator keeps ActuatorPort and adds policies around it in Phase 9. Adapter changes or translates a vendor or simulation interface into the sensor port expected by the application, which was the purpose of Phase 5.

9. Contrast Decorator with **inheritance** of combined policies. How does composition let you add or remove a policy without a new subclass for every combination?

> [!NOTE]
> ***Your Answer***
>
> Inheritance fixes a combination into a class and creates more classes as the number of policies grows. With composition, I can wrap the adapter with only the policies needed and change the stack without editing the adapter or creating a new combined type.

10. A classmate’s decorator changes the method signature “a little” (extra required argument, different return type). Another ignores wrap order and cannot explain whether logging runs once per logical call or per inner attempt. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> A changed signature means the decorator can no longer replace the component transparently, so callers must know which wrapper they received. Ignoring order makes behavior unpredictable because an outer logger may record once while an inner logger could record each retry or miss an earlier rejection. The stack order should be deliberate and documented.
