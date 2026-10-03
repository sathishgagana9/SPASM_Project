import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Send, Loader2, X, Lock } from "lucide-react";
import { api, ApiError } from "../services/api";
import { Markdown } from "../components/Markdown";
import { ErrorNotice } from "../components/ErrorNotice";
import { AnalysisPane } from "../components/AnalysisPane";
import { BoundaryStatusBadge } from "../components/BoundaryStatusBadge";
import type { ApiErrorBody, DriftEvent, Persona } from "../types";
import { buildTurnAnalyses, boundaryStatusesForTurn } from "../lib/turnAnalysis";

function PersonaPicker({
  personas, defaultPersonaId, onStart, onCancel,
}: {
  personas: Persona[];
  defaultPersonaId: string | null;
  onStart: (personaId: string, provider: string, model: string) => void;
  onCancel: (() => void) | null;
}) {
  const [personaId, setPersonaId] = useState(defaultPersonaId ?? "");
  const [model, setModel] = useState("");

  return (
    <div className="mx-auto max-w-2xl space-y-4 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-100">Select a persona to start chatting</h1>
        {onCancel && (
          <button onClick={onCancel} className="text-slate-500 hover:text-slate-300"><X size={18} /></button>
        )}
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {personas.map((p) => (
          <button
            key={p.id}
            onClick={() => setPersonaId(p.id)}
            className={`rounded-xl border p-3 text-left transition-colors ${
              personaId === p.id ? "border-lab-accent bg-lab-accent/10" : "border-lab-border bg-lab-panel hover:border-slate-600"
            }`}
          >
            <div className="text-sm font-medium text-slate-100">{p.name}</div>
            <div className="mt-1 text-xs text-slate-500">{p.description}</div>
          </button>
        ))}
      </div>

      {personaId && (
        <div className="space-y-3 rounded-xl border border-lab-border bg-lab-panel p-4">
          <div>
            <label className="mb-1 block text-xs uppercase text-slate-400">Provider</label>
            <div className="w-full rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-400">Groq</div>
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase text-slate-400">Model name</label>
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="openai/gpt-oss-20b"
              className="w-full rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200"
            />
          </div>
          <button
            onClick={() => onStart(personaId, "groq", model)}
            disabled={!model.trim()}
            className="w-full rounded-lg bg-lab-accent/90 px-4 py-2 text-sm font-medium text-lab-bg hover:bg-lab-accent disabled:opacity-50"
          >
            Start Chatting
          </button>
        </div>
      )}
    </div>
  );
}

