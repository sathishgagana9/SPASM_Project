import { useState } from "react";
import { Plus, X } from "lucide-react";

interface ListEditorProps {
  label: string;
  hint?: string;
  items: string[];
  onChange: (items: string[]) => void;
}

export function ListEditor({ label, hint, items, onChange }: ListEditorProps) {
  const [draft, setDraft] = useState("");

  const add = () => {
    if (draft.trim()) {
      onChange([...items, draft.trim()]);
      setDraft("");
    }
  };

  return (
    <div>
      <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">{label}</label>
      {hint && <p className="mb-2 text-xs text-slate-600">{hint}</p>}
      <div className="mb-2 flex flex-wrap gap-2">
        {items.map((item, i) => (
          <span
            key={i}
            className="flex items-center gap-1 rounded-full border border-lab-border bg-lab-bg px-3 py-1 text-xs text-slate-300"
          >
            {item}
            <button
              type="button"
              onClick={() => onChange(items.filter((_, idx) => idx !== i))}
              className="text-slate-500 hover:text-lab-danger"
              aria-label={`Remove ${item}`}
            >
              <X size={12} />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              add();
            }
          }}
          placeholder={`Add to ${label.toLowerCase()}…`}
          className="flex-1 rounded-lg border border-lab-border bg-lab-bg px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-lab-accent"
        />
        <button
          type="button"
          onClick={add}
          className="rounded-lg border border-lab-border px-2 text-slate-400 hover:border-lab-accent hover:text-lab-accent"
        >
          <Plus size={14} />
        </button>
      </div>
    </div>
  );
}
