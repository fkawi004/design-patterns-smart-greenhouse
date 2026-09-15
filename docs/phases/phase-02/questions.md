# Phase 2 — Factory Method questions

**Pattern / focus:** Factory Method.

**Read first:** [Guide 02](../../materials/guides/02-factory-method.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example courier notifiers) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to sensors, creators, the `devices` table, and the sensors API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Factory Method in plain language. What problem appears when callers scatter `new` / constructors (or a growing `if type == ...`) across the application?

> [!NOTE]
> ***Your Answer***
>
> Factory Method puts object creation behind a common method, while each concrete creator decides what object to make. If constructors or type checks are spread around the application, the same defaults and rules get repeated and adding a new type means editing many places.

2. Name the main participants of Factory Method (**product**, **concrete product**, **creator**, **concrete creator**, **client**). For each, give one sentence: what it is responsible for.

> [!NOTE]
> ***Your Answer***
>
> The product is the common object the application works with. A concrete product is a particular version of that product. The creator defines the creation method. A concrete creator builds one version with the correct settings. The client asks a creator for the product and uses it without needing to know its construction details.

3. How do you add a **new product variant** when creators are polymorphic (new class + registry entry) versus when creation lives in one shared `if/elif` function? Why does that difference matter for extension?

> [!NOTE]
> ***Your Answer***
>
> With polymorphic creators, I add a creator class for the new variant and one registry entry. With one shared `if/elif` function, I must keep changing the same function every time. Separate creators keep each variant's rules in one place and make extension safer.

## B. This phase of the application

4. In this lab, what is the **product** and what are the **concrete creators**? Why must the API handler (or sensor service) go through a creator/registry instead of constructing `MoistureSensor` / `LightSensor` itself?

> [!NOTE]
> ***Your Answer***
>
> The product is Sensor, and the concrete creators are MoistureSensorCreator and LightSensorCreator. The API goes through the service and registry so it does not need to know the defaults or construction rules for every sensor type.

5. `POST /api/sensors` accepts a short `type` key such as `"moisture"` or `"light"`, while the stored/returned field is `device_type` (for example `moisture_sensor`). Why are those two fields different? Who decides the stored `device_type` and `default_config`?

> [!NOTE]
> ***Your Answer***
>
> Type is a simple input key used to find the right creator. Device type is the stable value used by the application and database. The selected concrete creator decides the stored device type and default configuration.

6. Why is there a single `devices` table with `role="sensor"` instead of a dedicated `sensors` table? What later phase does that choice prepare for?

> [!NOTE]
> ***Your Answer***
>
> Sensors share common device fields, so one devices table avoids separate tables with repeated columns. The role identifies these rows as sensors and prepares the same table for actuators and device families in Phase 3.

7. What should happen when the client posts an **unknown** `type`? Where should that rejection be decided (registry/service vs router constructing a concrete class anyway)?

> [!NOTE]
> ***Your Answer***
>
> An unknown type should be rejected before anything is saved, and the API should return a helpful 400 response. The registry or service should make this decision, while the router only converts the error into an HTTP response.

## C. Compare, contrast, and scenarios

8. Contrast Factory Method with a **simple factory** (one function full of `if type == ...`). When is the simple factory “good enough,” and why does this phase still want polymorphic creators?

> [!NOTE]
> ***Your Answer***
>
> A simple factory can be enough when there are only a few stable types and their creation is very small. This phase uses polymorphic creators so moisture and light defaults stay separate and new sensor types can be added without growing one central function.

9. Contrast Factory Method with **Abstract Factory** (Phase 3). Factory Method answers which question? Abstract Factory answers which different question? Why is Factory Method enough for Phase 2 sensors?

> [!NOTE]
> ***Your Answer***
>
> Factory Method answers which single product should be created and how it gets its defaults. Abstract Factory creates a related family of products that should work together. Phase 2 only creates individual sensor types, so Factory Method is enough for now.

10. A classmate puts SQLAlchemy session commits (or FastAPI request parsing) **inside** a concrete creator. Why is that a trap? Where should persistence and HTTP stay instead?

> [!NOTE]
> ***Your Answer***
>
> That would mix creation rules with database or web framework details, making the creator harder to test and reuse. Database commits belong in the repository and infrastructure layer, while request parsing belongs in the FastAPI router.
