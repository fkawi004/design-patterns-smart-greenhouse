from src.domain.devices.entity import Device
from src.domain.sensors.ports import SensorPort
from src.infrastructure.adapters.sensors.errors import SensorAdapterError
from src.infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from src.infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from src.infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter


class SensorAdapterSelector:
    """Select by protocol; adapter=vendor_stub explicitly enables the exercise stub."""

    def for_device(self, device: Device) -> SensorPort:
        if device.default_config.get("adapter") == "vendor_stub":
            return VendorStubSensorAdapter()
        protocol = device.default_config.get("protocol")
        if protocol is None and device.device_family == "simulation":
            protocol = "simulation"
        if protocol == "simulation":
            return SimulationSensorAdapter()
        if protocol == "mqtt":
            return MqttSensorAdapter()
        raise SensorAdapterError(f"No sensor adapter for protocol '{protocol}'.")
