import { useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react";
import type { DriftEvent, RepairEvent } from "../types";

const SEVERITY_COLOR: Record<string, string> = {
  low: "text-lab-ok border-lab-ok/30 bg-lab-ok/5",
  medium: "text-lab-warn border-lab-warn/30 bg-lab-warn/5",
  high: "text-lab-danger border-lab-danger/30 bg-lab-danger/5",
  critical: "text-lab-danger border-lab-danger/30 bg-lab-danger/10",
};

export function DriftAlert({ drift, repair }: { drift: DriftEvent; repair: RepairEvent | null }) {
  const [showTechnical, setShowTechnical] = useState(false);
  const readableType = drift.drift_type.replace(/_/g, " ").replace("drift", "Drift").trim();

  return (
    <div className={`rounded-xl border p-4 ${SEVERITY_COLOR[drift.severity] ?? SEVERITY_COLOR.medium}`}>
      <div className="mb-2 flex items-center gap-2 text-sm font-medium">
        <AlertTriangle size={16} />
        {readableType} Detected
        <span className="mono ml-auto text-xs uppercase opacity-70">{drift.severity} · {Math.round(drift.confidence * 100)}% confidence</span>
      </div>
      <p className="mb-3 text-sm text-slate-300">{drift.reason}</p>

      {repair && (
        <div className="mb-2 flex items-center gap-2 text-sm">
          {repair.success ? <CheckCircle2 size={16} className="text-lab-ok" /> : <AlertTriangle size={16} className="text-lab-danger" />}
          <span>
            RAISE applied <span className="mono">{repair.operator.replace(/_/g, " ")}</span> —{" "}
            {repair.success ? "repair succeeded" : "REPAIR FAILED (drift persisted)"}
          </span>
          <span className="mono ml-auto text-xs opacity-70">
            {Math.round(repair.stability_before * 100)}% → {Math.round(repair.stability_after * 100)}%
          </span>
        </div>
      )}

      <button
        onClick={() => setShowTechnical((s) => !s)}
        className="mt-2 flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300"
      >
        {showTechnical ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        Technical details
      </button>
      {showTechnical && (
        <div className="mono mt-2 grid grid-cols-2 gap-1 text-xs text-slate-500 sm:grid-cols-4">
          {Object.entries(drift.dimensions).map(([dim, score]) => (
            <div key={dim}>
              {dim}: {Math.round(score * 100)}%
            </div>
          ))}
          <div className="col-span-2 sm:col-span-4">method: {drift.method} (rule-based, provisional — see docs/drift-detection.md)</div>
          {drift.scope_classification && (
            <div className="col-span-2 sm:col-span-4">
              scope: {drift.scope_classification}
              {drift.scope_similarity !== null && ` (similarity: ${drift.scope_similarity})`}
            </div>
          )}
          {drift.context_contradictions?.length > 0 && (
            <div className="col-span-2 sm:col-span-4 text-lab-warn">
              {drift.context_contradictions.length} contradiction(s) with earlier commitments
            </div>
          )}
        </div>
      )}
    </div>
  );
}
