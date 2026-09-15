import SensorList from "../features/sensors/SensorList";

const sections = [
  { id: "overview", title: "Overview", copy: "At-a-glance greenhouse conditions and trends." },
  { id: "controls", title: "Controls", copy: "Manual greenhouse controls will live here." },
  { id: "automation", title: "Automation", copy: "Rules and scheduled actions are coming later." },
  { id: "events", title: "Events", copy: "System activity and alerts will appear here." },
  { id: "configuration", title: "Configuration", copy: "Greenhouse and device settings will live here." },
];

export default function DashboardPage() {
  return (
    <section aria-labelledby="dashboard-title">
      <p className="text-sm font-medium text-emerald-400">Phase 2 · Factory Method</p>
      <h2 id="dashboard-title" className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
        Greenhouse dashboard
      </h2>
      <p className="mt-3 max-w-2xl text-slate-400">
        The three-tier foundation is running. Each section is ready for behaviour introduced in later design-pattern phases.
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <SensorList />
        {sections.map((section) => (
          <article
            id={section.id}
            key={section.id}
            className="min-h-44 rounded-2xl border border-white/10 bg-slate-900/70 p-6 shadow-xl shadow-black/10"
          >
            <div className="flex items-start justify-between gap-4">
              <h3 className="text-lg font-semibold text-slate-100">{section.title}</h3>
              <span className="rounded-full bg-slate-800 px-2.5 py-1 text-xs text-slate-400">Placeholder</span>
            </div>
            <p className="mt-5 text-sm leading-6 text-slate-400">{section.copy}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
