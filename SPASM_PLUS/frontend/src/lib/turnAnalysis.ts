/**
 * Turn-analysis derivation for the chat analysis pane.
 *
 * Everything here is a PURE function over data the backend already
 * returns (DriftEvent, RepairEvent, Message) — no new backend fields
 * were invented. Three fields the backend doesn't compute at all
 * (domain/topic, importance/priority, risk/sensitivity) are derived
 * here with small, explicit, keyword-based heuristics — each function
 * says so in its return value (`method: "heuristic"`) so the UI can
 * label them honestly rather than presenting a guess as a measurement,
 * consistent with how the rest of this project treats its own
 * detector output (see backend/docs/drift-detection.md).
 */
import type { DriftEvent, Message, RepairEvent } from "../types";
import type { BoundaryStatus } from "../components/BoundaryStatusBadge";

export interface TurnAnalysis {
  turnIndex: number;
  userMessage: Message;
  assistantMessage: Message;
  driftEvent: DriftEvent | null;
  repairEvent: RepairEvent | null;
}

/** Pairs each assistant message with the drift/repair events for that turn.
 * Matches by DriftEvent.message_id === the USER message's id (set in
 * conversations.py) rather than positionally — positional alignment would
 * break if monitoring was ever toggled off for just one turn mid-conversation,
 * since that turn would have no DriftEvent row at all. */
export function buildTurnAnalyses(
  messages: Message[],
  driftEvents: DriftEvent[],
  repairEvents: RepairEvent[]
): TurnAnalysis[] {
  const driftByUserMessageId = new Map(driftEvents.map((d) => [d.message_id, d] as const));
  const turns: TurnAnalysis[] = [];
  let turnIndex = 0;

  for (let i = 0; i < messages.length - 1; i++) {
    if (messages[i].role !== "user" || messages[i + 1].role !== "assistant") continue;
    const userMessage = messages[i];
    const assistantMessage = messages[i + 1];
    const driftEvent = driftByUserMessageId.get(userMessage.id) ?? null;
    const repairEvent = driftEvent ? repairEvents.find((r) => r.drift_event_id === driftEvent.id) ?? null : null;

    turns.push({ turnIndex, userMessage, assistantMessage, driftEvent, repairEvent });
    turnIndex++;
    i++; // skip the assistant message we just consumed
  }
  return turns;
}

export function confidenceLevel(driftEvent: DriftEvent | null): { label: string; value: number | null } {
  if (!driftEvent) return { label: "—", value: null };
  const v = driftEvent.confidence;
  const label = v >= 0.8 ? "High" : v >= 0.5 ? "Medium" : "Low";
  return { label, value: v };
}

export function assistantBehavior(driftEvent: DriftEvent | null, repairEvent: RepairEvent | null): string {
  if (!driftEvent) return "—";
  if (driftEvent.drift_type === "persona_boundary_enforced") {
    return driftEvent.persona_switch_attempt ? "Persona boundary enforced — switch attempt refused" : "Persona boundary enforced — out-of-scope request refused";
  }
  if (!driftEvent.detected) return "Aligned with persona";
  if (repairEvent?.success) return "Off-persona → repaired";
  if (repairEvent && !repairEvent.success) return "Off-persona → repair unresolved";
  return "Off-persona (unrepaired)";
}

/**
 * Spec Part 13's central distinction: a user ATTEMPTING to cause persona
 * drift and the ASSISTANT ACTUALLY drifting are two different events that
 * must never be conflated. This function is the single place that combines
 * both signals — persona_switch_attempt describes the USER's message,
 * detected/severity describe the ASSISTANT's actual behavior — into one
 * attribution label, so the rest of the UI never has to re-derive this
 * distinction ad hoc.
 */
export interface DriftAttribution {
  userAttemptedSwitch: boolean;
  requestedRole: string | null;
  assistantActuallyDrifted: boolean;
  correctionStatus: "not_applicable" | "prevented" | "repaired" | "failed";
  label: string;
}

export function driftAttribution(driftEvent: DriftEvent | null, repairEvent: RepairEvent | null): DriftAttribution {
  if (!driftEvent) {
    return { userAttemptedSwitch: false, requestedRole: null, assistantActuallyDrifted: false, correctionStatus: "not_applicable", label: "—" };
  }
  const userAttemptedSwitch = driftEvent.persona_switch_attempt;
  const wasBlocked = driftEvent.drift_type === "persona_boundary_enforced";

  if (wasBlocked) {
    // Blocked BEFORE generation — by construction, the assistant never
    // actually drifted (there was no unauthorized generation to drift into).
    return {
      userAttemptedSwitch, requestedRole: driftEvent.requested_role,
      assistantActuallyDrifted: false, correctionStatus: "prevented",
      label: userAttemptedSwitch
        ? `User attempted a switch to "${driftEvent.requested_role ?? "another role"}" — prevented before generation`
        : "User's request was out of scope — prevented before generation",
    };
  }

  if (!userAttemptedSwitch && !driftEvent.detected) {
    return { userAttemptedSwitch: false, requestedRole: null, assistantActuallyDrifted: false, correctionStatus: "not_applicable", label: "Normal in-scope turn — no drift attempt or occurrence" };
  }

  // Not blocked pre-generation, but the post-hoc detector still ran — this
  // covers cases the classifier missed (e.g. degraded fallback mode, or a
  // subtler drift the classifier didn't catch) where the ASSISTANT actually
  // did drift post-hoc.
  const assistantActuallyDrifted = driftEvent.detected;
  const correctionStatus: DriftAttribution["correctionStatus"] = !assistantActuallyDrifted
    ? "not_applicable"
    : repairEvent?.success
      ? "repaired"
      : "failed";

  return {
    userAttemptedSwitch, requestedRole: driftEvent.requested_role, assistantActuallyDrifted, correctionStatus,
    label: assistantActuallyDrifted
      ? `Assistant actually drifted (severity: ${driftEvent.severity})${repairEvent?.success ? " — repaired after the fact" : " — uncorrected"}`
      : "Assistant response scored within normal range",
  };
}

