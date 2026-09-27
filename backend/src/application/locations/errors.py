class LocationNotFoundError(LookupError):
    pass


class ZoneNotFoundError(LookupError):
    pass


class DeviceNotFoundError(LookupError):
    pass


class LastZoneDeletionError(ValueError):
    pass
