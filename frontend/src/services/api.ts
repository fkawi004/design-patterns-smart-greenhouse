export interface HealthResponse {
  status: string;
  db: "ok" | "fail";
}

export interface SensorDto {
  id: string;
  device_type: string;
  display_name: string;
  default_config: Record<string, unknown>;
}

export interface CreateSensorRequest {
  type: "moisture" | "light";
  display_name: string | null;
}

export type DeviceFamily = "simulation" | "edge";
export type DeviceRole = "sensor" | "actuator";

export interface DeviceDto {
  id: string;
  device_type: string;
  role: DeviceRole;
  device_family: DeviceFamily;
  display_name: string;
  default_config: Record<string, unknown>;
  zone_id: string | null;
  location_id: string | null;
}

export interface ZoneWriteDto {
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  schedule: Record<string, unknown>;
}

export interface ZoneDto extends ZoneWriteDto {
  id: string;
  location_id: string;
}

export interface LocationSummaryDto {
  id: string;
  name: string;
}

export interface LocationConfigDto {
  location: LocationSummaryDto;
  zones: ZoneDto[];
}

export interface BuildLocationConfigRequestDto {
  location_name: string;
  zones: ZoneWriteDto[];
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function errorDetail(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, { signal });
  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}

export async function fetchSensors(signal?: AbortSignal): Promise<SensorDto[]> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`, { signal });
  if (!response.ok) {
    throw new Error(`Sensor request failed with status ${response.status}`);
  }
  return response.json() as Promise<SensorDto[]>;
}

export async function createSensor(request: CreateSensorRequest): Promise<SensorDto> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Sensor creation failed with status ${response.status}`);
  }
  return response.json() as Promise<SensorDto>;
}

export async function fetchDevices(
  family?: DeviceFamily,
  role?: DeviceRole,
  signal?: AbortSignal,
): Promise<DeviceDto[]> {
  const query = new URLSearchParams();
  if (family) query.set("family", family);
  if (role) query.set("role", role);
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  const response = await fetch(`${API_BASE_URL}/api/devices${suffix}`, { signal });
  if (!response.ok) {
    throw new Error(`Device request failed with status ${response.status}`);
  }
  return response.json() as Promise<DeviceDto[]>;
}

export async function provisionDeviceFamily(family: DeviceFamily): Promise<DeviceDto[]> {
  const query = new URLSearchParams({ family });
  const response = await fetch(`${API_BASE_URL}/api/devices/provision?${query.toString()}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Device provisioning failed with status ${response.status}`);
  }
  return response.json() as Promise<DeviceDto[]>;
}

export async function fetchLocations(signal?: AbortSignal): Promise<LocationSummaryDto[]> {
  const response = await fetch(`${API_BASE_URL}/api/locations`, { signal });
  if (!response.ok) throw new Error(await errorDetail(response, "Locations could not be loaded."));
  return response.json() as Promise<LocationSummaryDto[]>;
}

export async function fetchLocationConfig(
  locationId: string,
  signal?: AbortSignal,
): Promise<LocationConfigDto> {
  const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}/config`, { signal });
  if (!response.ok) throw new Error(await errorDetail(response, "Location could not be loaded."));
  return response.json() as Promise<LocationConfigDto>;
}

export async function createLocationConfig(
  request: BuildLocationConfigRequestDto,
): Promise<LocationConfigDto> {
  const response = await fetch(`${API_BASE_URL}/api/locations/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(await errorDetail(response, "Location could not be created."));
  return response.json() as Promise<LocationConfigDto>;
}

export async function deleteLocation(locationId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error(await errorDetail(response, "Location could not be deleted."));
}

export async function addZone(locationId: string, zone: ZoneWriteDto): Promise<ZoneDto> {
  const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}/zones`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(zone),
  });
  if (!response.ok) throw new Error(await errorDetail(response, "Zone could not be added."));
  return response.json() as Promise<ZoneDto>;
}

export async function updateZone(
  locationId: string,
  zoneId: string,
  zone: ZoneWriteDto,
): Promise<ZoneDto> {
  const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}/zones/${zoneId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(zone),
  });
  if (!response.ok) throw new Error(await errorDetail(response, "Zone could not be updated."));
  return response.json() as Promise<ZoneDto>;
}

export async function deleteZone(locationId: string, zoneId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}/zones/${zoneId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error(await errorDetail(response, "Zone could not be deleted."));
}

export async function assignDeviceToZone(
  deviceId: string,
  zoneId: string | null,
): Promise<DeviceDto> {
  const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}/zone`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ zone_id: zoneId }),
  });
  if (!response.ok) throw new Error(await errorDetail(response, "Device could not be assigned."));
  return response.json() as Promise<DeviceDto>;
}

export async function fetchZoneDevices(
  locationId: string,
  zoneId: string,
  signal?: AbortSignal,
): Promise<DeviceDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations/${locationId}/zones/${zoneId}/devices`,
    { signal },
  );
  if (!response.ok) throw new Error(await errorDetail(response, "Zone devices could not be loaded."));
  return response.json() as Promise<DeviceDto[]>;
}
