import pytest

from src.domain.sensors.creators import UnknownSensorTypeError, get_sensor_creator


def test_moisture_creator_has_moisture_defaults() -> None:
    sensor = get_sensor_creator("moisture").create_sensor()

    assert sensor.device_type == "moisture_sensor"
    assert sensor.default_config["unit"] == "percent"
    assert "moisture_threshold" in sensor.default_config


def test_light_creator_has_distinct_defaults() -> None:
    moisture = get_sensor_creator("moisture").create_sensor()
    light = get_sensor_creator("light").create_sensor()

    assert light.device_type == "light_sensor"
    assert light.default_config["unit"] == "lux"
    assert light.default_config != moisture.default_config


def test_unknown_sensor_type_is_rejected() -> None:
    with pytest.raises(UnknownSensorTypeError, match="Unknown sensor type"):
        get_sensor_creator("temperature")