export function personaAdherence(driftEvent: DriftEvent | null): { label: string; value: number | null } {
  if (!driftEvent) return { label: "—", value: null };
  const v = driftEvent.dimensions.identity ?? null;
  if (v === null) return { label: "—", value: null };
  const label = v >= 0.85 ? "Strong" : v >= 0.6 ? "Weak" : "Broken";
  return { label, value: v };
}

export function scopeAdherence(driftEvent: DriftEvent | null): { label: string; similarity: number | null } {
  if (!driftEvent) return { label: "—", similarity: null };
  const classification = driftEvent.scope_classification;
  const labels: Record<string, string> = {
    in_scope: "In scope",
    out_of_scope_violation: "Out of scope — violated",
    appropriate_refusal: "Out of scope — correctly declined",
    over_refusal: "In scope — incorrectly declined",
    low_signal_not_flagged: "In scope (low-confidence signal)",
    out_of_scope_blocked: "Out of scope — correctly enforced",
    persona_switch_blocked: "Out of scope — persona switch enforced",
    "n/a": "Not evaluated",
    "": "Not evaluated",
  };
  return { label: labels[classification] ?? classification ?? "—", similarity: driftEvent.scope_similarity };
}

export function driftSeverity(driftEvent: DriftEvent | null): { label: string; severity: string } {
  if (!driftEvent) return { label: "—", severity: "low" };
  return { label: driftEvent.detected ? driftEvent.severity : "none", severity: driftEvent.severity };
}

export function responseQuality(driftEvent: DriftEvent | null, repairEvent: RepairEvent | null): string {
  if (!driftEvent) return "—";
  if (repairEvent) {
    if (repairEvent.success) return `Improved by repair (+${Math.round(repairEvent.stability_improvement * 100)} pts)`;
    return "Repair attempted, unresolved";
  }
  const s = driftEvent.overall_stability;
  if (s >= 0.85) return "Excellent";
  if (s >= 0.7) return "Good";
  if (s >= 0.5) return "Fair";
  return "Poor";
}

// ---- Heuristic-only fields below — clearly labeled, not backend measurements ----

const DOMAIN_KEYWORDS: Record<string, string[]> = {
  "Programming / Software": ["code", "function", "bug", "linked list", "algorithm", "software", "programming", "compile", "variable", "python", "javascript"],
  "Health / Medical": ["symptom", "pain", "doctor", "medicine", "diagnosis", "treatment", "disease", "health", "medical"],
  "Legal": ["law", "legal", "contract", "lawsuit", "court", "statute", "attorney", "lawyer"],
  "Finance": ["budget", "invest", "money", "tax", "loan", "interest rate", "financial", "savings"],
  "Cooking / Food": ["recipe", "cook", "ingredient", "bake", "kitchen", "meal", "food"],
  "Academic / Education": ["explain", "study", "exam", "homework", "learn", "concept", "history", "science", "math"],
  "Creative / Entertainment": ["joke", "story", "poem", "character", "roleplay", "fun", "game"],
};

export function domainTopic(userMessage: string, driftEvent: DriftEvent | null): { topic: string; method: "classifier" | "heuristic" } {
  // Prefer the REAL semantic classification from the backend's intent
  // classifier (app/drift/intent_classifier.py) when available — it reasons
  // about the actual persona scope, not just keyword co-occurrence. The
  // keyword heuristic below only fires as a fallback for turns where no
  // classifier data was recorded (e.g. monitoring was off for that turn).
  if (driftEvent?.requested_domain) {
    return { topic: driftEvent.requested_domain, method: "classifier" };
  }
  const lower = userMessage.toLowerCase();
  let best: string | null = null;
  let bestHits = 0;
  for (const [domain, keywords] of Object.entries(DOMAIN_KEYWORDS)) {
    const hits = keywords.filter((k) => lower.includes(k)).length;
    if (hits > bestHits) {
      bestHits = hits;
      best = domain;
    }
  }
  return { topic: best ?? "General / Other", method: "heuristic" };
}

