# Phase 5 — Adapter questions

**Pattern / focus:** Adapter.

**Read first:** [Guide 05](../../materials/guides/05-adapter.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a legacy XML calendar client) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to sensor ports, adapters, readings, and `sensor_readings` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Adapter in plain language. What problem appears when business code speaks a vendor or legacy protocol (odd field names, units, XML, status codes) directly?

> [!NOTE]
> ***Your Answer***
>
> Adapter changes an interface that does not fit into one the application expects. If business code works with vendor fields and protocols directly, it becomes tied to that vendor and is harder to test or replace.

2. Name the participants (**target / port**, **adaptee**, **adapter**, **client**). What does the adapter translate, and what must it **not** decide (business policy)?

> [!NOTE]
> ***Your Answer***
>
> SensorPort is the target, the simulation or vendor driver is the adaptee, and the sensor adapter translates its result. ReadingIngest and the sampler are clients of the port. The adapter translates fields, units, status, and source into a Reading, but it must not decide business rules such as when plants need water.

3. GoF distinguishes an **object adapter** (composition) from a **class adapter** (inheritance). Which does modern code prefer, and why?

> [!NOTE]
> ***Your Answer***
>
> Modern code usually prefers an object adapter using composition. It can wrap different implementations, is easier to replace in tests, and does not depend on the limits of inheritance.

## B. This phase of the application

4. What is `SensorPort` in this lab, and what normalized value type (for example `Reading`) do adapters return? Why do application services depend on the port rather than on a simulation driver or vendor SDK?

> [!NOTE]
> ***Your Answer***
>
> SensorPort is the common reading interface for all sensors. Its read operation returns a Reading with a device id, value, unit, source, and recorded time. Services depend on this port so the driver can change without changing the service, and tests can use a simple fake.

5. You need three translations onto the same normalized reading: a simulation adapter, a vendor stub, and an MQTT translator that accepts a payload dict.
Why is the different raw shape the point of the exercise? How does `source` (`simulation`, `vendor`, or `mqtt`) show which adapter produced the reading, and why must the MQTT translator not open a broker in this phase? Phase 12 may deliver that same dict on a device HTTP route or through an optional broker — why must this phase still not open either transport?

> [!NOTE]
> ***Your Answer***
>
> The different shapes show that each adapter can hide its own driver format and still return the same Reading. The source field records which adapter produced it. MQTT only translates an already received dictionary because connecting to HTTP or a broker is a transport responsibility planned for Phase 12, not part of this Adapter phase.

6. Readings are **appended** to `sensor_readings` (history grows). Why not keep only the latest value in memory or overwrite a single row, and which later phase consumes this history? Why do a manual read, the simulation sampler, and (later) MQTT share **one** writer of that table? Why does the sampler skip devices with tracking off and MQTT devices, and why do sensor cards poll the latest stored reading until Phase 12?

> [!NOTE]
> ***Your Answer***
>
> Appending readings keeps history for trends and for the later Strategy phase, while an in-memory value would disappear and one row would lose older data. One writer makes every source use the same validation and persistence rules. The sampler skips tracking-disabled sensors and MQTT devices because they should not generate simulated data. The cards poll stored data until Phase 12 provides live WebSocket updates.

7. `POST /api/sensors/{id}/read` runs an adapter, persists, and returns a DTO. What HTTP status is appropriate when the device is missing versus when the adapter fails? Why must the router never see vendor-shaped types?

> [!NOTE]
> ***Your Answer***
>
> A missing device returns 404, while an adapter or input failure returns 400. The router should only see the normal Reading DTO so vendor details stay inside the adapter and cannot spread into the API.

## C. Compare, contrast, and scenarios

8. Contrast Adapter with **Facade**. Adapter changes the **shape** of an existing interface; Facade simplifies **how to use** a subsystem. Give a greenhouse-shaped example of each (Adapter this phase; Facade in Phase 7).

> [!NOTE]
> ***Your Answer***
>
> The sensor adapter changes a vendor result into the Reading interface expected by the greenhouse application. A Phase 7 facade could give the dashboard one simple overview operation while it coordinates devices, locations, and reading repositories behind it.

9. Contrast Adapter with **Decorator**. Both wrap an object. What is different about the interface they present to the client?

> [!NOTE]
> ***Your Answer***
>
> Adapter presents a different interface that the client needs. Decorator keeps the same interface as the wrapped object and adds behavior around it.

10. A classmate puts irrigation policy (“if moisture &lt; 0.3 then water”) inside the vendor adapter. Why is that a trap? Where should that decision live instead (later Strategy), and what should stay in the adapter?

> [!NOTE]
> ***Your Answer***
>
> That mixes device translation with a greenhouse business decision and would make the rule depend on one vendor. The irrigation decision should live in the later Strategy. The adapter should only read and translate the vendor value into a normalized Reading.
