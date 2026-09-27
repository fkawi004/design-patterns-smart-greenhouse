# Builder in Phase 4

## The problem

A location configuration is one complete object made from a location name and one or more zones. Saving a partly filled dictionary could leave an empty location, no zones, repeated zone names, or invalid moisture thresholds in the database.

## The solution

LocationConfigBuilder collects the location name and zones one step at a time. Its build method checks the complete configuration and returns an immutable LocationConfig only when every rule passes. The application service translates the request DTO into builder calls, then gives the valid product to the repository. The repository saves the location and all its zones in one transaction.

Validation for required names, at least one zone, unique zone names, VWC values between 0 and 1, and low being less than high lives in the domain. Zone updates reuse the same zone validation rules.

Builder answers how one valid whole is assembled in steps. Factory Method chooses one product type, while Abstract Factory chooses a matching family of products.

The database and API use location and location_id because location is the relational resource that owns zones. The project does not introduce greenhouse_id.

Device assignment is not a builder method. A zone must already be saved before it has an id, so a separate assignment service sets devices.zone_id and copies the zone's location_id. Listing or deleting locations and changing saved zones are also separate use cases because they do not build a new configuration.

## Main files

- backend/src/domain/locations/config_builder.py contains the builder and validation.
- backend/src/application/locations/config_service.py coordinates creation and saved-zone management.
- backend/src/application/locations/zone_assignment_service.py handles device placement separately.
- backend/src/infrastructure/persistence/location_repository.py stores locations, zones, and assignments.
- backend/src/interfaces/api/locations.py exposes the location and zone routes.
- frontend/src/components/config/LocationConfigWizard.tsx provides the dashboard workflow.

## Extension idea

A later director could provide common location templates, such as a seedling layout, by calling the same builder steps. The builder would still own the final validation rules.
