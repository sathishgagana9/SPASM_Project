/**
 * Thin fetch wrapper for the RAISE backend (formerly Anchora / SPASM++). No mock data lives
 * here — every function returns real backend data or throws.
 */
import type {
  ApiErrorBody,
  ConnectionStatus,
  Conversation,
  DashboardSummary,
  DriftEvent,
  Message,
  Persona,
  PersonaInput,
  ProviderHealthResponse,
  RepairEvent,
  ResearchNote,
  ResearchNoteInput,
  SendMessageResponse,
  StreamEvent,
} from "../types";

const BASE = "/api";

export class ApiError extends Error {
  errorType: ApiErrorBody["error_type"];
  constructor(message: string, errorType: ApiErrorBody["error_type"] = "unknown") {
    super(message);
    this.errorType = errorType;
  }
}

async function parseErrorBody(res: Response): Promise<ApiError> {
  try {
    const json = await res.json();
    // FastAPI wraps our {message, error_type} dict under "detail"
    const detail = json.detail;
    if (detail && typeof detail === "object" && "message" in detail) {
      return new ApiError(detail.message, detail.error_type ?? "unknown");
    }
    if (typeof detail === "string") return new ApiError(detail, "unknown");
    return new ApiError(`${res.status} ${res.statusText}`, "unknown");
  } catch {
    return new ApiError(`${res.status} ${res.statusText}`, "unknown");
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw await parseErrorBody(res);
  if (res.status === 204) return undefined as T;
  return res.json();
}

/** Reads an SSE response body and yields parsed StreamEvent objects as they arrive. */
async function* streamRequest(path: string, body: unknown): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok || !res.body) throw await parseErrorBody(res);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.split("\n").find((l) => l.startsWith("data:"));
      if (!line) continue;
      const jsonStr = line.slice("data:".length).trim();
      if (!jsonStr) continue;
      try {
        yield JSON.parse(jsonStr) as StreamEvent;
      } catch {
        // ignore malformed chunk rather than killing the whole stream
      }
    }
  }
}

export const api = {
  health: () => request<{ status: string; environment: string }>("/health"),
  providerHealth: () => request<ProviderHealthResponse>("/health/providers"),

  listPersonas: () => request<Persona[]>("/personas"),
  createPersona: (data: PersonaInput) => request<Persona>("/personas", { method: "POST", body: JSON.stringify(data) }),
  updatePersona: (id: string, data: PersonaInput) =>
    request<Persona>(`/personas/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deletePersona: (id: string) => request<void>(`/personas/${id}`, { method: "DELETE" }),
  duplicatePersona: (id: string) => request<Persona>(`/personas/${id}/duplicate`, { method: "POST" }),
  activatePersona: (id: string) => request<Persona>(`/personas/${id}/activate`, { method: "POST" }),
  deactivatePersona: (id: string) => request<Persona>(`/personas/${id}/deactivate`, { method: "POST" }),
  connectPersona: (id: string, provider: string, model: string) =>
    request<Persona>(`/personas/${id}/connect`, { method: "POST", body: JSON.stringify({ provider, model }) }),
  disconnectPersona: (id: string) => request<Persona>(`/personas/${id}/disconnect`, { method: "POST" }),
  testConnection: (id: string) => request<ConnectionStatus>(`/personas/${id}/test-connection`, { method: "POST" }),
  runPersona: (id: string) => request<Persona>(`/personas/${id}/run`, { method: "POST" }),
  stopPersona: (id: string) => request<Persona>(`/personas/${id}/stop`, { method: "POST" }),

  dashboardSummary: () => request<DashboardSummary>("/dashboard/summary"),

  listModels: (provider: string) => request<{ provider: string; models: string[] }>(`/providers/${provider}/models`),

  createConversation: (data: { persona_id: string; provider: string; model: string; title?: string }) =>
    request<Conversation>("/conversations", { method: "POST", body: JSON.stringify(data) }),
  listConversations: () => request<Conversation[]>("/conversations"),
  renameConversation: (id: string, title: string) =>
    request<Conversation>(`/conversations/${id}`, { method: "PATCH", body: JSON.stringify({ title }) }),
  deleteConversation: (id: string) => request<void>(`/conversations/${id}`, { method: "DELETE" }),
  listMessages: (conversationId: string) => request<Message[]>(`/conversations/${conversationId}/messages`),
  listDriftEvents: (conversationId: string) => request<DriftEvent[]>(`/conversations/${conversationId}/drift-events`),
  listRepairEvents: (conversationId: string) => request<RepairEvent[]>(`/conversations/${conversationId}/repair-events`),
  sendMessage: (conversationId: string, content: string, monitor = true) =>
    request<SendMessageResponse>(`/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, monitor }),
    }),
  streamMessage: (conversationId: string, content: string, monitor = true) =>
    streamRequest(`/conversations/${conversationId}/messages/stream`, { content, monitor }),

  listResearchNotes: () => request<ResearchNote[]>("/research"),
  createResearchNote: (data: ResearchNoteInput) => request<ResearchNote>("/research", { method: "POST", body: JSON.stringify(data) }),
  updateResearchNote: (id: string, data: ResearchNoteInput) =>
    request<ResearchNote>(`/research/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteResearchNote: (id: string) => request<void>(`/research/${id}`, { method: "DELETE" }),

  listExperiments: () =>
    request<{ experiment_id: string; timestamp: string; git_commit: string | null; n_records: number; models: string[] }[]>(
      "/experiments"
    ),
};
