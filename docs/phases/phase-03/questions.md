# Phase 3 — Abstract Factory questions

**Pattern / focus:** Abstract Factory.

**Read first:** [Guide 03](../../materials/guides/03-abstract-factory.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example warrior/mage class kits) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to device families, provision, and the unified devices API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Abstract Factory in plain language. What goes wrong when related products are chosen independently (`if format` for each piece) instead of as a **family**?

> [!NOTE]
> ***Your Answer***
>
> Abstract Factory creates a group of related products that are meant to work together. If every product is chosen separately, the application can accidentally mix products with different settings or environments and create an inconsistent set.

2. Name the main participants (**abstract factory**, **concrete factory**, **abstract products**, **concrete products**, **client**). How does choosing a factory at the start **commit** the client to one family?

> [!NOTE]
> ***Your Answer***
>
> The abstract factory defines how a complete family is created. A concrete factory creates one specific family. Abstract products describe the kinds of products in the set, while concrete products are the actual family versions. The client uses the chosen factory, so every product it receives belongs to that same family.

3. When should you use Abstract Factory, and when should you skip it (for example only one product type per request, or mixing siblings is valid)?

> [!NOTE]
> ***Your Answer***
>
> Abstract Factory is useful when several related product types must use matching variants. It is unnecessary when only one product is created, there is only one possible family, or mixing products from different families is allowed.

## B. This phase of the application

4. In this lab, what is a **device family**, and what does `create_device_set()` (or your equivalent) return? Why must a simulation kit and an edge kit not mix incompatible siblings?

> [!NOTE]
> ***Your Answer***
>
> A device family represents one environment, either simulation or edge. The creation method returns two sensors and two actuators that share the same family. Mixing them could give one kit different protocols, labels, and configuration rules that do not belong together.

5. Phase 2 Factory Method creators still exist. How does Abstract Factory **compose** them rather than replace them? What would you lose if you deleted the sensor creators and inlined all construction inside the family factory?

> [!NOTE]
> ***Your Answer***
>
> Each family factory calls the existing moisture and light sensor creators, then adds the family information and matching actuators. If the sensor creators were deleted, their defaults would be duplicated inside every family factory and adding new sensor types would become harder.

6. Why add a `device_family` column on the existing `devices` table (with a default/backfill such as `"simulation"`) instead of a new table per family? What happens to Phase 2 sensor rows if you forget the backfill?

> [!NOTE]
> ***Your Answer***
>
> All devices share the same basic fields, so one table keeps storage and filtering simple. The family column identifies which set each row belongs to. The default also gives existing Phase 2 sensors a valid family. Without it, old rows could contain a missing family or the migration could fail because the column cannot be null.

7. `POST /api/devices/provision` returns a kit (expected size: two sensors and two actuators). `GET /api/devices` can filter by `family` and `role`. Why must the UI be able to filter by family? Why do `/api/sensors` routes from Phase 2 still need to work?

> [!NOTE]
> ***Your Answer***
>
> Filtering lets the UI show only the selected family instead of mixing simulation and edge devices together. The sensors routes must still work because Phase 2 supports creating individual sensor types and Phase 3 should extend that feature rather than break it.

## C. Compare, contrast, and scenarios

8. Draw the contrast in one paragraph: Factory Method vs Abstract Factory. Use the questions “which **one** product?” versus “which product **line**?” and mention that Abstract Factory often **uses** Factory Method–style methods inside.

> [!NOTE]
> ***Your Answer***
>
> Factory Method answers which one product should be created, such as one moisture or light sensor. Abstract Factory answers which product line should be created, such as a complete simulation or edge kit. An Abstract Factory can use Factory Method style creators inside it to build the individual products in that line.

9. A DTO or HTTP handler constructs concrete simulation/edge device types directly, bypassing the family factory. What consistency bug can that reintroduce? How should HTTP stay on the abstract factory / service instead?

> [!NOTE]
> ***Your Answer***
>
> Direct construction could mix an edge device with simulation defaults or forget one of the required products. The HTTP handler should only accept the family choice and pass it to the service, which resolves the correct family factory and returns mapped DTOs.

10. Someone proposes a single “god factory” that creates locations, readings, and devices “because we already have a factory.” Why is that a misuse of Abstract Factory?

> [!NOTE]
> ***Your Answer***
>
> Abstract Factory should create one related product family, not every object in the application. Locations, readings, and device kits have different responsibilities and change for different reasons. Combining them would make the factory large, tightly coupled, and difficult to maintain.
