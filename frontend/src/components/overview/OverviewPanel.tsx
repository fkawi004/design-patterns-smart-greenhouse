import { useEffect, useState } from "react";
import {
  fetchLocationOverview,
  fetchLocations,
  type LocationOverviewDto,
  type LocationSummaryDto,
} from "../../services/api";

function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "Overview could not be loaded.";
}

export default function OverviewPanel() {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([]);
  const [locationId, setLocationId] = useState("");
  const [overview, setOverview] = useState<LocationOverviewDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    function loadLocations() {
      void fetchLocations()
        .then((items) => {
          if (active) setLocations(items);
        })
        .catch((problem: unknown) => {
          if (active) setError(messageFrom(problem));
        });
    }
    loadLocations();
    window.addEventListener("locations-changed", loadLocations);
    return () => {
      active = false;
      window.removeEventListener("locations-changed", loadLocations);
    };
  }, []);

  useEffect(() => {
    setOverview(null);
    setError(null);
    if (!locationId) return;
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    fetchLocationOverview(locationId, controller.signal)
      .then((data) => {
        if (active) setOverview(data);
      })
      .catch((problem: unknown) => {
        if (active && !(problem instanceof DOMException && problem.name === "AbortError")) {
          setError(messageFrom(problem));
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [locationId]);

  async function refresh() {
    if (!locationId) return;
    setLoading(true);
    setError(null);
    try {
      setOverview(await fetchLocationOverview(locationId));
    } catch (problem) {
      setError(messageFrom(problem));
    } finally {
      setLoading(false);
    }
  }

  return (
    <article
      id="overview"
      className="rounded-2xl border border-sky-300/20 bg-slate-900/70 p-6 shadow-xl shadow-black/10 sm:col-span-2 xl:col-span-3"
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-300">Facade</p>
          <h3 className="mt-2 text-xl font-semibold text-slate-100">Location overview</h3>
          <p className="mt-2 text-sm text-slate-400">
            One API snapshot of zones, assigned devices, readings, and automation.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="text-xs text-slate-400">
            Location
            <select
              value={locationId}
              onChange={(event) => setLocationId(event.target.value)}
              className="mt-1 min-w-64 rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
            >
              <option value="">Select a location</option>
              {locations.map((location) => (
                <option key={location.id} value={location.id}>{location.name}</option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => void refresh()}
            disabled={!locationId || loading}
            className="rounded-lg bg-sky-300 px-4 py-2 text-sm font-semibold text-sky-950 disabled:opacity-40"
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
      </div>

      {error && <p className="mt-4 rounded-lg bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{error}</p>}
      {!locationId && <p className="mt-5 text-sm text-slate-500">Select a location to load its overview.</p>}

      {overview && (
        <div className="mt-6 space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl bg-slate-950/70 p-4">
              <p className="text-xs text-slate-500">Assigned sensors</p>
              <p className="mt-1 text-2xl font-semibold text-white">{overview.device_counts.sensor}</p>
            </div>
            <div className="rounded-xl bg-slate-950/70 p-4">
              <p className="text-xs text-slate-500">Assigned actuators</p>
              <p className="mt-1 text-2xl font-semibold text-white">{overview.device_counts.actuator}</p>
            </div>
            <div className="rounded-xl bg-slate-950/70 p-4">
              <p className="text-xs text-slate-500">Saved strategy</p>
              <p className="mt-1 text-sm font-semibold text-white">
                {overview.strategy_key ?? "No strategy saved"}
              </p>
            </div>
            <div className="rounded-xl bg-slate-950/70 p-4">
              <p className="text-xs text-slate-500">Recommendation</p>
              <p className="mt-1 text-sm font-semibold text-white">
                {overview.last_recommendation?.action ?? "No recommendation"}
              </p>
            </div>
          </div>

          {overview.last_recommendation && (
            <p className="rounded-xl border border-sky-300/15 bg-sky-300/5 px-4 py-3 text-sm leading-6 text-slate-300">
              {overview.last_recommendation.reason}
            </p>
          )}

          <div className="grid gap-3 lg:grid-cols-2">
            {overview.zones.map((zone) => {
              const readings = new Map(zone.latest_readings.map((reading) => [reading.device_id, reading]));
              return (
                <section key={zone.id} className="rounded-xl border border-white/10 bg-slate-950/60 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <h4 className="font-semibold text-white">{zone.name}</h4>
                    <span className="text-xs text-slate-500">
                      VWC {zone.moisture_threshold_low.toFixed(2)}–{zone.moisture_threshold_high.toFixed(2)}
                    </span>
                  </div>
                  {zone.devices.length === 0 ? (
                    <p className="mt-4 text-sm text-slate-500">No assigned devices.</p>
                  ) : (
                    <ul className="mt-4 space-y-3">
                      {zone.devices.map((device) => {
                        const reading = readings.get(device.id);
                        return (
                          <li key={device.id} className="rounded-lg bg-slate-900 p-3">
                            <div className="flex flex-wrap items-start justify-between gap-2">
                              <div>
                                <p className="text-sm font-medium text-white">{device.display_name}</p>
                                <p className="mt-1 text-xs text-slate-500">
                                  {device.role} · {device.device_type.replaceAll("_", " ")}
                                </p>
                              </div>
                              <span className="text-sm font-semibold text-sky-200">
                                {reading ? `${reading.value.toFixed(2)} ${reading.unit}` : "No reading"}
                              </span>
                            </div>
                            {reading && (
                              <p className="mt-2 text-xs text-slate-500">
                                Tracking {reading.tracking_enabled ? "on" : "off"} · every {reading.sampling_interval_seconds}s · {new Date(reading.recorded_at).toLocaleString()}
                              </p>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </section>
              );
            })}
          </div>
        </div>
      )}
    </article>
  );
}
