import { useEffect, useState } from "react";
import {
  fetchDevices,
  provisionDeviceFamily,
  type DeviceDto,
  type DeviceFamily,
} from "../../services/api";
import DeviceFamilySwitcher from "./DeviceFamilySwitcher";

type LoadState = "loading" | "ready" | "error";

function formatLabel(value: string) {
  return value.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

export default function DeviceList() {
  const [family, setFamily] = useState<DeviceFamily>("simulation");
  const [devices, setDevices] = useState<DeviceDto[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [isProvisioning, setIsProvisioning] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setLoadState("loading");
    fetchDevices(family, undefined, controller.signal)
      .then((data) => {
        setDevices(data);
        setLoadState("ready");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setLoadState("error");
      });
    return () => controller.abort();
  }, [family]);

  async function provisionFamily() {
    setIsProvisioning(true);
    try {
      await provisionDeviceFamily(family);
      setDevices(await fetchDevices(family));
      setLoadState("ready");
    } catch {
      setLoadState("error");
    } finally {
      setIsProvisioning(false);
    }
  }

  return (
    <article
      id="devices"
      className="rounded-2xl border border-cyan-300/20 bg-slate-900/70 p-6 shadow-xl shadow-black/10 sm:col-span-2 xl:col-span-3"
    >
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">
            Abstract Factory
          </p>
          <h3 className="mt-2 text-xl font-semibold text-slate-100">Devices</h3>
          <p className="mt-2 text-sm text-slate-400">
            Provision a matching family of two sensors and two actuators.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <DeviceFamilySwitcher
            selectedFamily={family}
            disabled={isProvisioning}
            onChange={setFamily}
          />
          <button
            type="button"
            onClick={() => void provisionFamily()}
            disabled={isProvisioning}
            className="rounded-xl bg-cyan-300 px-4 py-2.5 text-sm font-semibold text-cyan-950 hover:bg-cyan-200 disabled:cursor-wait disabled:opacity-60"
          >
            {isProvisioning ? "Provisioning..." : `Provision ${family} kit`}
          </button>
        </div>
      </div>

      <div className="mt-6" aria-live="polite">
        {loadState === "loading" && <p className="text-sm text-slate-400">Loading devices...</p>}
        {loadState === "error" && (
          <p className="text-sm text-rose-300">
            Devices could not be loaded. Check the API and try again.
          </p>
        )}
        {loadState === "ready" && devices.length === 0 && (
          <p className="text-sm text-slate-400">
            No {family} devices yet. Provision the first kit above.
          </p>
        )}
        {loadState === "ready" && devices.length > 0 && (
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {devices.map((device) => (
              <li key={device.id} className="rounded-xl border border-white/10 bg-slate-950/70 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-white">{device.display_name}</p>
                    <p className="mt-1 text-xs text-slate-500">{formatLabel(device.device_type)}</p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span
                      className={`rounded-full px-2 py-1 text-xs ${
                        device.role === "sensor"
                          ? "bg-emerald-400/10 text-emerald-300"
                          : "bg-amber-300/10 text-amber-200"
                      }`}
                    >
                      {device.role}
                    </span>
                    <span className="rounded-full bg-cyan-300/10 px-2 py-1 text-xs text-cyan-200">
                      {device.device_family}
                    </span>
                  </div>
                </div>
                <dl className="mt-4 space-y-1 text-xs text-slate-400">
                  {Object.entries(device.default_config).map(([key, value]) => (
                    <div key={key} className="flex justify-between gap-4">
                      <dt>{key.replaceAll("_", " ")}</dt>
                      <dd className="max-w-32 truncate text-slate-200" title={String(value)}>
                        {String(value)}
                      </dd>
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
