import { useQuery } from "@tanstack/react-query";
import { Server, Database, ShieldCheck, Cloud } from "lucide-react";
import { api } from "../services/api";
import { StatusPill } from "../components/StatusPill";

export function Overview() {
  const health = useQuery({ queryKey: ["health"], queryFn: api.health });
  const providers = useQuery({ queryKey: ["provider-health"], queryFn: api.providerHealth });
  const personas = useQuery({ queryKey: ["personas"], queryFn: api.listPersonas });
  // Real DB check: if this query succeeds, SQLite is reachable and queryable — no separate fake "DB: connected" flag.
  const dbCheck = useQuery({ queryKey: ["db-check"], queryFn: api.listPersonas });

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">System Status</h1>
        <p className="text-sm text-slate-500">Real backend connectivity — nothing on this page is mock data.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-lab-border bg-lab-panel p-4">
          <div className="mb-3 flex items-center gap-2 text-slate-400">
            <Server size={16} />
            <span className="text-sm">Backend API</span>
          </div>
          {health.isLoading && <StatusPill label="api" status="loading" />}
          {health.isError && <StatusPill label="api" status="unreachable" />}
          {health.data && <StatusPill label={health.data.environment} status="connected" />}
        </div>

        <div className="rounded-xl border border-lab-border bg-lab-panel p-4">
          <div className="mb-3 flex items-center gap-2 text-slate-400">
            <Cloud size={16} />
            <span className="text-sm">Groq Provider</span>
          </div>
          {providers.isLoading && <StatusPill label="groq" status="loading" />}
          {providers.data && <StatusPill label="groq" status={providers.data.groq.status as any} />}
        </div>

        <div className="rounded-xl border border-lab-border bg-lab-panel p-4">
          <div className="mb-3 flex items-center gap-2 text-slate-400">
            <Database size={16} />
            <span className="text-sm">Database</span>
          </div>
          {dbCheck.isLoading && <StatusPill label="sqlite" status="loading" />}
          {dbCheck.isError && <StatusPill label="sqlite" status="unreachable" />}
          {dbCheck.data && <StatusPill label={`${personas.data?.length ?? 0} personas`} status="connected" />}
        </div>

        <div className="rounded-xl border border-lab-border bg-lab-panel p-4">
          <div className="mb-3 flex items-center gap-2 text-slate-400">
            <ShieldCheck size={16} />
            <span className="text-sm">Drift Monitor</span>
          </div>
          <StatusPill label="rule-based" status="connected" />
          <p className="mt-2 text-[11px] text-slate-600">Always available — no external dependency (see docs/drift-detection.md).</p>
        </div>
      </div>
    </div>
  );
}
