from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.domain.devices.entity import Device
from src.infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from src.infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from src.infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from src.infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter


def sensor(device_type: str = "moisture_sensor") -> Device:
    return Device(
        id=uuid4(),
        device_type=device_type,
        role="sensor",
        device_family="simulation",
        display_name="Test sensor",
        default_config={"protocol": "simulation"},
    )


def test_vendor_adapter_normalizes_raw_payload() -> None:
    device = sensor("light_sensor")
    reading = VendorStubSensorAdapter().translate(
        device,
        {"measurement": "742.5", "uom": "lux", "status_code": 200},
    )

    assert reading.device_id == device.id
    assert reading.value == 742.5
    assert reading.unit == "lux"
    assert reading.source == "vendor"


@pytest.mark.parametrize(
    ("device_type", "minimum", "maximum", "unit"),
    [
        ("moisture_sensor", 0.2, 0.6, "vwc"),
        ("light_sensor", 200.0, 2000.0, "lux"),
    ],
)
def test_simulation_adapter_value_in_range(
    device_type: str,
    minimum: float,
    maximum: float,
    unit: str,
) -> None:
    reading = SimulationSensorAdapter().read(sensor(device_type))

    assert minimum <= reading.value <= maximum
    assert reading.unit == unit
    assert reading.source == "simulation"


def test_mqtt_adapter_translates_payload_without_transport() -> None:
    device = sensor()
    timestamp = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)

    reading = MqttSensorAdapter().translate(
        device,
        {"value": 0.41, "unit": "vwc"},
        timestamp,
    )

    assert reading.device_id == device.id
    assert reading.value == 0.41
    assert reading.unit == "vwc"
    assert reading.source == "mqtt"
    assert reading.recorded_at == timestamp


def test_simulation_actuator_records_intent() -> None:
    adapter = SimulationActuatorAdapter()
    device_id = uuid4()

    adapter.apply(device_id, "turn_on", {"duration_seconds": 10})

    assert adapter.applied_commands[0].device_id == device_id
    assert adapter.applied_commands[0].command == "turn_on"
    assert adapter.applied_commands[0].payload == {"duration_seconds": 10}
