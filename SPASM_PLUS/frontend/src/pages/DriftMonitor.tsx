import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { api } from "../services/api";

export function DriftMonitor() {
  const [conversationId, setConversationId] = useState<string>("");

  const conversations = useQuery({ queryKey: ["conversations"], queryFn: api.listConversations });
  const driftEvents = useQuery({
    queryKey: ["drift-events", conversationId],
    queryFn: () => api.listDriftEvents(conversationId),
    enabled: !!conversationId,
  });

  const chartData = (driftEvents.data ?? []).map((e, i) => ({
    turn: i + 1,
    stability: Math.round(e.overall_stability * 100),
    severity: e.severity,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Drift Monitor</h1>
        <p className="text-sm text-slate-500">
          Real drift events recorded during a conversation. Empty until you've chatted with an active persona.
        </p>
      </div>

      <select
        value={conversationId}
        onChange={(e) => setConversationId(e.target.value)}
        className="w-full max-w-sm rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200"
      >
        <option value="">Select a conversation…</option>
        {conversations.data?.map((c) => (
          <option key={c.id} value={c.id}>{c.title} · {c.model}</option>
        ))}
      </select>

      {conversationId && chartData.length === 0 && (
        <div className="rounded-xl border border-lab-border bg-lab-panel p-4 text-sm text-slate-500">
          No drift events recorded for this conversation yet — either no messages have been sent, or none have
          triggered drift.
        </div>
      )}

      {chartData.length > 0 && (
        <div className="rounded-xl border border-lab-border bg-lab-panel p-4">
          <h2 className="mb-3 text-sm font-medium text-slate-300">Stability over drift events</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="turn" stroke="#64748b" fontSize={12} />
              <YAxis domain={[0, 100]} stroke="#64748b" fontSize={12} />
              <Tooltip contentStyle={{ background: "#111721", border: "1px solid #1f2937" }} />
              <Line type="monotone" dataKey="stability" stroke="#22d3ee" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {driftEvents.data && driftEvents.data.length > 0 && (
        <div className="rounded-xl border border-lab-border bg-lab-panel">
          <h2 className="border-b border-lab-border px-4 py-3 text-sm font-medium text-slate-300">Timeline</h2>
          {driftEvents.data.map((e) => (
            <div key={e.id} className="flex items-center justify-between border-b border-lab-border px-4 py-2 text-xs last:border-0">
              <span className="text-slate-400">{new Date(e.created_at).toLocaleTimeString()}</span>
              <span className="text-slate-300">{e.drift_type.replace(/_/g, " ")}</span>
              <span className="mono uppercase text-slate-500">{e.severity}</span>
              <span className="mono text-slate-500">{Math.round(e.overall_stability * 100)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
