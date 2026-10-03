import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plug, PlugZap, Play, Square, Settings, Loader2, AlertTriangle } from "lucide-react";
import { api } from "../services/api";
import type { Persona } from "../types";

function StatusBadge({ persona }: { persona: Persona }) {
  if (persona.running) return <span className="rounded-full bg-lab-ok/10 px-2 py-0.5 text-[10px] uppercase text-lab-ok">Running</span>;
  if (persona.connected) return <span className="rounded-full bg-lab-accent/10 px-2 py-0.5 text-[10px] uppercase text-lab-accent">Connected</span>;
  if (persona.last_connection_error) return <span className="rounded-full bg-lab-danger/10 px-2 py-0.5 text-[10px] uppercase text-lab-danger">Error</span>;
  return <span className="rounded-full bg-slate-700/30 px-2 py-0.5 text-[10px] uppercase text-slate-400">Disconnected</span>;
}

export function PersonaCard({ persona, onOpenSettings }: { persona: Persona; onOpenSettings: (p: Persona) => void }) {
  const queryClient = useQueryClient();
  const [model, setModel] = useState(persona.default_model || "");
  const [showConnectForm, setShowConnectForm] = useState(false);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["personas"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
  };

  const connect = useMutation({
    mutationFn: () => api.connectPersona(persona.id, "groq", model),
    onSuccess: () => {
      invalidate();
      setShowConnectForm(false);
    },
  });
  const disconnect = useMutation({ mutationFn: () => api.disconnectPersona(persona.id), onSuccess: invalidate });
  const testConn = useMutation({ mutationFn: () => api.testConnection(persona.id) });
  const run = useMutation({ mutationFn: () => api.runPersona(persona.id), onSuccess: invalidate });
  const stop = useMutation({ mutationFn: () => api.stopPersona(persona.id), onSuccess: invalidate });

  return (
    <div className="rounded-xl border border-lab-border bg-lab-panel p-4">
      <div className="mb-3 flex items-start justify-between">
        <div>
          <div className="text-sm font-medium text-slate-100">{persona.display_label}</div>
          <div className="text-xs text-slate-500">{persona.description || "No description"}</div>
        </div>
        <StatusBadge persona={persona} />
      </div>

      <div className="mono mb-3 space-y-1 text-xs text-slate-500">
        <div>Provider: Groq</div>
        <div>Model: {persona.default_model || "—"}</div>
        {persona.active_conversation_id && <div>Session: {persona.active_conversation_id.slice(0, 8)}…</div>}
      </div>

      {persona.last_connection_error && !persona.connected && (
        <div className="mb-3 flex items-start gap-1.5 rounded-lg border border-lab-danger/30 bg-lab-danger/5 p-2 text-xs text-lab-danger">
          <AlertTriangle size={12} className="mt-0.5 shrink-0" />
          <span>{persona.last_connection_error}</span>
        </div>
      )}

      {testConn.data && (
        <div className={`mb-3 text-xs ${testConn.data.connected ? "text-lab-ok" : "text-lab-danger"}`}>
          Test result: {testConn.data.status} {testConn.data.error && `— ${testConn.data.error}`}
        </div>
      )}

      {showConnectForm && (
        <div className="mb-3 space-y-2 rounded-lg border border-lab-border bg-lab-bg p-2">
          <input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="openai/gpt-oss-20b"
            className="w-full rounded border border-lab-border bg-lab-panel px-2 py-1 text-xs text-slate-200"
          />
          <button
            onClick={() => connect.mutate()}
            disabled={!model.trim() || connect.isPending}
            className="w-full rounded bg-lab-accent/90 py-1 text-xs font-medium text-lab-bg hover:bg-lab-accent disabled:opacity-50"
          >
            {connect.isPending ? "Connecting…" : "Confirm Connect"}
          </button>
        </div>
      )}

      <div className="flex flex-wrap gap-1.5">
        {!persona.connected ? (
          <button
            onClick={() => setShowConnectForm((s) => !s)}
            className="flex items-center gap-1 rounded-lg border border-lab-border px-2.5 py-1.5 text-xs text-slate-300 hover:border-lab-accent hover:text-lab-accent"
          >
            <Plug size={12} /> Connect
          </button>
        ) : (
          <button
            onClick={() => disconnect.mutate()}
            className="flex items-center gap-1 rounded-lg border border-lab-border px-2.5 py-1.5 text-xs text-slate-300 hover:border-lab-danger hover:text-lab-danger"
          >
            <PlugZap size={12} /> Disconnect
          </button>
        )}

        <button
          onClick={() => testConn.mutate()}
          disabled={testConn.isPending}
          className="flex items-center gap-1 rounded-lg border border-lab-border px-2.5 py-1.5 text-xs text-slate-300 hover:border-lab-accent hover:text-lab-accent disabled:opacity-50"
        >
          {testConn.isPending ? <Loader2 size={12} className="animate-spin" /> : null} Test
        </button>

        {!persona.running ? (
          <button
            onClick={() => run.mutate()}
            disabled={!persona.connected || run.isPending}
            className="flex items-center gap-1 rounded-lg border border-lab-ok/40 px-2.5 py-1.5 text-xs text-lab-ok hover:bg-lab-ok/10 disabled:opacity-40"
          >
            <Play size={12} /> Run
          </button>
        ) : (
          <button
            onClick={() => stop.mutate()}
            className="flex items-center gap-1 rounded-lg border border-lab-warn/40 px-2.5 py-1.5 text-xs text-lab-warn hover:bg-lab-warn/10"
          >
            <Square size={12} /> Stop
          </button>
        )}

        <button
          onClick={() => onOpenSettings(persona)}
          className="ml-auto flex items-center gap-1 rounded-lg border border-lab-border px-2.5 py-1.5 text-xs text-slate-400 hover:border-lab-accent hover:text-lab-accent"
        >
          <Settings size={12} /> Settings
        </button>
      </div>
    </div>
  );
}
