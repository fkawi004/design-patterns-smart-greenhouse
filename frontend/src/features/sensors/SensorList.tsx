import { useEffect, useState } from "react";
import {
  createSensor,
  fetchSensors,
  type CreateSensorRequest,
  type SensorDto,
} from "../../services/api";

type LoadState = "loading" | "ready" | "error";

function formatType(deviceType: string) {
  return deviceType.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

export default function SensorList() {
  const [sensors, setSensors] = useState<SensorDto[]>([]);
  const [displayName, setDisplayName] = useState("");
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [creatingType, setCreatingType] = useState<CreateSensorRequest["type"] | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchSensors(controller.signal)
      .then((data) => {
        setSensors(data);
        setLoadState("ready");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setLoadState("error");
      });
    return () => controller.abort();
  }, []);

  async function addSensor(type: CreateSensorRequest["type"]) {
    setCreatingType(type);
    try {
      const sensor = await createSensor({ type, display_name: displayName.trim() || null });
      setSensors((current) => [sensor, ...current]);
      setDisplayName("");
      setLoadState("ready");
    } catch {
      setLoadState("error");
    } finally {
      setCreatingType(null);
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
            Factory Method
          </p>
          <h3 className="mt-2 text-xl font-semibold text-slate-100">Sensors</h3>
          <p className="mt-2 text-sm text-slate-400">
            Add moisture and light sensors with safe type-specific defaults.
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
            {sensors.map((sensor) => (
              <li key={sensor.id} className="rounded-xl border border-white/10 bg-slate-950/70 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-white">{sensor.display_name}</p>
                    <p className="mt-1 text-xs text-slate-500">{formatType(sensor.device_type)}</p>
                  </div>
                  <span className="rounded-full bg-emerald-400/10 px-2 py-1 text-xs text-emerald-300">
                    Saved
                  </span>
                </div>
                <dl className="mt-4 space-y-1 text-xs text-slate-400">
                  {Object.entries(sensor.default_config).map(([key, value]) => (
                    <div key={key} className="flex justify-between gap-4">
                      <dt>{key.replaceAll("_", " ")}</dt>
                      <dd className="text-slate-200">{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              </li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}