export function ChatPage({
  conversationId, defaultPersonaId, monitoringEnabled, onConversationCreated,
}: {
  conversationId: string | null;
  defaultPersonaId: string | null;
  monitoringEnabled: boolean;
  onConversationCreated: (id: string) => void;
}) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState("");
  const [streamingText, setStreamingText] = useState<string | null>(null);
  const [streamError, setStreamError] = useState<ApiErrorBody["error_type"] | null>(null);
  const [liveDrift, setLiveDrift] = useState<DriftEvent | null>(null);
  const [isSending, setIsSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const personas = useQuery({ queryKey: ["personas"], queryFn: api.listPersonas });

  const conversation = useQuery({
    queryKey: ["conversation-lookup", conversationId],
    queryFn: async () => (await api.listConversations()).find((c) => c.id === conversationId) ?? null,
    enabled: !!conversationId,
  });

  const messages = useQuery({
    queryKey: ["messages", conversationId],
    queryFn: () => api.listMessages(conversationId!),
    enabled: !!conversationId,
  });

  const driftEvents = useQuery({
    queryKey: ["drift-events", conversationId],
    queryFn: () => api.listDriftEvents(conversationId!),
    enabled: !!conversationId,
  });

  const repairEvents = useQuery({
    queryKey: ["repair-events", conversationId],
    queryFn: () => api.listRepairEvents(conversationId!),
    enabled: !!conversationId,
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.data, streamingText]);

  useEffect(() => {
    setLiveDrift(null);
    setStreamingText(null);
    setStreamError(null);
  }, [conversationId]);

  const createConversation = useMutation({
    mutationFn: (args: { persona_id: string; provider: string; model: string }) =>
      api.createConversation(args),
    onSuccess: (convo) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      onConversationCreated(convo.id);
    },
  });

  async function handleSend(content: string) {
    if (!conversationId || !content.trim() || isSending) return;
    setDraft("");
    setIsSending(true);
    setStreamingText("");
    setStreamError(null);

    try {
      for await (const event of api.streamMessage(conversationId, content, monitoringEnabled)) {
        if (event.type === "token") {
          setStreamingText((prev) => (prev ?? "") + event.content);
        } else if (event.type === "error") {
          setStreamError(event.error_type);
          setStreamingText(null);
        } else if (event.type === "drift") {
          setLiveDrift(event as unknown as DriftEvent);
        } else if (event.type === "repair" && event.repaired_content) {
          setStreamingText(event.repaired_content);
        } else if (event.type === "final") {
          queryClient.invalidateQueries({ queryKey: ["messages", conversationId] });
          queryClient.invalidateQueries({ queryKey: ["drift-events", conversationId] });
          queryClient.invalidateQueries({ queryKey: ["repair-events", conversationId] });
          queryClient.invalidateQueries({ queryKey: ["conversations"] });
          queryClient.invalidateQueries({ queryKey: ["conversation-lookup", conversationId] });
          setStreamingText(null);
        }
      }
    } catch (e) {
      const err = e as ApiError;
      setStreamError(err.errorType ?? "unknown");
      setStreamingText(null);
    } finally {
      setIsSending(false);
    }
  }

  if (!conversationId) {
    return (
      <PersonaPicker
        personas={personas.data ?? []}
        defaultPersonaId={defaultPersonaId}
        onCancel={null}
        onStart={(personaId, provider, model) => createConversation.mutate({ persona_id: personaId, provider, model })}
      />
    );
  }

  const persona = personas.data?.find((p) => p.id === conversation.data?.persona_id) ?? null;
  const turnsForBadges = buildTurnAnalyses(messages.data ?? [], driftEvents.data ?? [], repairEvents.data ?? []);
  const badgesByAssistantMessageId = new Map(
    turnsForBadges.map((t) => [t.assistantMessage.id, boundaryStatusesForTurn(t.driftEvent, t.repairEvent)] as const)
  );

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="border-b border-lab-border px-6 py-3">
          <div className="flex items-center gap-1.5">
            <Lock size={12} className="text-slate-500" />
            <span className="text-sm font-medium text-slate-100">{persona?.name ?? "…"}</span>
            <span className="text-[10px] uppercase tracking-wide text-slate-600">— persona locked</span>
          </div>
          <div className="text-xs text-slate-500">{persona?.description}</div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="mx-auto max-w-2xl space-y-4">
            {messages.isLoading && (
              <div className="space-y-3 pt-4">
                <div className="h-10 w-2/3 animate-pulse rounded-xl bg-lab-panel" />
                <div className="ml-auto h-10 w-1/2 animate-pulse rounded-xl bg-lab-panel" />
                <div className="h-10 w-3/5 animate-pulse rounded-xl bg-lab-panel" />
              </div>
            )}

            {!messages.isLoading && messages.data?.length === 0 && (
              <div className="flex flex-col items-center gap-2 pt-16 text-center text-slate-500">
                <Lock size={20} className="text-slate-600" />
                <p className="text-sm">
                  Locked to <span className="text-slate-300">{persona?.name}</span>.
                </p>
                <p className="max-w-xs text-xs">
                  Every message is checked against this persona's configured scope before a response is generated —
                  send a message to get started.
                </p>
              </div>
            )}

            {messages.data?.map((m) => {
              const badges = m.role === "assistant" ? badgesByAssistantMessageId.get(m.id) ?? [] : [];
              const isBoundaryEnforced = badges.includes("drift_prevented");
              const isUncorrectedDrift = badges.includes("drift_detected") && !badges.includes("correction_successful");
              return (
                <div key={m.id} className={m.role === "user" ? "ml-auto max-w-lg" : "max-w-lg"}>
                  {badges.length > 0 && (
                    <div className="mb-1 flex flex-wrap gap-1">
                      {badges.map((b) => <BoundaryStatusBadge key={b} status={b} size="xs" />)}
                    </div>
                  )}
                  <div
                    className={`rounded-xl px-4 py-2.5 text-sm ${m.role === "user" ? "bg-lab-accent/10 text-slate-100" : "bg-lab-panel text-slate-200"} ${
                      isBoundaryEnforced ? "border-l-2 border-lab-accent" : isUncorrectedDrift ? "border-l-2 border-lab-danger" : ""
                    }`}
                  >
                    <Markdown content={m.content} />
                    {m.was_repaired && <div className="mono mt-1 text-[10px] uppercase text-lab-warn">repaired response</div>}
                  </div>
                </div>
              );
            })}

            {streamingText !== null && (
              <div className="max-w-lg">
                <div className="rounded-xl bg-lab-panel px-4 py-2.5 text-sm text-slate-200">
                  <Markdown content={streamingText || "…"} />
                </div>
              </div>
            )}

            {isSending && streamingText === "" && (
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Loader2 size={12} className="animate-spin" /> Generating…
              </div>
            )}

            {streamError && (
              <ErrorNotice
                errorType={streamError}
                onRetry={() => handleSend(draft || messages.data?.at(-1)?.content || "")}
              />
            )}

            <div ref={bottomRef} />
          </div>
        </div>

        <form
          onSubmit={(e) => { e.preventDefault(); handleSend(draft); }}
          className="border-t border-lab-border p-4"
        >
          <div className="mx-auto flex max-w-2xl items-end gap-2">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(draft);
                }
              }}
              placeholder="Message… (Enter to send, Shift+Enter for a new line)"
              rows={1}
              className="max-h-40 flex-1 resize-none rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200 outline-none focus:border-lab-accent"
            />
            <button
              type="submit"
              disabled={isSending || !draft.trim()}
              className="rounded-lg bg-lab-accent/90 p-2.5 text-lab-bg hover:bg-lab-accent disabled:opacity-50"
            >
              <Send size={16} />
            </button>
          </div>
        </form>
      </div>

      <AnalysisPane
        persona={persona}
        messages={messages.data ?? []}
        driftEvents={driftEvents.data ?? []}
        repairEvents={repairEvents.data ?? []}
        monitoringEnabled={monitoringEnabled}
        liveDrift={liveDrift}
      />
    </div>
  );
}
