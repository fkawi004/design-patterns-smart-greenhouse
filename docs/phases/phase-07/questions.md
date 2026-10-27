# Phase 7 — Facade questions

**Pattern / focus:** Facade.

**Read first:** [Guide 07](../../materials/guides/07-facade.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a video publish pipeline) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to the location overview, the facade, and the dashboard Overview page from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Facade in plain language. What problem appears when every HTTP handler (or every UI screen) repeats the same multi-step dance across repositories and services?

> [!NOTE]
> **_Your Answer_**
>
> Facade gives a simple entry point to a group of more complicated services. Without it, different handlers and screens repeat the same calls and can build slightly different results. Changes would also need to be made in several places.

2. A facade **orchestrates** collaborators. What should it **not** become (a god object that owns all domain logic)? Where should irrigation policy, sensor translation, and persistence stay instead?

> [!NOTE]
> **_Your Answer_**
>
> A facade should coordinate work, not collect all business rules into one large class. Irrigation decisions stay in Strategy classes, sensor translation stays in Adapters, and database queries stay in repositories. The facade only asks them for the data and behavior it needs.

3. When should you use Facade, and when should you skip it (a single repository call is enough; or you actually need to **translate** a mismatched interface)?

> [!NOTE]
> **_Your Answer_**
>
> Facade is useful when one use case needs several subsystem calls in a known order. It is unnecessary when one repository call already solves the use case. If the real problem is changing one incompatible interface into another, Adapter should be used instead.

## B. This phase of the application

4. What does `GET /api/locations/{location_id}/overview` return? Name the main pieces of the overview DTO: location, assigned device counts, and `zones` (thresholds, assigned devices, and those devices’ latest readings, including `tracking_enabled` and `sampling_interval_seconds`), plus strategy key and last recommendation. Why may those reading rows come from the sampler or MQTT ingest, not only from `POST /read`? Why is overview scoped by `location_id`?

> [!NOTE]
> **_Your Answer_**
>
> It returns the location, assigned sensor and actuator counts, every zone with thresholds, its assigned devices, and the latest available reading for each device. Reading summaries also contain tracking and sampling settings. It includes the saved strategy key and a current recommendation. All reading sources use the same table, so sampler and MQTT rows are valid too. Location id is the scope because it owns the zones and their assigned devices.

5. Why does this phase **not** require a new business table? What already exists from Phases 2–6 that the facade only **composes**?

> [!NOTE]
> **_Your Answer_**
>
> The overview does not create new business data. Locations, zones, devices, assignments, sensor readings, and automation rules are already saved by earlier phases. The facade only reads and combines those tables into one response.

6. The overview HTTP handler should call **only** the facade, not reading/strategy/device repositories directly. Why? How does that help tests and later changes to the query shape?

> [!NOTE]
> **_Your Answer_**
>
> Calling only the facade keeps HTTP code small and stops repository coordination from leaking into the router. Tests can replace the facade with one fake, and repository queries can later be optimized without changing the route contract.

7. The location selector may use the existing locations list. The Overview cards come from **one** overview fetch, and Refresh repeats that same fetch. Why must the React page not stitch device, reading, and automation calls together to build the same snapshot? How does a new reading or a saved strategy show up on overview without extra frontend glue?

> [!NOTE]
> **_Your Answer_**
>
> Building the snapshot in React would duplicate backend rules and could combine responses taken at different times. The page makes one overview request, so it stays simple and consistent. A new reading or saved strategy is already in the database, and the next overview request reads it automatically.

## C. Compare, contrast, and scenarios

8. Contrast Facade with **Adapter**. One makes an existing interface usable; the other makes a subsystem simpler to call. Which is which, and how do both appear in this greenhouse app (Phase 5 vs Phase 7)?

> [!NOTE]
> **_Your Answer_**
>
> Adapter makes an incompatible interface usable, such as translating simulation, vendor, or MQTT data into a Reading. Facade makes several existing subsystems easier to use by giving the dashboard one overview operation.

9. This phase mentions **N+1** queries. What is an N+1 problem in an overview that lists latest readings for many devices, and what can the facade (or its repository) do about it without putting SQL in the router?

> [!NOTE]
> **_Your Answer_**
>
> N+1 happens when the application first loads a list of devices and then runs another reading query for every device. The repository can request the newest readings for all assigned device ids in one query and return a map. The router still only calls the facade and never contains SQL.

10. A classmate hides every error behind a generic “overview failed,” so a missing location, a DB outage, and a strategy error look the same. Why is that a trap for a facade?

> [!NOTE]
> **_Your Answer_**
>
> A generic error removes useful meaning and makes debugging or correct HTTP responses difficult. The facade should preserve important error types, such as a missing location becoming 404, while unexpected database or strategy failures remain visible as real server problems.
