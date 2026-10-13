# Phase 6 — Strategy questions

**Pattern / focus:** Strategy.

**Read first:** [Guide 06](../../materials/guides/06-strategy.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example shipping quotes) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to irrigation (or lighting) policies, location context, and the automation API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Strategy in plain language. How does the **context** use a strategy, and why must “choose which algorithm” stay separate from “run the algorithm”?

> [!NOTE]
> ***Your Answer***
>
> Strategy makes different algorithms replaceable behind the same interface. The context gives its data to the selected strategy and asks it to decide. Choosing a strategy is kept separate so the algorithm does not need to know about settings, HTTP input, or how it was selected.

2. Name the participants (**strategy**, **concrete strategies**, **context**, **client**). What goes wrong when all policies live as `if/elif` inside the context (or inside an HTTP router)?

> [!NOTE]
> ***Your Answer***
>
> AutomationStrategy is the strategy interface, and the conservative and aggressive classes are the concrete strategies. LocationAutomationContext carries the values, and AutomationService is the client. One large if/elif block mixes responsibilities and must be changed every time a policy is added, which also makes each policy harder to test alone.

3. When should you use Strategy, and when should you skip it (one algorithm only; or the variation is a **lifecycle mode** rather than a chosen policy)?

> [!NOTE]
> ***Your Answer***
>
> Strategy is useful when the same task has several algorithms that can be selected or replaced. It is unnecessary when there is only one simple algorithm. If behavior changes because an object moves through lifecycle stages, State is a better match than Strategy.

## B. This phase of the application

4. In this lab, what does a strategy’s `decide(context)` return (action + reason)? Give a concrete difference you implemented (or were required to implement) between **conservative** and **aggressive** on the **same** moisture reading and zone thresholds.

> [!NOTE]
> ***Your Answer***
>
> It returns a Recommendation with an action such as irrigate or wait and a reason. With low 0.30, high 0.50, and moisture 0.40, conservative waits because the value is not below the low threshold. Aggressive irrigates because it starts before the value reaches the high threshold.

5. Where do the numbers in `LocationAutomationContext` (or your equivalent) come from? Latest moisture may already be in `sensor_readings` from a manual read, the simulation sampler, or MQTT translation — why does this phase not add a scheduler or a broker? Why must strategies receive a plain context object, not SQLAlchemy rows or FastAPI types? Why are thresholds read from **zones**, not hardcoded in the strategy class?

> [!NOTE]
> ***Your Answer***
>
> The thresholds come from each saved zone, and moisture comes from the newest database reading of a moisture sensor assigned to that zone. Phase 5 already owns reading collection, so this phase only uses the stored values and does not create another sampler or broker. A plain context keeps domain logic separate from SQLAlchemy and FastAPI. Reading thresholds from zones also lets every zone use its own configuration.

6. The active `strategy_key` is **persisted** per `location_id` (for example in `automation_rules`). Why must `POST .../automation/evaluate` use the **saved** key rather than a key the client sends only in that request? What happens on the next evaluate after the operator changes strategy but moisture stays the same?

> [!NOTE]
> ***Your Answer***
>
> The saved key is the location's actual automation configuration, so evaluation stays consistent across page reloads and different clients. After the operator saves a new strategy, the next evaluation reads that key from the database. The recommendation can change even when moisture is unchanged because a different policy is now active.

7. Strategy **recommends** (irrigate / wait). It should not itself start a pump. Why keep **decide** separate from **execute**? Which later pattern is meant to carry out the action?

> [!NOTE]
> ***Your Answer***
>
> Keeping decision and execution separate makes the policy safe to test and allows a user or another service to inspect the recommendation first. Starting a pump has side effects and failure handling that do not belong in the calculation. The later Command pattern is meant to carry out that action.

## C. Compare, contrast, and scenarios

8. Contrast Strategy with **State** (Phase 8). Both delegate to an object with the same shape. Who typically **changes** the active object, and is the variation a **policy** or a **lifecycle**?

> [!NOTE]
> ***Your Answer***
>
> With Strategy, a client or operator selects a policy such as conservative or aggressive. With State, the object usually changes its own active state when its lifecycle changes. Strategy represents a chosen algorithm, while State represents a lifecycle condition.

9. Contrast Strategy with **Adapter** (Phase 5) and with **Builder** (Phase 4). Which one translates a foreign API, which one assembles a valid aggregate, and which one swaps an algorithm?

> [!NOTE]
> ***Your Answer***
>
> Adapter translates a foreign driver or payload into the interface the application expects. Builder assembles one valid location configuration in steps. Strategy swaps the algorithm used to make an automation decision.

10. A classmate writes one “mega-strategy” that still contains `if conservative` / `if aggressive` inside a single class. Another strategy class calls the actuator adapter to water immediately. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> The mega-strategy hides the same conditional design inside one class, so adding a policy still requires editing the whole decision block. Calling an actuator mixes recommendation with a real side effect and makes the strategy risky and difficult to test. Each policy should only calculate and return its recommendation.
