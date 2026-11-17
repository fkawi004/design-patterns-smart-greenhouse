import { useEffect, useState } from "react";
import {
  executeCommand,
  fetchCommandHistory,
  fetchDevices,
  type CommandLogDto,
  type CommandType,
  type DeviceDto,
} from "../../services/api";

function shortDeviceId(deviceId: string) {
  return `${deviceId.slice(0, 8)}…`;
}

function formatLabel(value: string) {
  return value.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "The command could not be executed.";
}

const statusClasses: Record<string, string> = {
  success: "bg-emerald-400/10 text-emerald-300",
  failed: "bg-rose-400/10 text-rose-300",
  rejected: "bg-amber-300/10 text-amber-200",
};

export default function CommandPanel() {
  const [actuators, setActuators] = useState<DeviceDto[]>([]);
  const [history, setHistory] = useState<CommandLogDto[]>([]);
  const [levels, setLevels] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh(signal?: AbortSignal) {
    setLoading(true);
    setError(null);
    try {
      const [nextActuators, nextHistory] = await Promise.all([
        fetchDevices(undefined, "actuator", signal),
        fetchCommandHistory(50, signal),
      ]);
      setActuators(nextActuators);
      setHistory(nextHistory);
    } catch (problem) {
      if (problem instanceof DOMException && problem.name === "AbortError") return;
      setError(errorMessage(problem));
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    void refresh(controller.signal);
    return () => controller.abort();
  }, []);

  async function runCommand(
    device: DeviceDto,
    commandType: CommandType,
    payload: Record<string, unknown> = {},
  ) {
    const actionKey = `${device.id}:${commandType}`;
    setActiveAction(actionKey);
    setFeedback(null);
    setError(null);
    try {
      const result = await executeCommand(commandType, device.id, payload);
      setFeedback(
        `${formatLabel(commandType)} for ${device.display_name}: ${result.status}.`,
      );
      await refresh();
      window.dispatchEvent(new Event("actuator-state-changed"));
      window.dispatchEvent(new Event("actuator-executions-changed"));
    } catch (problem) {
      setError(errorMessage(problem));
    } finally {
      setActiveAction(null);
    }
  }

  return (
    <article
      id="controls"
      className="rounded-2xl border border-fuchsia-300/20 bg-slate-900/70 p-6 shadow-xl shadow-black/10 sm:col-span-2 xl:col-span-3"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-fuchsia-300">
            Command
          </p>
          <h3 className="mt-2 text-xl font-semibold text-slate-100">Actuator controls</h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Each action is a command object. State decides whether it is allowed, and every
            accepted, failed, or rejected request is saved below.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          disabled={loading || activeAction !== null}
          className="rounded-xl border border-fuchsia-300/30 px-4 py-2 text-sm font-semibold text-fuchsia-200 hover:border-fuchsia-300/60 disabled:cursor-wait disabled:opacity-50"
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {feedback && <p className="mt-5 text-sm text-emerald-300">{feedback}</p>}
      {error && <p className="mt-5 text-sm text-rose-300">{error}</p>}

      {!loading && actuators.length === 0 && (
        <p className="mt-6 text-sm text-slate-500">Provision a device family to add actuators.</p>
      )}
      {actuators.length > 0 && (
        <ul className="mt-6 grid gap-3 md:grid-cols-2">
          {actuators.map((device) => (
            <li key={device.id} className="rounded-xl border border-white/10 bg-slate-950/60 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-100">{device.display_name}</p>
                  <p className="mt-1 text-xs text-slate-500">{formatLabel(device.device_type)}</p>
                </div>
                <span className="rounded-full bg-slate-400/10 px-2 py-1 text-xs text-slate-300">
                  {device.state}
                </span>
              </div>

              {device.device_type === "water_pump" && (
                <div className="mt-4 flex gap-2">
                  {(["start_pump", "stop_pump"] as const).map((commandType) => (
                    <button
                      key={commandType}
                      type="button"
                      onClick={() => void runCommand(device, commandType)}
                      disabled={
                        activeAction !== null || !device.allowed_commands.includes(commandType)
                      }
                      className="rounded-lg bg-fuchsia-300 px-3 py-2 text-xs font-semibold text-fuchsia-950 hover:bg-fuchsia-200 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500"
                    >
                      {activeAction === `${device.id}:${commandType}`
                        ? "Working..."
                        : formatLabel(commandType)}
                    </button>
                  ))}
                </div>
              )}

              {device.device_type === "grow_light" && (
                <div className="mt-4 flex items-end gap-2">
                  <label className="text-xs text-slate-400">
                    Light level
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={levels[device.id] ?? 1}
                      onChange={(event) =>
                        setLevels((current) => ({
                          ...current,
                          [device.id]: Number(event.target.value),
                        }))
                      }
                      className="mt-1 w-24 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      void runCommand(device, "set_light_level", {
                        level: levels[device.id] ?? 1,
                      })
                    }
                    disabled={
                      activeAction !== null ||
                      !device.allowed_commands.includes("set_light_level")
                    }
                    className="rounded-lg bg-fuchsia-300 px-3 py-2 text-xs font-semibold text-fuchsia-950 hover:bg-fuchsia-200 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500"
                  >
                    {activeAction === `${device.id}:set_light_level`
                      ? "Working..."
                      : "Set level"}
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      <h4 className="mt-8 text-sm font-semibold uppercase tracking-wide text-slate-300">
        Command history
      </h4>
      {!loading && history.length === 0 && (
        <p className="mt-3 text-sm text-slate-500">No actuator commands have been submitted yet.</p>
      )}
      {history.length > 0 && (
        <div className="mt-3 overflow-x-auto rounded-xl border border-white/10">
          <table className="min-w-full divide-y divide-white/10 text-left text-sm">
            <thead className="bg-slate-950/80 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Time</th>
                <th className="px-4 py-3 font-medium">Device</th>
                <th className="px-4 py-3 font-medium">Command</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Payload</th>
                <th className="px-4 py-3 font-medium">Error</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 bg-slate-950/50 text-slate-300">
              {history.map((entry) => (
                <tr key={entry.id}>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-400">
                    {new Date(entry.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs" title={entry.device_id}>
                    {shortDeviceId(entry.device_id)}
                  </td>
                  <td className="px-4 py-3">{formatLabel(entry.command_type)}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-1 text-xs ${statusClasses[entry.status]}`}>
                      {entry.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-400">
                    {JSON.stringify(entry.payload)}
                  </td>
                  <td className="px-4 py-3 text-slate-400">{entry.error_message ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
}
