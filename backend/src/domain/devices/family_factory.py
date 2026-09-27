from abc import ABC, abstractmethod

from src.domain.devices.entity import Device
from src.domain.sensors.creators import get_sensor_creator
from src.domain.sensors.entity import Sensor


class UnknownDeviceFamilyError(ValueError):
    pass


class DeviceFamilyFactory(ABC):
    family_key: str

    @abstractmethod
    def create_device_set(self) -> list[Device]:
        """Create one coherent set of sensors and actuators."""

    def _sensor_device(
        self,
        sensor: Sensor,
        display_name: str,
        family_config: dict[str, object],
    ) -> Device:
        return Device(
            device_type=sensor.device_type,
            role="sensor",
            device_family=self.family_key,
            display_name=display_name,
            default_config={**sensor.default_config, **family_config},
        )


class SimulationDeviceFamilyFactory(DeviceFamilyFactory):
    family_key = "simulation"

    def create_device_set(self) -> list[Device]:
        moisture = get_sensor_creator("moisture").create_sensor()
        light = get_sensor_creator("light").create_sensor()
        family_config = {"protocol": "simulation", "source": "generated"}
        return [
            self._sensor_device(moisture, "Simulated Moisture Sensor", family_config),
            self._sensor_device(light, "Simulated Light Sensor", family_config),
            Device(
                device_type="water_pump",
                role="actuator",
                device_family=self.family_key,
                display_name="Simulated Water Pump",
                default_config={
                    "protocol": "simulation",
                    "max_flow_liters_per_minute": 8,
                    "command_delay_ms": 100,
                },
            ),
            Device(
                device_type="grow_light",
                role="actuator",
                device_family=self.family_key,
                display_name="Simulated Grow Light",
                default_config={
                    "protocol": "simulation",
                    "max_brightness_percent": 100,
                    "command_delay_ms": 80,
                },
            ),
        ]


class EdgeDeviceFamilyFactory(DeviceFamilyFactory):
    family_key = "edge"

    def create_device_set(self) -> list[Device]:
        moisture = get_sensor_creator("moisture").create_sensor()
        light = get_sensor_creator("light").create_sensor()
        family_config = {
            "protocol": "mqtt",
            "gateway": "greenhouse-edge",
            "hardware_stub": True,
        }
        return [
            self._sensor_device(moisture, "Edge Moisture Probe", family_config),
            self._sensor_device(light, "Edge Light Meter", family_config),
            Device(
                device_type="water_pump",
                role="actuator",
                device_family=self.family_key,
                display_name="Edge Pump Relay",
                default_config={
                    "protocol": "mqtt",
                    "topic": "greenhouse/edge/pump",
                    "relay_channel": 1,
                    "hardware_stub": True,
                },
            ),
            Device(
                device_type="grow_light",
                role="actuator",
                device_family=self.family_key,
                display_name="Edge Light Controller",
                default_config={
                    "protocol": "mqtt",
                    "topic": "greenhouse/edge/light",
                    "relay_channel": 2,
                    "hardware_stub": True,
                },
            ),
        ]


DEVICE_FAMILY_FACTORIES: dict[str, DeviceFamilyFactory] = {
    "simulation": SimulationDeviceFamilyFactory(),
    "edge": EdgeDeviceFamilyFactory(),
}


def get_device_family_factory(family_key: str) -> DeviceFamilyFactory:
    try:
        return DEVICE_FAMILY_FACTORIES[family_key]
    except KeyError as error:
        supported = ", ".join(sorted(DEVICE_FAMILY_FACTORIES))
        raise UnknownDeviceFamilyError(
            f"Unknown device family '{family_key}'. Supported families: {supported}."
        ) from error
