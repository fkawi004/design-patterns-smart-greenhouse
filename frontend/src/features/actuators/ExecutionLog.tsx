import { useEffect, useState } from "react";
import {
  fetchActuatorExecutions,
  type ActuatorExecutionDto,
} from "../../services/api";

function shortDeviceId(deviceId: string) {
  return `${deviceId.slice(0, 8)}…`;
}

function messageFrom(error: unknown) {
  return error instanceof Error ? error.message : "Execution log could not be loaded.";
}

export default function ExecutionLog() {
  const [executions, setExecutions] = useState<ActuatorExecutionDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh(signal?: AbortSignal) {
    setLoading(true);
    setError(null);
    try {
      setExecutions(await fetchActuatorExecutions(20, signal));
    } catch (problem) {
      if (problem instanceof DOMException && problem.name === "AbortError") return;
      setError(messageFrom(problem));
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    void refresh(controller.signal);
    return () => controller.abort();
  }, []);

  return (
    <article
      id="executions"
      className="rounded-2xl border border-violet-300/20 bg-slate-900/70 p-6 shadow-xl shadow-black/10 sm:col-span-2 xl:col-span-3"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-300">
            Decorator
          </p>
          <h3 className="mt-2 text-xl font-semibold text-slate-100">Actuator execution log</h3>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
            Commands are not validated until Phase 10. A successful attempt has the logging
            policy and no message. An actuator running for 30 minutes is blocked with maxRunTime
            and logging, with the message Max run time exceeded.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          disabled={loading}
          className="rounded-xl border border-violet-300/30 px-4 py-2 text-sm font-semibold text-violet-200 hover:border-violet-300/60 disabled:cursor-wait disabled:opacity-50"
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {error && (
        <p className="mt-5 rounded-lg bg-rose-400/10 px-3 py-2 text-sm text-rose-200">
          {error}
        </p>
      )}
      {!loading && !error && executions.length === 0 && (
        <p className="mt-6 text-sm text-slate-500">No actuator attempts have been recorded yet.</p>
      )}
      {executions.length > 0 && (
        <div className="mt-6 overflow-x-auto rounded-xl border border-white/10">
          <table className="min-w-full divide-y divide-white/10 text-left text-sm">
            <thead className="bg-slate-950/80 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Time</th>
                <th className="px-4 py-3 font-medium">Device</th>
                <th className="px-4 py-3 font-medium">Result</th>
                <th className="px-4 py-3 font-medium">Policies</th>
                <th className="px-4 py-3 font-medium">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 bg-slate-950/50 text-slate-300">
              {executions.map((execution) => (
                <tr key={execution.id}>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-400">
                    {new Date(execution.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs" title={execution.device_id}>
                    {shortDeviceId(execution.device_id)}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${
                        execution.success
                          ? "bg-emerald-400/10 text-emerald-300"
                          : "bg-rose-400/10 text-rose-300"
                      }`}
                    >
                      {execution.success ? "success" : "blocked"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-violet-200">
                    {execution.policy_applied.join(", ")}
                  </td>
                  <td className="px-4 py-3 text-slate-400">{execution.message ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
}
