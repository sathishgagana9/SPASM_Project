import { useQuery } from "@tanstack/react-query";
import { Users, Plug, Play, AlertTriangle, Server, Plus } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { PersonaCard } from "../components/PersonaCard";
import type { Persona } from "../types";

function SummaryStat({ icon: Icon, label, value }: { icon: React.ComponentType<{ size?: number }>; label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-lab-border bg-lab-panel p-4">
      <div className="mb-2 flex items-center gap-2 text-slate-500">
        <Icon size={14} />
        <span className="text-xs uppercase tracking-wide">{label}</span>
      </div>
      <div className="mono text-2xl text-slate-100">{value}</div>
    </div>
  );
}

export function Dashboard({ onOpenSettings }: { onOpenSettings: (p: Persona) => void }) {
  const queryClient = useQueryClient();
  const summary = useQuery({ queryKey: ["dashboard-summary"], queryFn: api.dashboardSummary });
  const personas = useQuery({ queryKey: ["personas"], queryFn: api.listPersonas });

  const createBlank = useMutation({
    mutationFn: () =>
      api.createPersona({
        name: `persona-${Math.random().toString(36).slice(2, 8)}`,
        description: "",
        identity: "",
        tone: "",
        scope: "",
        personality_traits: [],
        goals: [],
        values: [],
        behavior_rules: [],
        knowledge_boundaries: [],
        response_constraints: [],
        forbidden_behaviors: [],
        example_responses: [],
      }),
    onSuccess: (p) => {
      queryClient.invalidateQueries({ queryKey: ["personas"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      onOpenSettings(p);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Persona Dashboard</h1>
          <p className="text-sm text-slate-500">What personas exist, what they're connected to, and whether they're running.</p>
        </div>
        <button
          onClick={() => createBlank.mutate()}
          disabled={createBlank.isPending}
          className="flex items-center gap-1 rounded-lg bg-lab-accent/90 px-3 py-2 text-sm font-medium text-lab-bg hover:bg-lab-accent disabled:opacity-50"
        >
          <Plus size={14} /> New Persona
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        <SummaryStat icon={Users} label="Total Personas" value={summary.data?.total_personas ?? "…"} />
        <SummaryStat icon={Plug} label="Connected" value={summary.data?.connected ?? "…"} />
        <SummaryStat icon={Play} label="Running" value={summary.data?.running ?? "…"} />
        <SummaryStat icon={AlertTriangle} label="Errors" value={summary.data?.errors ?? "…"} />
        <SummaryStat icon={Server} label="Providers" value={summary.data?.available_providers.length ?? "…"} />
      </div>

      {personas.isLoading && <div className="text-sm text-slate-500">Loading…</div>}
      {personas.isError && <div className="text-sm text-lab-danger">Could not reach the backend.</div>}
      {personas.data?.length === 0 && (
        <div className="rounded-xl border border-lab-border bg-lab-panel p-6 text-center text-sm text-slate-500">
          No personas yet. Click "New Persona" to create one, or run the seed script for 5 ready-made examples.
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {personas.data?.map((p) => (
          <PersonaCard key={p.id} persona={p} onOpenSettings={onOpenSettings} />
        ))}
      </div>
    </div>
  );
}
