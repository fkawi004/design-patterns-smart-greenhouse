# Factory Method in Phase 2

## The problem

The application needs to create different sensor types. Each type has its own stored name and default configuration. If the API created these objects directly with a growing `if/elif` block, the API would need to know every sensor rule and would become harder to extend.

## The solution

`SensorCreator` defines one common `create_sensor` method. `MoistureSensorCreator` and `LightSensorCreator` implement it with their own defaults. A registry maps the short API keys `moisture` and `light` to these creators. `SensorService` selects the creator and then asks the repository to save the resulting `Sensor`.

The responsibilities are separated in these files:

- `backend/src/domain/sensors/entity.py` contains the product.
- `backend/src/domain/sensors/creators.py` contains the creator hierarchy and registry.
- `backend/src/application/sensors/service.py` coordinates creation and persistence.
- `backend/src/infrastructure/persistence/device_repository.py` saves sensors in PostgreSQL.
- `backend/src/interfaces/api/sensors.py` handles HTTP input and output.

## Extension exercise

To add a temperature sensor, create `TemperatureSensorCreator` with a `temperature_sensor` device type and temperature-specific defaults. Then register it using the short key `temperature`. The router, service, repository, and `devices` table do not need to be redesigned.
