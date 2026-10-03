export interface Persona {
  id: string;
  display_index: number;
  display_label: string;
  name: string;
  description: string;
  identity: string;
  tone: string;
  scope: string;
  personality_traits: string[];
  goals: string[];
  values: string[];
  behavior_rules: string[];
  knowledge_boundaries: string[];
  response_constraints: string[];
  forbidden_behaviors: string[];
  example_responses: string[];
  is_active: boolean;
  default_provider: string;
  default_model: string;
  connected: boolean;
  running: boolean;
  active_conversation_id: string | null;
  last_connection_error: string;
  created_at: string;
  updated_at: string;
}

export type PersonaInput = Omit<
  Persona,
  | "id"
  | "display_index"
  | "display_label"
  | "is_active"
  | "default_provider"
  | "default_model"
  | "connected"
  | "running"
  | "active_conversation_id"
  | "last_connection_error"
  | "created_at"
  | "updated_at"
>;

export interface ConnectionStatus {
  connected: boolean;
  status: string;
  error: string;
}

export interface DashboardSummary {
  total_personas: number;
  connected: number;
  running: number;
  errors: number;
  available_providers: string[];
}

export interface ProviderHealth {
  status: string;
  base_url?: string;
}

export interface ProviderHealthResponse {
  groq: ProviderHealth;
}

export interface Conversation {
  id: string;
  persona_id: string;
  provider: string;
  model: string;
  title: string;
  stability_score: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  was_repaired: boolean;
  created_at: string;
}

export interface DriftEvent {
  id: string;
  message_id: string;
  detected: boolean;
  drift_type: string;
  severity: "none" | "low" | "medium" | "high" | "critical";
  confidence: number;
  drift_probability: number;
  dimensions: Record<string, number>;
  overall_stability: number;
  reason: string;
  method: string;
  detector_version: string;
  threshold_version: string;
  scope_classification: string;
  scope_similarity: number | null;
  context_contradictions: { prior_commitment: string; contradicting_claim: string; overlap: number }[];
  // Added for the intent-classifier / persona-boundary pipeline — describe
  // what the USER'S message was asking for, independent of whether the
  // assistant complied. This is what lets the UI distinguish "user attempted
  // a persona switch but the assistant correctly refused" from "the
  // assistant actually drifted" — see turnAnalysis.ts's driftAttribution.
  persona_switch_attempt: boolean;
  requested_role: string | null;
  requested_domain: string;
  created_at: string;
}

export interface RepairEvent {
  id: string;
  drift_event_id: string;
  operator: string;
  stability_before: number;
  stability_after: number;
  stability_improvement: number;
  success: boolean;
  duration_ms: number;
  token_overhead: number;
  quality_flags: string[];
  created_at: string;
}

export interface SendMessageResponse {
  user_message: Message;
  assistant_message: Message;
  drift_event: DriftEvent | null;
  repair_event: RepairEvent | null;
  conversation_stability: number;
}

export interface ResearchNote {
  id: string;
  title: string;
  topic: string;
  questions: string[];
  notes: string;
  sources: string[];
  findings: string;
  summary: string;
  persona_id: string | null;
  conversation_id: string | null;
  created_at: string;
  updated_at: string;
}

export type ResearchNoteInput = Omit<ResearchNote, "id" | "created_at" | "updated_at">;

export interface ApiErrorBody {
  message: string;
  error_type: "timeout" | "unreachable" | "auth" | "rate_limit" | "malformed" | "unknown";
}

// SSE event shapes from POST /conversations/{id}/messages/stream
export type StreamEvent =
  | { type: "token"; content: string }
  | { type: "error"; message: string; error_type: ApiErrorBody["error_type"] }
  | { type: "done"; content: string }
  | ({ type: "drift" } & DriftEvent)
  | ({ type: "repair" } & RepairEvent & { repaired_content: string })
  | { type: "final"; content: string; was_repaired: boolean; message_id: string };
