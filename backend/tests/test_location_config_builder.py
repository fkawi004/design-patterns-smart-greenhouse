import pytest

from src.domain.locations.config_builder import LocationConfigBuilder
from src.domain.locations.errors import ConfigurationError


def test_build_success() -> None:
    config = (
        LocationConfigBuilder()
        .with_location_name("  Main greenhouse  ")
        .add_zone("North", 0.2, 0.5, {"watering": "08:00"})
        .add_zone("South", 0.3, 0.6)
        .build()
    )

    assert config.location.name == "Main greenhouse"
    assert [zone.name for zone in config.location.zones] == ["North", "South"]
    assert config.location.zones[0].schedule == {"watering": "08:00"}


def test_build_requires_name() -> None:
    builder = LocationConfigBuilder().add_zone("North", 0.2, 0.5)

    with pytest.raises(ConfigurationError, match="Location name"):
        builder.build()


def test_build_requires_zones() -> None:
    builder = LocationConfigBuilder().with_location_name("Main greenhouse")

    with pytest.raises(ConfigurationError, match="At least one zone"):
        builder.build()


@pytest.mark.parametrize(
    ("low", "high"),
    [(0.5, 0.5), (0.7, 0.4), (-0.1, 0.4), (0.2, 1.1)],
)
def test_build_rejects_invalid_thresholds(low: float, high: float) -> None:
    builder = (
        LocationConfigBuilder().with_location_name("Main greenhouse").add_zone("North", low, high)
    )

    with pytest.raises(ConfigurationError):
        builder.build()


def test_build_requires_unique_zone_names() -> None:
    builder = (
        LocationConfigBuilder()
        .with_location_name("Main greenhouse")
        .add_zone("North", 0.2, 0.5)
        .add_zone(" north ", 0.3, 0.6)
    )

    with pytest.raises(ConfigurationError, match="unique"):
        builder.build()
