import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import type { Persona } from "../types";
import { FullLockupImage, PROJECT_FORMER_NAMES } from "../components/Logo";

export function Settings({
  theme, onThemeChange, monitoringEnabled, onMonitoringChange, defaultPersonaId, onDefaultPersonaChange,
}: {
  theme: "dark" | "light";
  onThemeChange: (t: "dark" | "light") => void;
  monitoringEnabled: boolean;
  onMonitoringChange: (v: boolean) => void;
  defaultPersonaId: string | null;
  onDefaultPersonaChange: (id: string | null) => void;
}) {
  const personas = useQuery({ queryKey: ["personas"], queryFn: api.listPersonas });
  const health = useQuery({ queryKey: ["health"], queryFn: api.health });
  const providerHealth = useQuery({ queryKey: ["provider-health"], queryFn: api.providerHealth });

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-8">
      <h1 className="text-xl font-semibold text-slate-100">Settings</h1>
      <p className="text-sm text-slate-500">
        Stored locally in this browser — there's no user-account system yet, so these aren't synced across devices.
      </p>

      <section className="space-y-3 rounded-xl border border-lab-border bg-lab-panel p-4">
        <h2 className="text-sm font-medium text-slate-200">General</h2>
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Theme</span>
          <select
            value={theme}
            onChange={(e) => onThemeChange(e.target.value as "dark" | "light")}
            className="rounded-lg border border-lab-border bg-lab-bg px-3 py-1.5 text-sm text-slate-200"
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </div>
      </section>

      <section className="space-y-3 rounded-xl border border-lab-border bg-lab-panel p-4">
        <h2 className="text-sm font-medium text-slate-200">Persona</h2>
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Default persona for new chats</span>
          <select
            value={defaultPersonaId ?? ""}
            onChange={(e) => onDefaultPersonaChange(e.target.value || null)}
            className="rounded-lg border border-lab-border bg-lab-bg px-3 py-1.5 text-sm text-slate-200"
          >
            <option value="">None (choose each time)</option>
            {personas.data?.map((p: Persona) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
      </section>

      <section className="space-y-3 rounded-xl border border-lab-border bg-lab-panel p-4">
        <h2 className="text-sm font-medium text-slate-200">Monitoring</h2>
        <label className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Drift monitoring enabled</span>
          <input
            type="checkbox"
            checked={monitoringEnabled}
            onChange={(e) => onMonitoringChange(e.target.checked)}
            className="h-4 w-4"
          />
        </label>
        <p className="text-xs text-slate-600">
          When off, responses generate faster but the persona monitor panel won't detect or repair drift.
        </p>
      </section>

      <section className="space-y-2 rounded-xl border border-lab-border bg-lab-panel p-4">
        <h2 className="mb-1 text-sm font-medium text-slate-200">System</h2>
        <div className="mono space-y-1 text-xs text-slate-400">
          <div>Backend: {health.isError ? "unreachable" : health.data?.status ?? "…"}</div>
          <div>Groq: {providerHealth.data?.groq.status ?? "…"}</div>
        </div>
        <p className="text-xs text-slate-600">Full detail on the System Status page.</p>
      </section>

      <section className="space-y-3 rounded-xl border border-lab-border bg-lab-panel p-4">
        <h2 className="text-sm font-medium text-slate-200">About</h2>
        <FullLockupImage maxWidth={420} />
        <p className="text-xs text-slate-500">
          A research framework for detecting, preventing, analyzing, and correcting real-world AI persona drift:
          keeping an assigned persona's identity, scope, and behavior authoritative against both accidental
          generation-time drift and deliberate user attempts to switch personas through conversation.
        </p>
        <p className="text-[10px] text-slate-600">
          Formerly released as {PROJECT_FORMER_NAMES.map((n) => <span key={n} className="mono">{n}</span>).reduce((prev, curr) => <>{prev}, {curr}</>)}.
        </p>
      </section>
    </div>
  );
}
