# Abstract Factory in Phase 3

## The problem

The greenhouse now needs complete device kits for different environments. Choosing every sensor and actuator separately could mix simulation devices with edge devices, producing inconsistent names, protocols, and configuration.

## The solution

DeviceFamilyFactory defines one method that creates a complete device set. SimulationDeviceFamilyFactory and EdgeDeviceFamilyFactory each return two sensors and two actuators with one family key and matching defaults. The family factories still call the Phase 2 sensor creators, so the existing Factory Method implementation remains responsible for individual sensor types.

Factory Method answers which one sensor product to create. Abstract Factory answers which related product line to provision. In this phase, that product line contains moisture and light sensors together with a water pump and grow light actuator.

The main implementation is in these files:

- backend/src/domain/devices/entity.py contains the domain Device.
- backend/src/domain/devices/family_factory.py contains the abstract and concrete family factories.
- backend/src/application/devices/family_service.py coordinates provisioning and persistence.
- backend/src/application/devices/dto.py and mappers.py keep the API model separate from the domain.
- backend/src/infrastructure/persistence/device_repository.py stores and filters all device roles.
- backend/src/interfaces/api/devices.py exposes the unified devices API.

Device is not an API DTO because the domain should not depend on HTTP or Pydantic. A separate mapper controls exactly what the API returns without putting web concerns into the factory or entity.

## Extension exercise

Add a cloud family with the same four device types, cloud-specific labels, and a different protocol. Register the new concrete factory without changing the API, repository, or existing family factories.
