import { useEffect, useState, type FormEvent } from "react";
import {
  addZone,
  createLocationConfig,
  deleteLocation,
  deleteZone,
  fetchLocationConfig,
  fetchLocations,
  fetchZoneDevices,
  updateZone,
  type DeviceDto,
  type LocationConfigDto,
  type LocationSummaryDto,
  type ZoneDto,
  type ZoneWriteDto,
} from "../../services/api";

interface ZoneDraft {
  key: string;
  name: string;
  low: string;
  high: string;
  watering: string;
}

function emptyZone(): ZoneDraft {
  return { key: crypto.randomUUID(), name: "", low: "0.2", high: "0.5", watering: "" };
}

function zoneDraftFrom(zone: ZoneDto): ZoneDraft {
  return {
    key: zone.id,
    name: zone.name,
    low: String(zone.moisture_threshold_low),
    high: String(zone.moisture_threshold_high),
    watering: typeof zone.schedule.watering === "string" ? zone.schedule.watering : "",
  };
}

function validateZone(draft: ZoneDraft): string | null {
  const low = Number(draft.low);
  const high = Number(draft.high);
  if (!draft.name.trim()) return "Every zone needs a name.";
  if (!Number.isFinite(low) || !Number.isFinite(high)) return "Thresholds must be numbers.";
  if (low < 0 || high > 1) return "Thresholds must stay between 0 and 1.";
  if (low >= high) return "The low threshold must be less than the high threshold.";
  return null;
}

function zoneRequest(draft: ZoneDraft): ZoneWriteDto {
  return {
    name: draft.name.trim(),
    moisture_threshold_low: Number(draft.low),
    moisture_threshold_high: Number(draft.high),
    schedule: draft.watering.trim() ? { watering: draft.watering.trim() } : {},
  };
}

function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

interface ZoneFieldsProps {
  draft: ZoneDraft;
  onChange: (draft: ZoneDraft) => void;
}

function ZoneFields({ draft, onChange }: ZoneFieldsProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <label className="text-xs text-slate-400">
        Zone name
        <input
          value={draft.name}
          onChange={(event) => onChange({ ...draft, name: event.target.value })}
          className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
        />
      </label>
      <label className="text-xs text-slate-400">
        Low VWC
        <input
          type="number"
          min="0"
          max="1"
          step="0.01"
          value={draft.low}
          onChange={(event) => onChange({ ...draft, low: event.target.value })}
          className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
        />
      </label>
      <label className="text-xs text-slate-400">
        High VWC
        <input
          type="number"
          min="0"
          max="1"
          step="0.01"
          value={draft.high}
          onChange={(event) => onChange({ ...draft, high: event.target.value })}
          className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
        />
      </label>
      <label className="text-xs text-slate-400">
        Watering time
        <input
          type="time"
          value={draft.watering}
          onChange={(event) => onChange({ ...draft, watering: event.target.value })}
          className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
        />
      </label>
    </div>
  );
}

interface SavedZoneEditorProps {
  zone: ZoneDto;
  devices: DeviceDto[];
  canDelete: boolean;
  onSave: (zone: ZoneDto, draft: ZoneDraft) => Promise<void>;
  onDelete: (zone: ZoneDto) => Promise<void>;
}

function SavedZoneEditor({ zone, devices, canDelete, onSave, onDelete }: SavedZoneEditorProps) {
  const [draft, setDraft] = useState(() => zoneDraftFrom(zone));
  const [validation, setValidation] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => setDraft(zoneDraftFrom(zone)), [zone]);

  async function save() {
    const problem = validateZone(draft);
    setValidation(problem);
    if (problem) return;
    setBusy(true);
    try {
      await onSave(zone, draft);
    } finally {
      setBusy(false);
    }
  }

  return (
    <li className="rounded-xl border border-white/10 bg-slate-950/70 p-4">
      <ZoneFields draft={draft} onChange={setDraft} />
      {validation && <p className="mt-2 text-xs text-rose-300">{validation}</p>}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-400">
          Devices: {devices.length ? devices.map((device) => device.display_name).join(", ") : "None"}
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => void save()}
            className="rounded-lg bg-cyan-300 px-3 py-2 text-xs font-semibold text-cyan-950 disabled:opacity-50"
          >
            Save zone
          </button>
          <button
            type="button"
            disabled={busy || !canDelete}
            title={canDelete ? "Delete zone" : "A location must keep one zone"}
            onClick={() => void onDelete(zone)}
            className="rounded-lg border border-rose-300/30 px-3 py-2 text-xs text-rose-200 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Delete zone
          </button>
        </div>
      </div>
    </li>
  );
}

