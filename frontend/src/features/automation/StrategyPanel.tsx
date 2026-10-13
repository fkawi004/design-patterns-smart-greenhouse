import { useEffect, useState } from "react";
import {
  evaluateLocationAutomation,
  fetchLocations,
  fetchLocationStrategy,
  saveLocationStrategy,
  type AutomationStrategyKey,
  type LocationSummaryDto,
  type RecommendationDto,
} from "../../services/api";

function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export default function StrategyPanel() {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([]);
  const [locationId, setLocationId] = useState("");
  const [strategyKey, setStrategyKey] = useState<AutomationStrategyKey>("conservative");
  const [recommendation, setRecommendation] = useState<RecommendationDto | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    function loadLocations() {
      void fetchLocations()
        .then((data) => {
          if (active) setLocations(data);
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
    setRecommendation(null);
    setMessage(null);
    setError(null);
    if (!locationId) return;
    const controller = new AbortController();
    fetchLocationStrategy(locationId, controller.signal)
      .then((saved) => setStrategyKey(saved.strategy_key))
      .catch((problem: unknown) => {
        if (!(problem instanceof DOMException && problem.name === "AbortError")) {
          setError(messageFrom(problem));
        }
      });
    return () => controller.abort();
  }, [locationId]);

  async function save() {
    if (!locationId) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const saved = await saveLocationStrategy(locationId, strategyKey);
      setStrategyKey(saved.strategy_key);
      setRecommendation(null);
      setMessage("Strategy saved. The next evaluation will use it.");
    } catch (problem) {
      setError(messageFrom(problem));
    } finally {
      setBusy(false);
    }
  }

  async function evaluate() {
    if (!locationId) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await evaluateLocationAutomation(locationId);
      setRecommendation(result);
      setStrategyKey(result.strategy_key);
    } catch (problem) {
      setError(messageFrom(problem));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article
      id="automation"
      className="min-h-44 rounded-2xl border border-cyan-300/20 bg-slate-900/70 p-6 shadow-xl shadow-black/10 sm:col-span-2 xl:col-span-3"
    >
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Strategy</p>
      <h3 className="mt-2 text-xl font-semibold text-slate-100">Location automation</h3>
      <p className="mt-2 text-sm text-slate-400">
        Save an irrigation policy and evaluate the latest readings against each zone's thresholds.
      </p>

      <div className="mt-5 grid gap-3 md:grid-cols-[1fr_1fr_auto_auto] md:items-end">
        <label className="text-xs text-slate-400">
          Location
          <select
            value={locationId}
            onChange={(event) => setLocationId(event.target.value)}
            className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
          >
            <option value="">Select a location</option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>{location.name}</option>
            ))}
          </select>
        </label>
        <label className="text-xs text-slate-400">
          Irrigation strategy
          <select
            value={strategyKey}
            onChange={(event) => setStrategyKey(event.target.value as AutomationStrategyKey)}
            disabled={!locationId || busy}
            className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            <option value="conservative">Conservative</option>
            <option value="aggressive">Aggressive</option>
          </select>
        </label>
        <button
          type="button"
          onClick={() => void save()}
          disabled={!locationId || busy}
          className="rounded-lg border border-cyan-300/30 px-4 py-2 text-sm font-semibold text-cyan-200 hover:bg-cyan-300/10 disabled:opacity-40"
        >
          Save strategy
        </button>
        <button
          type="button"
          onClick={() => void evaluate()}
          disabled={!locationId || busy}
          className="rounded-lg bg-cyan-300 px-4 py-2 text-sm font-semibold text-cyan-950 hover:bg-cyan-200 disabled:opacity-40"
        >
          {busy ? "Working..." : "Evaluate"}
        </button>
      </div>

      {(message || error) && (
        <p className={`mt-4 rounded-lg px-3 py-2 text-sm ${error ? "bg-rose-400/10 text-rose-200" : "bg-emerald-400/10 text-emerald-200"}`}>
          {error ?? message}
        </p>
      )}

      {recommendation && (
        <div className="mt-4 rounded-xl border border-white/10 bg-slate-950/70 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${recommendation.action === "irrigate" ? "bg-blue-400/15 text-blue-200" : "bg-emerald-400/15 text-emerald-200"}`}>
              {recommendation.action}
            </span>
            <span className="text-xs text-slate-500">{recommendation.strategy_key}</span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-300">{recommendation.reason}</p>
        </div>
      )}
    </article>
  );
}
