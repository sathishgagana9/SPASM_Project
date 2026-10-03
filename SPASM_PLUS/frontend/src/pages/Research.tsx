import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, ChevronDown, ChevronUp, FlaskConical } from "lucide-react";
import { api } from "../services/api";
import { ListEditor } from "../components/ListEditor";
import type { ResearchNote, ResearchNoteInput } from "../types";

const EMPTY: ResearchNoteInput = {
  title: "", topic: "", questions: [], notes: "", sources: [], findings: "", summary: "",
  persona_id: null, conversation_id: null,
};

export function Research() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<ResearchNoteInput>(EMPTY);
  const [expanded, setExpanded] = useState<string | null>(null);

  const notes = useQuery({ queryKey: ["research-notes"], queryFn: api.listResearchNotes });
  const experiments = useQuery({ queryKey: ["experiments"], queryFn: api.listExperiments });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["research-notes"] });

  const create = useMutation({
    mutationFn: api.createResearchNote,
    onSuccess: () => { invalidate(); setForm(EMPTY); },
  });
  const update = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ResearchNoteInput }) => api.updateResearchNote(id, data),
    onSuccess: invalidate,
  });
  const remove = useMutation({ mutationFn: api.deleteResearchNote, onSuccess: invalidate });

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Research</h1>
        <p className="text-sm text-slate-500">Working research notes — topic, questions, sources, findings, summary.</p>
      </div>

      <section className="rounded-xl border border-lab-border bg-lab-panel p-4">
        <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-200">
          <FlaskConical size={14} /> Experiment Results
        </div>
        {experiments.isLoading && <p className="text-xs text-slate-500">Loading…</p>}
        {experiments.data?.length === 0 && (
          <p className="text-xs text-slate-500">
            NOT YET EVALUATED — no experiment result files found in <code>research/results/raw/</code>. Run one of
            the scripts in <code>research/experiments/</code> against a live model to populate this.
          </p>
        )}
        {experiments.data && experiments.data.length > 0 && (
          <div className="space-y-1">
            {experiments.data.map((e) => (
              <div key={e.experiment_id} className="flex items-center justify-between rounded-lg border border-lab-border px-3 py-2 text-xs">
                <div>
                  <div className="mono text-slate-200">{e.experiment_id}</div>
                  <div className="text-slate-500">{new Date(e.timestamp).toLocaleString()} · {e.models.join(", ")}</div>
                </div>
                <div className="mono text-slate-400">{e.n_records} records</div>
              </div>
            ))}
          </div>
        )}
      </section>

      <form
        onSubmit={(e) => { e.preventDefault(); if (form.title.trim()) create.mutate(form); }}
        className="space-y-3 rounded-xl border border-lab-border bg-lab-panel p-4"
      >
        <div className="grid grid-cols-2 gap-3">
          <input
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="Title"
            className="rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200"
          />
          <input
            value={form.topic}
            onChange={(e) => setForm({ ...form, topic: e.target.value })}
            placeholder="Topic"
            className="rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200"
          />
        </div>
        <ListEditor label="Questions" items={form.questions} onChange={(v) => setForm({ ...form, questions: v })} />
        <textarea
          value={form.notes}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
          placeholder="Notes"
          rows={3}
          className="w-full rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200"
        />
        <ListEditor label="Sources" items={form.sources} onChange={(v) => setForm({ ...form, sources: v })} />
        <textarea
          value={form.findings}
          onChange={(e) => setForm({ ...form, findings: e.target.value })}
          placeholder="Findings"
          rows={2}
          className="w-full rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200"
        />
        <textarea
          value={form.summary}
          onChange={(e) => setForm({ ...form, summary: e.target.value })}
          placeholder="Summary"
          rows={2}
          className="w-full rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-200"
        />
        <button
          type="submit"
          disabled={create.isPending || !form.title.trim()}
          className="flex items-center gap-1 rounded-lg bg-lab-accent/90 px-4 py-2 text-sm font-medium text-lab-bg hover:bg-lab-accent disabled:opacity-50"
        >
          <Plus size={14} /> Save Research
        </button>
      </form>

      <div className="space-y-2">
        {notes.data?.map((n: ResearchNote) => (
          <div key={n.id} className="rounded-xl border border-lab-border bg-lab-panel">
            <div className="flex items-center justify-between px-4 py-3">
              <button onClick={() => setExpanded(expanded === n.id ? null : n.id)} className="flex items-center gap-2 text-left">
                {expanded === n.id ? <ChevronUp size={14} className="text-slate-500" /> : <ChevronDown size={14} className="text-slate-500" />}
                <div>
                  <div className="text-sm font-medium text-slate-200">{n.title}</div>
                  <div className="text-xs text-slate-500">{n.topic}</div>
                </div>
              </button>
              <button onClick={() => remove.mutate(n.id)} className="rounded-lg p-2 text-slate-500 hover:bg-lab-danger/10 hover:text-lab-danger">
                <Trash2 size={14} />
              </button>
            </div>
            {expanded === n.id && (
              <div className="space-y-2 border-t border-lab-border px-4 py-3 text-xs text-slate-400">
                <div><span className="text-slate-500">Questions:</span> {n.questions.join(", ") || "—"}</div>
                <div><span className="text-slate-500">Notes:</span> {n.notes || "—"}</div>
                <div><span className="text-slate-500">Sources:</span> {n.sources.join(", ") || "—"}</div>
                <div><span className="text-slate-500">Findings:</span> {n.findings || "—"}</div>
                <div><span className="text-slate-500">Summary:</span> {n.summary || "—"}</div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
