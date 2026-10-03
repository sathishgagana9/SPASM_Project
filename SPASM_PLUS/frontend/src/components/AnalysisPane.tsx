import { useEffect, useState, type ReactNode } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Cell,
} from "recharts";
import { ShieldCheck, ShieldAlert, ShieldQuestion, ShieldX, ChevronDown, ChevronRight, type LucideIcon } from "lucide-react";
import type { Message, Persona, DriftEvent, RepairEvent } from "../types";
import { BoundaryStatusBadge } from "./BoundaryStatusBadge";
import {
  buildTurnAnalyses, type TurnAnalysis, type DriftAttribution,
  confidenceLevel, assistantBehavior, personaAdherence, scopeAdherence, driftSeverity,
  responseQuality, domainTopic, importancePriority, riskSensitivity, reasoningEvidence, driftAttribution,
  boundaryStatusesForTurn,
} from "../lib/turnAnalysis";

type StabilityState = "stable" | "watch" | "drifting" | "critical";

function classify(overallStability: number | null): StabilityState {
  if (overallStability === null) return "stable";
  if (overallStability >= 0.85) return "stable";
  if (overallStability >= 0.7) return "watch";
  if (overallStability >= 0.5) return "drifting";
  return "critical";
}

const STATE_META: Record<StabilityState, { label: string; color: string; icon: LucideIcon }> = {
  stable: { label: "Persona Stable", color: "text-lab-ok", icon: ShieldCheck },
  watch: { label: "Minor Drift", color: "text-lab-warn", icon: ShieldQuestion },
  drifting: { label: "Persona Drifting", color: "text-lab-warn", icon: ShieldAlert },
  critical: { label: "Severe Drift", color: "text-lab-danger", icon: ShieldX },
};

const SEVERITY_COLOR: Record<string, string> = {
  none: "#334155", low: "#34d399", medium: "#f59e0b", high: "#f43f5e", critical: "#f43f5e",
};

function severityDotColor(turn: TurnAnalysis): string {
  if (!turn.driftEvent) return SEVERITY_COLOR.none;
  if (turn.driftEvent.drift_type === "persona_boundary_enforced") {
    // Distinct from a real violation — this is the SUCCESS case (spec Part 26:
    // "DRIFT PREVENTED" needs its own visual identity, separate from "DRIFT
    // DETECTED"). Switch attempts get purple, plain out-of-scope gets blue —
    // both are "prevented", neither is "detected" (i.e. an actual failure).
    return turn.driftEvent.persona_switch_attempt ? "#a855f7" : "#22d3ee";
  }
  if (!turn.driftEvent.detected) return SEVERITY_COLOR.none;
  return SEVERITY_COLOR[turn.driftEvent.severity] ?? SEVERITY_COLOR.none;
}

function MetricCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mono text-sm text-slate-100">{value}</div>
      {sub && <div className="text-[10px] text-slate-500">{sub}</div>}
    </div>
  );
}