export default function LocationConfigWizard() {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [config, setConfig] = useState<LocationConfigDto | null>(null);
  const [zoneDevices, setZoneDevices] = useState<Record<string, DeviceDto[]>>({});
  const [locationName, setLocationName] = useState("");
  const [newZones, setNewZones] = useState<ZoneDraft[]>(() => [emptyZone()]);
  const [zoneToAdd, setZoneToAdd] = useState<ZoneDraft>(() => emptyZone());
  const [validation, setValidation] = useState<string | null>(null);
  const [apiMessage, setApiMessage] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetchLocations(controller.signal)
      .then(setLocations)
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setApiMessage(messageFrom(error));
        }
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setConfig(null);
      setZoneDevices({});
      return;
    }
    const controller = new AbortController();
    fetchLocationConfig(selectedId, controller.signal)
      .then(async (loaded) => {
        const devicePairs = await Promise.all(
          loaded.zones.map(async (zone) => [
            zone.id,
            await fetchZoneDevices(loaded.location.id, zone.id, controller.signal),
          ] as const),
        );
        setConfig(loaded);
        setZoneDevices(Object.fromEntries(devicePairs));
      })
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setApiMessage(messageFrom(error));
        }
      });
    return () => controller.abort();
  }, [selectedId]);

  useEffect(() => {
    if (!selectedId) return;
    let active = true;
    function refreshAssignmentLists() {
      void fetchLocationConfig(selectedId)
        .then(async (loaded) => {
          const devicePairs = await Promise.all(
            loaded.zones.map(async (zone) => [
              zone.id,
              await fetchZoneDevices(loaded.location.id, zone.id),
            ] as const),
          );
          if (active) setZoneDevices(Object.fromEntries(devicePairs));
        })
        .catch((error: unknown) => {
          if (active) setApiMessage(messageFrom(error));
        });
    }
    window.addEventListener("device-assignments-changed", refreshAssignmentLists);
    return () => {
      active = false;
      window.removeEventListener("device-assignments-changed", refreshAssignmentLists);
    };
  }, [selectedId]);

  async function reloadSelected() {
    if (!selectedId) return;
    const loaded = await fetchLocationConfig(selectedId);
    const devicePairs = await Promise.all(
      loaded.zones.map(async (zone) => [
        zone.id,
        await fetchZoneDevices(loaded.location.id, zone.id),
      ] as const),
    );
    setConfig(loaded);
    setZoneDevices(Object.fromEntries(devicePairs));
    window.dispatchEvent(new Event("locations-changed"));
  }

  function validateNewLocation(): string | null {
    if (!locationName.trim()) return "Location name is required.";
    if (!newZones.length) return "Add at least one zone.";
    for (const zone of newZones) {
      const problem = validateZone(zone);
      if (problem) return problem;
    }
    const names = newZones.map((zone) => zone.name.trim().toLowerCase());
    if (new Set(names).size !== names.length) return "Zone names must be unique.";
    return null;
  }

  async function createLocation(event: FormEvent) {
    event.preventDefault();
    const problem = validateNewLocation();
    setValidation(problem);
    if (problem) return;
    setBusy(true);
    setApiMessage(null);
    setSuccess(null);
    try {
      const created = await createLocationConfig({
        location_name: locationName.trim(),
        zones: newZones.map(zoneRequest),
      });
      setLocations(await fetchLocations());
      setLocationName("");
      setNewZones([emptyZone()]);
      setSelectedId(created.location.id);
      setSuccess("Location configuration saved.");
      window.dispatchEvent(new Event("locations-changed"));
    } catch (error) {
      setApiMessage(messageFrom(error));
    } finally {
      setBusy(false);
    }
  }

  async function removeSelectedLocation() {
    if (!config || !window.confirm(`Delete ${config.location.name} and its zones?`)) return;
    setBusy(true);
    setApiMessage(null);
    try {
      await deleteLocation(config.location.id);
      setLocations(await fetchLocations());
      setSelectedId("");
      setConfig(null);
      setZoneDevices({});
      setSuccess("Location deleted. Assigned devices are now unassigned.");
      window.dispatchEvent(new Event("locations-changed"));
    } catch (error) {
      setApiMessage(messageFrom(error));
    } finally {
      setBusy(false);
    }
  }

  async function addZoneToSelection() {
    if (!config) return;
    const problem = validateZone(zoneToAdd);
    setValidation(problem);
    if (problem) return;
    setBusy(true);
    setApiMessage(null);
    try {
      await addZone(config.location.id, zoneRequest(zoneToAdd));
      setZoneToAdd(emptyZone());
      await reloadSelected();
      setSuccess("Zone added.");
    } catch (error) {
      setApiMessage(messageFrom(error));
    } finally {
      setBusy(false);
    }
  }

  async function saveZone(zone: ZoneDto, draft: ZoneDraft) {
    if (!config) return;
    setApiMessage(null);
    try {
      await updateZone(config.location.id, zone.id, zoneRequest(draft));
      await reloadSelected();
      setSuccess("Zone updated.");
    } catch (error) {
      setApiMessage(messageFrom(error));
    }
  }

  async function removeZone(zone: ZoneDto) {
    if (!config || !window.confirm(`Delete zone ${zone.name}?`)) return;
    setApiMessage(null);
    try {
      await deleteZone(config.location.id, zone.id);
      await reloadSelected();
      setSuccess("Zone deleted. Its devices are now unassigned.");
    } catch (error) {
      setApiMessage(messageFrom(error));
    }
  }

  return (
    <article
      id="configuration"
      className="rounded-2xl border border-violet-300/20 bg-slate-900/70 p-6 shadow-xl shadow-black/10 sm:col-span-2 xl:col-span-3"
    >
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-300">Builder</p>
      <h3 className="mt-2 text-xl font-semibold text-slate-100">Location configuration</h3>
      <p className="mt-2 text-sm text-slate-400">
        Build a valid location with zones, then manage saved zones and assignments separately.
      </p>

      {(apiMessage || success) && (
        <p className={`mt-4 rounded-lg px-3 py-2 text-sm ${apiMessage ? "bg-rose-400/10 text-rose-200" : "bg-emerald-400/10 text-emerald-200"}`}>
          {apiMessage ?? success}
        </p>
      )}

      <form onSubmit={(event) => void createLocation(event)} className="mt-6 rounded-xl border border-white/10 p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex-1 text-xs text-slate-400">
            New location name
            <input
              value={locationName}
              onChange={(event) => setLocationName(event.target.value)}
              className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              placeholder="Main greenhouse"
            />
          </label>
          <button
            type="submit"
            disabled={busy}
            className="rounded-lg bg-violet-300 px-4 py-2 text-sm font-semibold text-violet-950 disabled:opacity-50"
          >
            Build and save
          </button>
        </div>
        <div className="mt-4 space-y-3">
          {newZones.map((zone, index) => (
            <div key={zone.key} className="rounded-lg bg-slate-950/60 p-3">
              <ZoneFields
                draft={zone}
                onChange={(next) => setNewZones((items) => items.map((item) => item.key === next.key ? next : item))}
              />
              <button
                type="button"
                disabled={newZones.length === 1}
                onClick={() => setNewZones((items) => items.filter((item) => item.key !== zone.key))}
                className="mt-2 text-xs text-rose-300 disabled:opacity-30"
              >
                Remove zone {index + 1}
              </button>
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={() => setNewZones((items) => [...items, emptyZone()])}
          className="mt-3 text-sm font-medium text-violet-300"
        >
          + Add another zone
        </button>
        {validation && <p className="mt-3 text-sm text-rose-300">{validation}</p>}
      </form>

      <div className="mt-6 grid gap-5 lg:grid-cols-[18rem_1fr]">
        <div>
          <label className="text-xs text-slate-400">
            Saved locations
            <select
              value={selectedId}
              onChange={(event) => {
                setSelectedId(event.target.value);
                setApiMessage(null);
                setSuccess(null);
              }}
              className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
            >
              <option value="">Select a location</option>
              {locations.map((location) => (
                <option key={location.id} value={location.id}>{location.name}</option>
              ))}
            </select>
          </label>
          {locations.length === 0 && <p className="mt-2 text-xs text-slate-500">No saved locations yet.</p>}
          {config && (
            <button
              type="button"
              disabled={busy}
              onClick={() => void removeSelectedLocation()}
              className="mt-3 rounded-lg border border-rose-300/30 px-3 py-2 text-xs text-rose-200 disabled:opacity-50"
            >
              Delete selected location
            </button>
          )}
        </div>

        {config ? (
          <div>
            <p className="text-sm font-medium text-white">{config.location.name}</p>
            <p className="mt-1 break-all text-xs text-slate-500">ID: {config.location.id}</p>
            <ul className="mt-4 space-y-3">
              {config.zones.map((zone) => (
                <SavedZoneEditor
                  key={zone.id}
                  zone={zone}
                  devices={zoneDevices[zone.id] ?? []}
                  canDelete={config.zones.length > 1}
                  onSave={saveZone}
                  onDelete={removeZone}
                />
              ))}
            </ul>
            <div className="mt-4 rounded-xl border border-dashed border-white/15 p-4">
              <p className="mb-3 text-sm font-medium text-slate-200">Add a zone</p>
              <ZoneFields draft={zoneToAdd} onChange={setZoneToAdd} />
              <button
                type="button"
                disabled={busy}
                onClick={() => void addZoneToSelection()}
                className="mt-3 rounded-lg bg-slate-700 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
              >
                Add zone
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Select a saved location to manage its zones.</p>
        )}
      </div>
    </article>
  );
}
