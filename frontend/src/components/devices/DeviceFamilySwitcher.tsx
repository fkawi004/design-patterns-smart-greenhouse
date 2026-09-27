import type { DeviceFamily } from "../../services/api";

interface DeviceFamilySwitcherProps {
  selectedFamily: DeviceFamily;
  disabled?: boolean;
  onChange: (family: DeviceFamily) => void;
}

const families: DeviceFamily[] = ["simulation", "edge"];

export default function DeviceFamilySwitcher({
  selectedFamily,
  disabled = false,
  onChange,
}: DeviceFamilySwitcherProps) {
  return (
    <div className="inline-flex rounded-xl border border-white/10 bg-slate-950 p-1" aria-label="Device family">
      {families.map((family) => (
        <button
          key={family}
          type="button"
          disabled={disabled}
          aria-pressed={selectedFamily === family}
          onClick={() => onChange(family)}
          className={`rounded-lg px-4 py-2 text-sm font-semibold capitalize transition disabled:cursor-wait disabled:opacity-60 ${
            selectedFamily === family
              ? "bg-cyan-300 text-cyan-950"
              : "text-slate-400 hover:text-white"
          }`}
        >
          {family}
        </button>
      ))}
    </div>
  );
}
