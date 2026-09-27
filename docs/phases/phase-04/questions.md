# Phase 4 — Builder questions

**Pattern / focus:** Builder.

**Read first:** [Guide 04](../../materials/guides/04-builder.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example ramen orders) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to locations, zones, `location_id`, and the configuration wizard from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Builder in plain language. Why does construction of a complex object need **stepwise assembly** and **validation at the end** (`build()`), instead of a telescoping constructor or a half-filled dict written straight to the database?

> [!NOTE]
> **_Your Answer_**
>
> Builder creates a complex object in clear steps and checks the complete result before it can be used. This is easier to understand than a constructor with many arguments, and it prevents an unfinished dictionary from being saved as if it were a valid configuration.

2. Name the main participants (**product**, **builder**, **optional director**, **client**). Until `build()` succeeds, is the intermediate object a finished domain product? Why does that distinction matter?

> [!NOTE]
> **_Your Answer_**
>
> The product is LocationConfig, the builder is LocationConfigBuilder, and the client is the location configuration service. A director is optional and could define a reusable sequence of builder steps. The intermediate builder state is not a finished product because it may still be incomplete or invalid. Only a successful build returns something that may be persisted.

3. List at least three kinds of invalid configuration a location/zone `build()` should reject in **this** lab (name, zones, moisture thresholds). Why must those rules live in the **domain** builder, not only in the HTTP layer?

> [!NOTE]
> **_Your Answer_**
>
> It rejects an empty location name, a location with no zones, an empty zone name, repeated zone names, thresholds outside 0 to 1, and a low threshold that is equal to or higher than the high threshold. These rules belong in the domain so they are enforced even if the configuration is created somewhere other than the HTTP API.

## B. This phase of the application

4. What aggregate does the builder produce (location plus zones)? Why does this course use **`location_id`** (and never `greenhouse_id`) as the name for that scope?

> [!NOTE]
> **_Your Answer_**
>
> The builder produces one LocationConfig containing a location and all of its zones. Location is the resource that owns the zones in the database and API, so location_id describes that relationship consistently. Greenhouse_id would introduce a second name for the same scope and make later relationships confusing.

5. Describe the path from API request to persistence: DTO → builder steps → `build()` → repository. What must **not** be persisted if `build()` raises `ConfigurationError` (or equivalent)? Why does assigning a device wait until the zone row exists, and why does the client send only `zone_id`?

> [!NOTE]
> **_Your Answer_**
>
> The API reads the request DTO, the service sends its location name and zones through the builder, build validates the whole configuration, and the repository saves the valid result. If validation fails, neither the location nor any zones should be saved. Device assignment waits because the zone needs a database id first. The client sends only zone_id, and the server copies location_id from that zone so the two values cannot disagree.

6. Saving a location and its zones must be **one transaction**. What goes wrong if the location row commits and a later zone insert fails? How does that relate to “no half-built aggregates in the database”?

> [!NOTE]
> **_Your Answer_**
>
> If the location commits first and a zone insert fails later, the database can contain a location with missing zones. One transaction makes all inserts succeed together or rolls all of them back, so the database never contains only part of the configuration.

7. The configuration wizard UI collects fields in steps. How does that UI map to Builder without turning React (or the HTTP handler) into the place that owns domain validation?

> [!NOTE]
> **_Your Answer_**
>
> The wizard collects the same location and zone values that become builder steps on the backend. React gives quick inline feedback for obvious mistakes, but the service and domain builder still make the final decision. This keeps the rules reliable for every client and not only this screen.

## C. Compare, contrast, and scenarios

8. Contrast Builder with Factory Method and with Abstract Factory. Which pattern answers “which type?”, which answers “which matching kit?”, and which answers “how do we assemble one **valid whole** in steps?”

> [!NOTE]
> **_Your Answer_**
>
> Factory Method answers which one product type should be created. Abstract Factory answers which matching family or kit should be created. Builder answers how one complete and valid object is assembled through several steps before it is returned.

9. Fluent method chaining (`builder.add_zone(...).build()`) is a coding style. Why is a fluent interface **not** the same thing as the Builder pattern?

> [!NOTE]
> **_Your Answer_**
>
> Method chaining only changes how calls are written. Builder is about separating the construction process, keeping intermediate state, and returning a checked product at the end. A fluent class without those responsibilities is not automatically a Builder.

10. A classmate validates thresholds only in FastAPI / Pydantic and leaves `build()` empty. Another mutates builder fields after `build()` while treating the product as immutable. Explain why each is a trap.

> [!NOTE]
> **_Your Answer_**
>
> HTTP-only validation can be bypassed by tests, scripts, or another interface, so the domain could still create an invalid configuration. Mutating shared builder data after build can also change a product that callers believe is fixed. The builder should validate itself and return a separate immutable result.
