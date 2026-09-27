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
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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
