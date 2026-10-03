import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2, Plus, Copy, Power, ChevronDown, ChevronUp } from "lucide-react";
import { api } from "../services/api";
import { ListEditor } from "../components/ListEditor";
import type { Persona, PersonaInput } from "../types";

function randomInternalName() {
  return `persona-${Math.random().toString(36).slice(2, 8)}`;
}

const EMPTY: PersonaInput = {
  name: randomInternalName(),
  description: "",
  identity: "",
  tone: "",
  scope: "",
  personality_traits: [],
  goals: [],
  values: [],
  behavior_rules: [],
  knowledge_boundaries: [],
  response_constraints: [],
  forbidden_behaviors: [],
  example_responses: [],
};

export function Personas({ focusPersonaId }: { focusPersonaId?: string | null }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<PersonaInput>(EMPTY);
  const [expanded, setExpanded] = useState<string | null>(null);

  const personas = useQuery({ queryKey: ["personas"], queryFn: api.listPersonas });

  useEffect(() => {
    if (focusPersonaId) setExpanded(focusPersonaId);
  }, [focusPersonaId]);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["personas"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
  };

  const createMutation = useMutation({
    mutationFn: api.createPersona,
    onSuccess: () => {
      invalidate();
      setForm({ ...EMPTY, name: randomInternalName() });
    },
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: PersonaInput }) => api.updatePersona(id, data),
    onSuccess: invalidate,
  });
  const deleteMutation = useMutation({ mutationFn: api.deletePersona, onSuccess: invalidate });
  const duplicateMutation = useMutation({ mutationFn: api.duplicatePersona, onSuccess: invalidate });
  const activateMutation = useMutation({ mutationFn: api.activatePersona, onSuccess: invalidate });
  const deactivateMutation = useMutation({ mutationFn: api.deactivatePersona, onSuccess: invalidate });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Persona Studio</h1>
        <p className="text-sm text-slate-500">
          Advanced configuration. Personas are shown generically as "Persona N" everywhere else in the app —
          the internal reference name here is only used to build the system prompt and is never displayed
          elsewhere.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          createMutation.mutate(form);
        }}
        className="space-y-4 rounded-xl border border-lab-border bg-lab-panel p-4"
      >
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">Tone</label>
          <input
            value={form.tone}
            onChange={(e) => setForm({ ...form, tone: e.target.value })}
            placeholder="Formal and academic"
            className="w-full rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200 outline-none focus:border-lab-accent"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">Description</label>
          <input
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="w-full rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200 outline-none focus:border-lab-accent"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">
            Scope <span className="normal-case text-slate-600">(what this persona should stay within — enforced in the system prompt)</span>
          </label>
          <textarea
            value={form.scope}
            onChange={(e) => setForm({ ...form, scope: e.target.value })}
            rows={2}
            placeholder="Academic education — explaining concepts, answering study questions, guiding learning."
            className="w-full rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200 outline-none focus:border-lab-accent"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">Identity</label>
          <textarea
            value={form.identity}
            onChange={(e) => setForm({ ...form, identity: e.target.value })}
            rows={2}
            placeholder="A patient, encouraging academic tutor who explains concepts step by step."
            className="w-full rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200 outline-none focus:border-lab-accent"
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <ListEditor label="Personality Traits" items={form.personality_traits} onChange={(v) => setForm({ ...form, personality_traits: v })} />
          <ListEditor label="Goals" items={form.goals} onChange={(v) => setForm({ ...form, goals: v })} />
          <ListEditor label="Values" items={form.values} onChange={(v) => setForm({ ...form, values: v })} />
          <ListEditor label="Behavioral Rules" items={form.behavior_rules} onChange={(v) => setForm({ ...form, behavior_rules: v })} />
          <ListEditor label="Knowledge Boundaries" hint="Topics the persona should not engage with." items={form.knowledge_boundaries} onChange={(v) => setForm({ ...form, knowledge_boundaries: v })} />
          <ListEditor label="Response Constraints" items={form.response_constraints} onChange={(v) => setForm({ ...form, response_constraints: v })} />
          <ListEditor label="Forbidden Behaviors" items={form.forbidden_behaviors} onChange={(v) => setForm({ ...form, forbidden_behaviors: v })} />
          <ListEditor label="Example Responses" items={form.example_responses} onChange={(v) => setForm({ ...form, example_responses: v })} />
        </div>

        <details className="rounded-lg border border-lab-border p-3">
          <summary className="cursor-pointer text-xs uppercase tracking-wide text-slate-400">Advanced</summary>
          <div className="mt-2">
            <label className="mb-1 block text-xs text-slate-500">
              Internal reference name (optional — used only to build the system prompt, never shown elsewhere)
            </label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200 outline-none focus:border-lab-accent"
            />
          </div>
        </details>

        <button
          type="submit"
          disabled={createMutation.isPending}
          className="flex items-center gap-1 rounded-lg bg-lab-accent/90 px-4 py-2 text-sm font-medium text-lab-bg hover:bg-lab-accent disabled:opacity-50"
        >
          <Plus size={16} /> Create Persona
        </button>
        {createMutation.isError && <p className="text-xs text-lab-danger">{(createMutation.error as Error).message}</p>}
      </form>

      <div className="space-y-2">
        {personas.isLoading && <div className="text-sm text-slate-500">Loading…</div>}
        {personas.isError && <div className="text-sm text-lab-danger">Could not reach the backend.</div>}
        {personas.data?.map((p: Persona) => (
          <div key={p.id} className="rounded-xl border border-lab-border bg-lab-panel">
            <div className="flex items-center justify-between px-4 py-3">
              <button
                className="flex items-center gap-2 text-left"
                onClick={() => setExpanded(expanded === p.id ? null : p.id)}
              >
                {expanded === p.id ? <ChevronUp size={14} className="text-slate-500" /> : <ChevronDown size={14} className="text-slate-500" />}
                <div>
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
                    {p.display_label}
                    {p.is_active && <span className="rounded-full bg-lab-ok/10 px-2 py-0.5 text-[10px] uppercase text-lab-ok">Enabled</span>}
                  </div>
                  <div className="text-xs text-slate-500">{p.description || "—"}</div>
                </div>
              </button>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => (p.is_active ? deactivateMutation.mutate(p.id) : activateMutation.mutate(p.id))}
                  className={`rounded-lg p-2 hover:bg-white/5 ${p.is_active ? "text-lab-ok" : "text-slate-500"}`}
                  aria-label="Toggle enabled"
                  title={p.is_active ? "Disable" : "Enable"}
                >
                  <Power size={16} />
                </button>
                <button onClick={() => duplicateMutation.mutate(p.id)} className="rounded-lg p-2 text-slate-500 hover:bg-white/5" aria-label="Duplicate">
                  <Copy size={16} />
                </button>
                <button onClick={() => deleteMutation.mutate(p.id)} className="rounded-lg p-2 text-slate-500 hover:bg-lab-danger/10 hover:text-lab-danger" aria-label="Delete">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
            {expanded === p.id && (
              <div className="space-y-3 border-t border-lab-border px-4 py-3 text-xs text-slate-400">
                <div><span className="text-slate-500">Identity:</span> {p.identity || "—"}</div>
                <div><span className="text-slate-500">Scope:</span> {p.scope || "—"}</div>
                <div><span className="text-slate-500">Tone:</span> {p.tone || "—"}</div>
                <div><span className="text-slate-500">Traits:</span> {p.personality_traits.join(", ") || "—"}</div>
                <div><span className="text-slate-500">Goals:</span> {p.goals.join(", ") || "—"}</div>
                <div><span className="text-slate-500">Behavior rules:</span> {p.behavior_rules.join(", ") || "—"}</div>
                <div><span className="text-slate-500">Forbidden:</span> {p.forbidden_behaviors.join(", ") || "—"}</div>
                <details>
                  <summary className="cursor-pointer text-slate-500">Advanced (internal reference name)</summary>
                  <div className="mt-2 flex items-center gap-2">
                    <input
                      defaultValue={p.name}
                      onBlur={(e) => {
                        if (e.target.value !== p.name) {
                          updateMutation.mutate({ id: p.id, data: { ...p, name: e.target.value } });
                        }
                      }}
                      className="w-full rounded-lg border border-lab-border bg-lab-bg px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-lab-accent"
                    />
                  </div>
                </details>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
