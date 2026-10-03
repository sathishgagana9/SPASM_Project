interface StatusPillProps {
  label: string;
  status: "connected" | "unreachable" | "error" | "not configured" | "NOT IMPLEMENTED" | "loading";
}

const STYLES: Record<string, string> = {
  connected: "bg-lab-ok/10 text-lab-ok border-lab-ok/30",
  unreachable: "bg-lab-danger/10 text-lab-danger border-lab-danger/30",
  error: "bg-lab-danger/10 text-lab-danger border-lab-danger/30",
  "not configured": "bg-slate-700/30 text-slate-400 border-slate-600/40",
  "NOT IMPLEMENTED": "bg-slate-700/30 text-slate-400 border-slate-600/40",
  loading: "bg-slate-700/30 text-slate-400 border-slate-600/40 animate-pulse",
};

export function StatusPill({ label, status }: StatusPillProps) {
  return (
    <div className={`flex items-center justify-between rounded-lg border px-3 py-2 text-sm ${STYLES[status] ?? STYLES.error}`}>
      <span className="mono text-xs uppercase tracking-wide text-slate-400">{label}</span>
      <span className="mono text-xs uppercase">{status}</span>
    </div>
  );
}