const URGENCY_WORDS = ["urgent", "asap", "immediately", "emergency", "deadline", "important", "critical"];

export function importancePriority(userMessage: string, driftEvent: DriftEvent | null): { label: string; method: "heuristic" } {
  const lower = userMessage.toLowerCase();
  const hasUrgency = URGENCY_WORDS.some((w) => lower.includes(w));
  const isComplex = userMessage.split(/\s+/).length > 40 || (userMessage.match(/\?/g)?.length ?? 0) > 1;
  const severeDrift = driftEvent?.detected && (driftEvent.severity === "high" || driftEvent.severity === "critical");
  const switchAttempt = driftEvent?.persona_switch_attempt;
  if (hasUrgency || severeDrift || switchAttempt) return { label: "High", method: "heuristic" };
  if (isComplex || userMessage.includes("?")) return { label: "Medium", method: "heuristic" };
  return { label: "Low", method: "heuristic" };
}

const RISK_KEYWORDS: Record<string, string[]> = {
  High: ["suicide", "self-harm", "kill myself", "weapon", "explosive", "illegal drug"],
  Medium: ["diagnosis", "prescription", "lawsuit", "medical condition", "legal advice", "financial advice", "ssn", "social security number"],
};

export function riskSensitivity(userMessage: string, driftEvent: DriftEvent | null): { label: string; method: "heuristic" } {
  const lower = userMessage.toLowerCase();
  if (driftEvent?.persona_switch_attempt) return { label: "High — persona hijack attempt", method: "heuristic" };
  if (RISK_KEYWORDS.High.some((w) => lower.includes(w))) return { label: "High", method: "heuristic" };
  if (RISK_KEYWORDS.Medium.some((w) => lower.includes(w))) return { label: "Medium", method: "heuristic" };
  return { label: "Low", method: "heuristic" };
}

export function reasoningEvidence(driftEvent: DriftEvent | null): string[] {
  if (!driftEvent) return ["No drift check has run yet for this turn."];
  const lines: string[] = [];
  if (driftEvent.reason) lines.push(driftEvent.reason);
  if (driftEvent.persona_switch_attempt) {
    lines.push(
      `Intent classifier detected a persona-switch attempt` +
      (driftEvent.requested_role ? ` (requested role: "${driftEvent.requested_role}")` : "") +
      " — request was blocked before generation."
    );
  }
  const weakDims = Object.entries(driftEvent.dimensions)
    .filter(([, v]) => v < 0.85)
    .sort((a, b) => a[1] - b[1]);
  if (weakDims.length) {
    lines.push("Weakest dimensions: " + weakDims.map(([k, v]) => `${k} (${Math.round(v * 100)}%)`).join(", "));
  }
  if (driftEvent.scope_similarity !== null && driftEvent.scope_similarity !== undefined) {
    lines.push(`Scope topical similarity: ${(driftEvent.scope_similarity * 100).toFixed(1)}% (classification: ${driftEvent.scope_classification})`);
  }
  if (driftEvent.context_contradictions?.length) {
    lines.push(
      ...driftEvent.context_contradictions.map(
        (c) => `Contradicted an earlier commitment ("${c.prior_commitment}" vs "${c.contradicting_claim}")`
      )
    );
  }
  if (driftEvent.method) {
    const methodLabels: Record<string, string> = {
      llm_intent_classifier: "Semantic intent classifier (LLM-based, not keyword matching)",
      fallback_regex_and_lexical: "Degraded fallback (classifier unavailable — used regex + lexical similarity)",
    };
    lines.push(`Detection method: ${methodLabels[driftEvent.method] ?? driftEvent.method} (${driftEvent.detector_version || "unversioned"})`);
  }
  return lines.length ? lines : ["No specific issues flagged — response scored within normal range on all dimensions."];
}

/**
 * Maps a turn's real backend data onto spec Part 26's fixed status
 * vocabulary — the single place this mapping happens, so the chat bubbles
 * and the analysis pane render the exact same badges for the exact same
 * turn rather than two components independently reinventing "what counts
 * as drift_prevented". Order matters: badges are meant to be read left to
 * right as a short narrative of what happened on this turn.
 */
export function boundaryStatusesForTurn(driftEvent: DriftEvent | null, repairEvent: RepairEvent | null): BoundaryStatus[] {
  if (!driftEvent) return [];

  if (driftEvent.drift_type === "persona_boundary_enforced") {
    const statuses: BoundaryStatus[] = [];
    statuses.push(driftEvent.persona_switch_attempt ? "drift_attempt" : "out_of_scope");
    statuses.push("drift_prevented");
    return statuses;
  }

  if (!driftEvent.detected) {
    return []; // ordinary in-scope turn — no badge needed, absence of a badge IS the "nothing happened" signal
  }

  // Post-hoc detector caught actual drift the pre-generation gate didn't prevent.
  const statuses: BoundaryStatus[] = ["drift_detected"];
  if (repairEvent) statuses.push(repairEvent.success ? "correction_successful" : "correction_failed");
  return statuses;
}