function DimensionBarChart({ driftEvent }: { driftEvent: DriftEvent | null }) {
  if (!driftEvent || Object.keys(driftEvent.dimensions).length === 0) {
    return <div className="text-xs text-slate-600">No dimension data for this turn.</div>;
  }
  const data = Object.entries(driftEvent.dimensions).map(([dim, value]) => ({
    dim: dim.slice(0, 4), fullDim: dim, value: Math.round(value * 100),
  }));
  return (
    <ResponsiveContainer width="100%" height={110}>
      <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
        <XAxis dataKey="dim" tick={{ fontSize: 9, fill: "#64748b" }} axisLine={{ stroke: "#1f2937" }} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: "#64748b" }} axisLine={false} tickLine={false} width={28} />
        <Tooltip
          contentStyle={{ background: "#111721", border: "1px solid #1f2937", fontSize: 11 }}
          labelFormatter={(_, payload) => payload?.[0]?.payload?.fullDim ?? ""}
          formatter={(value: number) => [`${value}%`, "score"]}
        />
        <Bar dataKey="value" radius={[2, 2, 0, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.value >= 85 ? "#34d399" : d.value >= 60 ? "#f59e0b" : "#f43f5e"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function TurnSeverityGrid({ turns, selectedIndex, onSelect }: { turns: TurnAnalysis[]; selectedIndex: number | null; onSelect: (i: number) => void }) {
  if (turns.length === 0) return <div className="text-xs text-slate-600">No turns yet.</div>;
  return (
    <div className="grid grid-cols-10 gap-1">
      {turns.map((turn) => (
        <button
          key={turn.turnIndex}
          onClick={() => onSelect(turn.turnIndex)}
          title={`Turn ${turn.turnIndex + 1}: ${turn.driftEvent ? turn.driftEvent.severity : "not monitored"}`}
          className={`aspect-square rounded-sm transition-transform hover:scale-110 ${
            selectedIndex === turn.turnIndex ? "ring-2 ring-lab-accent" : ""
          }`}
          style={{ backgroundColor: severityDotColor(turn) }}
        />
      ))}
    </div>
  );
}

function PipelineRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between border-l-2 border-lab-border py-1 pl-2 text-xs">
      <span className="text-slate-500">{label}</span>
      {children}
    </div>
  );
}

/** Spec Part 25: "the right panel should become one of the strongest parts
 * of the UI because it demonstrates the research contribution" — a
 * step-by-step readout of the actual pipeline decision for this turn:
 * persona -> user intent -> scope status -> switch attempt -> assistant
 * behavior -> correction status. Uses the SAME boundaryStatusesForTurn()
 * derivation (and the same BoundaryStatusBadge component) as the chat
 * bubbles, so a turn is described identically wherever it shows up. */
function BoundaryPipeline({ persona, turn, attribution }: { persona: Persona; turn: TurnAnalysis | null; attribution: DriftAttribution }) {
  if (!turn?.driftEvent) return null;
  const statuses = boundaryStatusesForTurn(turn.driftEvent, turn.repairEvent);
  return (
    <div className="space-y-0.5 rounded-lg border border-lab-border bg-lab-bg p-3">
      <div className="mb-1 text-[10px] uppercase tracking-wide text-slate-500">Boundary enforcement pipeline</div>
      <PipelineRow label="Selected persona"><span className="mono text-xs text-slate-300">{persona.name}</span></PipelineRow>
      <PipelineRow label="Persona switch attempt">
        <span className={`mono text-xs ${attribution.userAttemptedSwitch ? "text-lab-warn" : "text-lab-ok"}`}>
          {attribution.userAttemptedSwitch ? `Detected${attribution.requestedRole ? ` (${attribution.requestedRole})` : ""}` : "Not detected"}
        </span>
      </PipelineRow>
      <PipelineRow label="Outcome">
        <div className="flex flex-wrap justify-end gap-1">
          {statuses.length > 0
            ? statuses.map((s) => <BoundaryStatusBadge key={s} status={s} size="xs" />)
            : <BoundaryStatusBadge status="in_scope" size="xs" />}
        </div>
      </PipelineRow>
    </div>
  );
}

