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
