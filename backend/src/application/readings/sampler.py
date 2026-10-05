from datetime import datetime

from src.application.readings.service import ReadingIngest, ReadingRepository


class SimulationSampler:
    def __init__(self, repository: ReadingRepository, ingest: ReadingIngest) -> None:
        self.repository = repository
        self.ingest = ingest

    def run_once(self, now: datetime) -> int:
        recorded = 0
        for device in self.repository.list_tracking_sensors():
            protocol = device.default_config.get("protocol")
            if protocol is None and device.device_family == "simulation":
                protocol = "simulation"
            if protocol != "simulation" or device.default_config.get("adapter") == "vendor_stub":
                continue
            if device.id is None:
                continue
            latest = self.repository.latest_for_device(device.id)
            if latest is not None:
                elapsed = (now - latest.recorded_at).total_seconds()
                if elapsed < device.sampling_interval_seconds:
                    continue
            self.ingest.take_reading(device.id, recorded_at=now)
            recorded += 1
        return recorded