export function AnalysisPane({
  persona,
  messages,
  driftEvents,
  repairEvents,
  monitoringEnabled,
  liveDrift,
}: {
  persona: Persona | null;
  messages: Message[];
  driftEvents: DriftEvent[];
  repairEvents: RepairEvent[];
  monitoringEnabled: boolean;
  liveDrift: DriftEvent | null;
}) {
  const turns = buildTurnAnalyses(messages, driftEvents, repairEvents);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  // Default to (and follow) the latest turn unless the user has explicitly
  // picked an earlier one to inspect.
  useEffect(() => {
    setSelectedIndex(null);
  }, [messages.length === 0]);

  const effectiveIndex = selectedIndex ?? turns.length - 1;
  const selectedTurn = turns[effectiveIndex] ?? null;
  const effectiveDrift = selectedTurn?.driftEvent ?? liveDrift;

  if (!persona) {
    return (
      <div className="w-96 shrink-0 border-l border-lab-border bg-lab-panel/40 p-4">
        <div className="text-xs uppercase tracking-wide text-slate-500">Chat Analysis</div>
        <p className="mt-2 text-sm text-slate-600">Start a conversation to see live monitoring.</p>
      </div>
    );
  }

  const stabilityHistory = turns.map((t) => t.driftEvent?.overall_stability ?? 1);
  const chartData = stabilityHistory.map((v, i) => ({ turn: i + 1, value: Math.round(v * 100) }));
  const latestStability = effectiveDrift ? effectiveDrift.overall_stability : stabilityHistory.at(-1) ?? 1;
  const state = monitoringEnabled ? classify(latestStability) : "stable";
  const meta = STATE_META[state];
  const Icon = meta.icon;

  const conf = confidenceLevel(effectiveDrift);
  const behavior = assistantBehavior(effectiveDrift, selectedTurn?.repairEvent ?? null);
  const adherence = personaAdherence(effectiveDrift);
  const scope = scopeAdherence(effectiveDrift);
  const severity = driftSeverity(effectiveDrift);
  const quality = responseQuality(effectiveDrift, selectedTurn?.repairEvent ?? null);
  const userText = selectedTurn?.userMessage.content ?? "";
  const domain = domainTopic(userText, effectiveDrift);
  const importance = importancePriority(userText, effectiveDrift);
  const risk = riskSensitivity(userText, effectiveDrift);
  const reasoning = reasoningEvidence(effectiveDrift);
  const attribution = driftAttribution(effectiveDrift, selectedTurn?.repairEvent ?? null);

  return (
    <div className="w-96 shrink-0 space-y-4 overflow-y-auto border-l border-lab-border bg-lab-panel/40 p-4">
      <div>
        <div className="text-xs uppercase tracking-wide text-slate-500">Chat Analysis</div>
        <div className="mt-1 text-sm font-medium text-slate-100">{persona.name}</div>
      </div>

      {!monitoringEnabled ? (
        <div className="rounded-lg border border-lab-border bg-lab-bg p-3 text-xs text-slate-500">
          Monitoring temporarily unavailable — disabled in Settings.
        </div>
      ) : (
        <>
          <div className={`flex items-center gap-2 text-sm font-medium ${meta.color}`}>
            <Icon size={16} />
            {meta.label}
            {selectedIndex !== null && selectedIndex !== turns.length - 1 && (
              <span className="ml-auto rounded bg-lab-bg px-1.5 py-0.5 text-[10px] font-normal text-slate-500">
                viewing turn {selectedIndex + 1}
              </span>
            )}
          </div>

          {/* --- Visualization 1: stability line chart across all turns --- */}
          {chartData.length > 1 && (
            <div>
              <div className="mb-1 text-xs text-slate-500">Stability over turns</div>
              <ResponsiveContainer width="100%" height={60}>
                <LineChart data={chartData}>
                  <YAxis domain={[0, 100]} hide />
                  <Line type="monotone" dataKey="value" stroke="#22d3ee" strokeWidth={2} dot={{ r: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* --- Visualization 2: per-turn severity grid (also a turn navigator) --- */}
          <div>
            <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
              <span>Turn-by-turn severity</span>
              <span className="text-[10px] text-slate-600">{turns.length} turn{turns.length === 1 ? "" : "s"}</span>
            </div>
            <TurnSeverityGrid turns={turns} selectedIndex={effectiveIndex} onSelect={setSelectedIndex} />
          </div>

          {/* --- Detailed metrics grid for the selected turn --- */}
          <div className="grid grid-cols-2 gap-x-3 gap-y-2 rounded-lg border border-lab-border bg-lab-bg p-3">
            <MetricCard label="Confidence" value={conf.label} sub={conf.value !== null ? conf.value.toFixed(2) : undefined} />
            <MetricCard label="Assistant behavior" value={behavior} />
            <MetricCard label="Question domain" value={domain.topic} sub={domain.method} />
            <MetricCard label="Question priority" value={importance.label} sub="heuristic" />
            <MetricCard label="Persona adherence" value={adherence.label} sub={adherence.value !== null ? `${Math.round(adherence.value * 100)}%` : undefined} />
            <MetricCard label="Scope adherence" value={scope.label} sub={scope.similarity !== null ? `sim ${(scope.similarity * 100).toFixed(0)}%` : undefined} />
            <MetricCard label="Drift severity" value={severity.label} />
            <MetricCard label="Response quality" value={quality} />
            <MetricCard label="Risk / sensitivity" value={risk.label} sub="heuristic" />
          </div>

          {/* --- Boundary enforcement pipeline (spec Part 25) --- */}
          <BoundaryPipeline persona={persona} turn={selectedTurn} attribution={attribution} />

          {/* --- Visualization 3: dimension score bar chart for the selected turn --- */}
          <div>
            <div className="mb-1 text-xs text-slate-500">Dimension breakdown (selected turn)</div>
            <DimensionBarChart driftEvent={effectiveDrift} />
          </div>

          {/* --- Reasoning / evidence --- */}
          <div>
            <div className="mb-1 text-xs text-slate-500">Reasoning / evidence</div>
            <ul className="space-y-1 text-xs text-slate-400">
              {reasoning.map((line, i) => (
                <li key={i} className="border-l-2 border-lab-border pl-2">{line}</li>
              ))}
            </ul>
          </div>

          {attribution.assistantActuallyDrifted && (
            <div className="rounded-lg border border-lab-warn/30 bg-lab-warn/5 p-2 text-xs text-slate-300">
              <div className="mb-1 font-medium text-lab-warn">⚠ Persona Drift Detected</div>
              {effectiveDrift?.reason}
            </div>
          )}
          {attribution.correctionStatus === "prevented" && (
            <div className="rounded-lg border border-lab-ok/30 bg-lab-ok/5 p-2 text-xs text-slate-300">
              <div className="mb-1 font-medium text-lab-ok">✓ Drift Prevented</div>
              {effectiveDrift?.reason}
            </div>
          )}

          {/* --- Turn-by-turn list (expandable) --- */}
          <div>
            <button
              onClick={() => setHistoryOpen((o) => !o)}
              className="flex w-full items-center gap-1 text-xs text-slate-500 hover:text-slate-300"
            >
              {historyOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              Turn-by-turn history ({turns.length})
            </button>
            {historyOpen && (
              <div className="mt-2 max-h-64 space-y-1 overflow-y-auto">
                {turns.map((turn) => {
                  const isSelected = turn.turnIndex === effectiveIndex;
                  const s = driftSeverity(turn.driftEvent);
                  const b = assistantBehavior(turn.driftEvent, turn.repairEvent);
                  return (
                    <button
                      key={turn.turnIndex}
                      onClick={() => setSelectedIndex(turn.turnIndex)}
                      className={`block w-full rounded-md border px-2 py-1.5 text-left text-xs transition-colors ${
                        isSelected ? "border-lab-accent bg-lab-accent/10" : "border-lab-border bg-lab-bg hover:border-slate-600"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="mono text-slate-400">Turn {turn.turnIndex + 1}</span>
                        <span className="mono" style={{ color: severityDotColor(turn) }}>{s.label}</span>
                      </div>
                      <div className="mt-0.5 truncate text-slate-500">{turn.userMessage.content}</div>
                      <div className="mt-0.5 text-[10px] text-slate-600">{b}</div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="space-y-1 text-xs text-slate-500">
            <div>Messages analyzed: {turns.length}</div>
          </div>
        </>
      )}
    </div>
  );
}
