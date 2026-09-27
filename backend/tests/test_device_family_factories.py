from src.domain.devices.family_factory import (
    EdgeDeviceFamilyFactory,
    SimulationDeviceFamilyFactory,
)


def test_simulation_factory_creates_complete_family() -> None:
    devices = SimulationDeviceFamilyFactory().create_device_set()

    assert len(devices) == 4
    assert {device.device_type for device in devices} == {
        "moisture_sensor",
        "light_sensor",
        "water_pump",
        "grow_light",
    }
    assert {device.device_family for device in devices} == {"simulation"}
    assert sum(device.role == "sensor" for device in devices) == 2
    assert sum(device.role == "actuator" for device in devices) == 2


def test_edge_factory_differs_from_simulation() -> None:
    simulation = SimulationDeviceFamilyFactory().create_device_set()
    edge = EdgeDeviceFamilyFactory().create_device_set()

    assert len(edge) == 4
    assert {device.device_type for device in edge} == {
        device.device_type for device in simulation
    }
    assert {device.device_family for device in edge} == {"edge"}
    assert sum(device.role == "sensor" for device in edge) == 2
    assert sum(device.role == "actuator" for device in edge) == 2
    assert edge[0].default_config["protocol"] == "mqtt"
    assert simulation[0].default_config["protocol"] == "simulation"
    assert edge[0].display_name != simulation[0].display_name
