# Adapter in Phase 5

## The problem

The application needs one way to read sensors even though simulation, a vendor driver, and MQTT use different data shapes. If application services used those details directly, changing a driver would also require changing the business code.

## The solution

SensorPort is the target interface used by the application. Each sensor adapter translates its own input into the same Reading value containing the device id, value, unit, source, and time. SimulationSensorAdapter creates course test values, VendorStubSensorAdapter translates the vendor-shaped response, and MqttSensorAdapter translates an already received payload dictionary. The MQTT adapter does not connect to a broker in this phase.

The adapter selector chooses the implementation from the device configuration. Simulation is the normal course driver. Setting `adapter` to `vendor_stub` selects the documented vendor stub, while an MQTT protocol selects the translator that intentionally reports that transport is not available yet.

ReadingIngest is the single writer for `sensor_readings`. A manual read and the background sampler both pass through it, so all readings use the same persistence path. The sampler reads only enabled simulation sensors when their saved interval has passed. Sensor cards poll the latest stored row every five seconds until a later phase introduces live WebSocket updates.

ActuatorPort and SimulationActuatorAdapter provide the matching actuator boundary without sending commands to real hardware.

## Main files

- `backend/src/domain/sensors/ports.py` defines SensorPort.
- `backend/src/domain/sensors/reading.py` defines the normalized Reading.
- `backend/src/domain/actuators/ports.py` defines ActuatorPort.
- `backend/src/infrastructure/adapters` contains simulation, vendor, MQTT, and actuator adapters.
- `backend/src/application/readings/service.py` contains the one reading writer.
- `backend/src/application/readings/sampler.py` contains the due-time sampler.
- `backend/src/infrastructure/persistence/reading_repository.py` stores the reading history.

## Extension idea

A third vendor can be added by implementing SensorPort and adding one selector rule. The API, sampler, reading writer, and database do not need vendor-specific types or field names.
