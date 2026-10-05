import { useEffect, useState } from "react";
import {
  createSensor,
  fetchSensorReadings,
  fetchSensors,
  readSensor,
  updateDeviceSampling,
  type CreateSensorRequest,
  type ReadingDto,
  type SensorDto,
} from "../../services/api";

type LoadState = "loading" | "ready" | "error";

function formatType(deviceType: string) {
  return deviceType.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

function formatReading(reading: ReadingDto) {
  return `${reading.value.toFixed(2)} ${reading.unit}`;
}

export default function SensorList() {
  const [sensors, setSensors] = useState<SensorDto[]>([]);
  const [latest, setLatest] = useState<Record<string, ReadingDto | undefined>>({});
  const [intervalDrafts, setIntervalDrafts] = useState<Record<string, string>>({});
  const [displayName, setDisplayName] = useState("");
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [creatingType, setCreatingType] = useState<CreateSensorRequest["type"] | null>(null);
  const [busySensor, setBusySensor] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchSensors(controller.signal)
      .then((data) => {
        setSensors(data);
        setIntervalDrafts(
          Object.fromEntries(data.map((sensor) => [sensor.id, String(sensor.sampling_interval_seconds)])),
        );
        setLoadState("ready");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setLoadState("error");
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (sensors.length === 0) return;
    let active = true;

    async function refreshLatest() {
      const entries = await Promise.all(
        sensors.map(async (sensor) => {
          try {
            const readings = await fetchSensorReadings(sensor.id, 1);
            return [sensor.id, readings[0]] as const;
          } catch {
            return [sensor.id, undefined] as const;
          }
        }),
      );
      if (active) setLatest(Object.fromEntries(entries));
    }

    void refreshLatest();
    // Phase 12 replaces this short polling loop with WebSocket updates.
    const timer = window.setInterval(() => void refreshLatest(), 5_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [sensors]);

  async function addSensor(type: CreateSensorRequest["type"]) {
    setCreatingType(type);
    setActionError(null);
    try {
      const sensor = await createSensor({ type, display_name: displayName.trim() || null });
      setSensors((current) => [sensor, ...current]);
      setIntervalDrafts((current) => ({
        ...current,
        [sensor.id]: String(sensor.sampling_interval_seconds),
      }));
      setDisplayName("");
      setLoadState("ready");
    } catch {
      setActionError("The sensor could not be created.");
    } finally {
      setCreatingType(null);
    }
  }

  async function takeReading(sensorId: string) {
    setBusySensor(sensorId);
    setActionError(null);
    try {
      const reading = await readSensor(sensorId);
      setLatest((current) => ({ ...current, [sensorId]: reading }));
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "The sensor could not be read.");
    } finally {
      setBusySensor(null);
    }
  }

  async function saveSampling(sensor: SensorDto, trackingEnabled = sensor.tracking_enabled) {
    const interval = Number(intervalDrafts[sensor.id]);
    if (!Number.isInteger(interval) || interval < 5) {
      setActionError("Sampling interval must be a whole number of at least 5 seconds.");
      return;
    }

    setBusySensor(sensor.id);
    setActionError(null);
    try {
      const settings = await updateDeviceSampling(sensor.id, interval, trackingEnabled);
      setSensors((current) =>
        current.map((item) =>
          item.id === sensor.id
            ? {
                ...item,
                sampling_interval_seconds: settings.sampling_interval_seconds,
                tracking_enabled: settings.tracking_enabled,
              }
            : item,
        ),
      );
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Sampling settings could not be saved.");
    } finally {
      setBusySensor(null);
    }
  }

  return (
    <article
      id="sensors"
      className="rounded-2xl border border-emerald-400/20 bg-slate-900/70 p-6 shadow-xl shadow-black/10 sm:col-span-2 xl:col-span-3"
    >
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
            Factory Method + Adapter
          </p>
          <h3 className="mt-2 text-xl font-semibold text-slate-100">Sensors</h3>
          <p className="mt-2 text-sm text-slate-400">
            Read sensors through adapters and keep every reading in PostgreSQL.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <label className="sr-only" htmlFor="sensor-name">
            Sensor display name
          </label>
          <input
            id="sensor-name"
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            placeholder="Optional display name"
            maxLength={128}
            className="rounded-xl border border-white/10 bg-slate-950 px-4 py-2.5 text-sm text-white outline-none placeholder:text-slate-600 focus:border-emerald-400/60"
          />
          <button
            type="button"
            onClick={() => void addSensor("moisture")}
            disabled={creatingType !== null}
            className="rounded-xl bg-emerald-400 px-4 py-2.5 text-sm font-semibold text-emerald-950 hover:bg-emerald-300 disabled:cursor-wait disabled:opacity-60"
          >
            {creatingType === "moisture" ? "Adding..." : "Add moisture"}
          </button>
          <button
            type="button"
            onClick={() => void addSensor("light")}
            disabled={creatingType !== null}
            className="rounded-xl border border-amber-300/30 bg-amber-300/10 px-4 py-2.5 text-sm font-semibold text-amber-200 hover:bg-amber-300/20 disabled:cursor-wait disabled:opacity-60"
          >
            {creatingType === "light" ? "Adding..." : "Add light"}
          </button>
        </div>
      </div>

      <div className="mt-6" aria-live="polite">
        {actionError && <p className="mb-4 text-sm text-rose-300">{actionError}</p>}
        {loadState === "loading" && <p className="text-sm text-slate-400">Loading sensors...</p>}
        {loadState === "error" && (
          <p className="text-sm text-rose-300">
            Sensors could not be loaded. Check the API and try again.
          </p>
        )}
        {loadState === "ready" && sensors.length === 0 && (
          <p className="text-sm text-slate-400">No sensors yet. Add the first one above.</p>
        )}
        {sensors.length > 0 && (
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sensors.map((sensor) => {
              const reading = latest[sensor.id];
              const isBusy = busySensor === sensor.id;
              return (
                <li key={sensor.id} className="rounded-xl border border-white/10 bg-slate-950/70 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-white">{sensor.display_name}</p>
                      <p className="mt-1 text-xs text-slate-500">{formatType(sensor.device_type)}</p>
                    </div>
                    <span className="rounded-full bg-emerald-400/10 px-2 py-1 text-xs text-emerald-300">
                      {reading?.source ?? "No reading"}
                    </span>
                  </div>

                  <div className="mt-4 rounded-lg bg-slate-900 p-3">
                    <p className="text-lg font-semibold text-white">
                      {reading ? formatReading(reading) : "Waiting for data"}
                    </p>
                    {reading && (
                      <p className="mt-1 text-xs text-slate-500">
                        Stored {new Date(reading.recorded_at).toLocaleString()}
                      </p>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => void takeReading(sensor.id)}
                    disabled={isBusy}
                    className="mt-3 w-full rounded-lg bg-cyan-400 px-3 py-2 text-sm font-semibold text-cyan-950 hover:bg-cyan-300 disabled:cursor-wait disabled:opacity-60"
                  >
                    {isBusy ? "Working..." : "Read now"}
                  </button>

                  <div className="mt-4 border-t border-white/10 pt-4">
                    <label className="text-xs text-slate-400" htmlFor={`interval-${sensor.id}`}>
                      Sampling interval (seconds)
                    </label>
                    <div className="mt-2 flex gap-2">
                      <input
                        id={`interval-${sensor.id}`}
                        type="number"
                        min={5}
                        step={1}
                        value={intervalDrafts[sensor.id] ?? ""}
                        onChange={(event) =>
                          setIntervalDrafts((current) => ({
                            ...current,
                            [sensor.id]: event.target.value,
                          }))
                        }
                        className="min-w-0 flex-1 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400/60"
                      />
                      <button
                        type="button"
                        onClick={() => void saveSampling(sensor)}
                        disabled={isBusy}
                        className="rounded-lg border border-white/10 px-3 py-2 text-sm text-slate-200 hover:bg-white/5 disabled:opacity-60"
                      >
                        Save
                      </button>
                    </div>
                    <label className="mt-3 flex items-center gap-2 text-sm text-slate-300">
                      <input
                        type="checkbox"
                        checked={sensor.tracking_enabled}
                        disabled={isBusy}
                        onChange={(event) => void saveSampling(sensor, event.target.checked)}
                        className="size-4 accent-emerald-400"
                      />
                      Automatic tracking
                    </label>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </article>
  );
}
