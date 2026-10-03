import { useEffect, useRef, useState } from "react";
import {
  Plus, MoreHorizontal, Pencil, Trash2, Check, X, ChevronDown,
  FlaskConical, Settings, ServerCog, LayoutDashboard, Users,
} from "lucide-react";
import { Wordmark } from "./Logo";
import type { Conversation, Persona } from "../types";

export type View = "chat" | "research" | "settings" | "system" | "manager" | "studio";

function ConversationRow({
  convo, personaLabel, active, onSelect, onRename, onDelete,
}: {
  convo: Conversation;
  personaLabel: string;
  active: boolean;
  onSelect: () => void;
  onRename: (title: string) => void;
  onDelete: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(convo.title);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  if (editing) {
    return (
      <div className="flex items-center gap-1 rounded-lg bg-white/5 px-2 py-1.5">
        <input
          autoFocus
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              onRename(draft);
              setEditing(false);
            }
            if (e.key === "Escape") setEditing(false);
          }}
          className="flex-1 rounded border border-lab-border bg-lab-bg px-1.5 py-0.5 text-xs text-slate-200"
        />
        <button onClick={() => { onRename(draft); setEditing(false); }} className="text-lab-ok"><Check size={12} /></button>
        <button onClick={() => setEditing(false)} className="text-slate-500"><X size={12} /></button>
      </div>
    );
  }

  return (
    <div
      className={`group flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs ${
        active ? "bg-lab-accent/10 text-lab-accent" : "text-slate-400 hover:bg-white/5"
      }`}
    >
      <button onClick={onSelect} className="flex-1 truncate text-left">
        <div className="truncate">{convo.title}</div>
        <div className="truncate text-[10px] text-slate-600">{personaLabel}</div>
      </button>
      <div className="relative">
        <button
          onClick={() => setMenuOpen((s) => !s)}
          className="rounded p-1 opacity-0 hover:bg-white/10 group-hover:opacity-100"
        >
          <MoreHorizontal size={12} />
        </button>
        {menuOpen && (
          <div className="absolute right-0 top-6 z-10 w-32 rounded-lg border border-lab-border bg-lab-panel py-1 shadow-lg">
            {!confirmingDelete ? (
              <>
                <button
                  onClick={() => { setEditing(true); setMenuOpen(false); }}
                  className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-xs text-slate-300 hover:bg-white/5"
                >
                  <Pencil size={12} /> Rename
                </button>
                <button
                  onClick={() => setConfirmingDelete(true)}
                  className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-xs text-lab-danger hover:bg-white/5"
                >
                  <Trash2 size={12} /> Delete
                </button>
              </>
            ) : (
              <div className="px-3 py-1.5">
                <div className="mb-1 text-[10px] text-slate-400">Delete this chat?</div>
                <div className="flex gap-1">
                  <button
                    onClick={() => { onDelete(); setMenuOpen(false); setConfirmingDelete(false); }}
                    className="rounded bg-lab-danger/20 px-2 py-0.5 text-[10px] text-lab-danger"
                  >
                    Delete
                  </button>
                  <button
                    onClick={() => setConfirmingDelete(false)}
                    className="rounded border border-lab-border px-2 py-0.5 text-[10px] text-slate-400"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function AvailablePersonasDropdown({
  personas, selectedPersonaId, onSelectPersona, onManagePersonas,
}: {
  personas: Persona[];
  selectedPersonaId: string | null;
  onSelectPersona: (id: string) => void;
  onManagePersonas: () => void;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const selectedPersona = personas.find((p) => p.id === selectedPersonaId) ?? null;

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <div ref={containerRef} className="mb-1">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between rounded-lg border border-lab-border bg-lab-bg/60 px-2.5 py-2 text-xs text-slate-300 transition-colors hover:border-lab-accent/40 hover:bg-white/5"
      >
        <div className="min-w-0 text-left">
          <div className="font-medium">Available Personas</div>
          {!open && selectedPersona && (
            <div className="mt-0.5 flex items-center gap-1 truncate text-[10px] text-lab-accent">
              <Check size={9} /> {selectedPersona.name}
            </div>
          )}
        </div>
        <ChevronDown size={13} className={`shrink-0 text-slate-500 transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
      </button>

      <div
        className="overflow-hidden transition-all duration-200 ease-out"
        style={{ maxHeight: open ? personas.length * 34 + 8 : 0, opacity: open ? 1 : 0 }}
      >
        <div className="mt-1 space-y-0.5 rounded-lg border border-lab-border bg-lab-bg/40 p-1">
          {personas.map((p) => {
            const isSelected = p.id === selectedPersonaId;
            return (
              <button
                key={p.id}
                onClick={() => { onSelectPersona(p.id); setOpen(false); }}
                className={`flex w-full items-center gap-1.5 truncate rounded-md px-2 py-1.5 text-left text-xs transition-colors ${
                  isSelected ? "bg-lab-accent/10 text-lab-accent" : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                }`}
              >
                <Check size={11} className={isSelected ? "opacity-100" : "opacity-0"} />
                <span className="truncate">{p.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      <button
        onClick={onManagePersonas}
        className="group mt-1 flex w-full items-center justify-between px-2 py-1 text-xs text-lab-accent/80 transition-colors hover:text-lab-accent"
      >
        Manage Personas
        <span className="transition-transform group-hover:translate-x-0.5">→</span>
      </button>
    </div>
  );
}

export function Sidebar({
  view, onChangeView, conversations, personas, activeConversationId, defaultPersonaId,
  onSelectConversation, onNewChat, onRenameConversation, onDeleteConversation, onSelectPersonaForNewChat,
}: {
  view: View;
  onChangeView: (v: View) => void;
  conversations: Conversation[];
  personas: Persona[];
  activeConversationId: string | null;
  defaultPersonaId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onRenameConversation: (id: string, title: string) => void;
  onDeleteConversation: (id: string) => void;
  onSelectPersonaForNewChat: (personaId: string) => void;
}) {
  const personaById = Object.fromEntries(personas.map((p) => [p.id, p.name]));

  return (
    <aside className="relative z-10 flex w-64 shrink-0 flex-col overflow-hidden border-r border-lab-border bg-lab-panel/60 p-3">
      {/* Subtle radial cyan glow behind the brand area — very low-opacity, not a flashy effect */}
      <div
        className="pointer-events-none absolute -left-16 -top-16 h-56 w-56 rounded-full opacity-[0.15] blur-3xl"
        style={{ background: "radial-gradient(circle, #22d3ee 0%, transparent 70%)" }}
      />

      <div className="relative mb-4 px-1">
        <Wordmark size="md" />
      </div>

      <button
        onClick={onNewChat}
        className="group relative mb-4 flex items-center justify-center gap-1.5 overflow-hidden rounded-full bg-gradient-to-r from-lab-accent to-cyan-400 px-4 py-2 text-sm font-medium text-lab-bg shadow-[0_0_16px_rgba(34,211,238,0.35)] transition-all hover:shadow-[0_0_22px_rgba(34,211,238,0.55)] active:scale-[0.98]"
      >
        <Plus size={14} className="transition-transform group-hover:rotate-90" />
        New Chat
      </button>

      <AvailablePersonasDropdown
        personas={personas}
        selectedPersonaId={defaultPersonaId}
        onSelectPersona={onSelectPersonaForNewChat}
        onManagePersonas={() => onChangeView("manager")}
      />

      <div className="mt-3 flex-1 overflow-y-auto">
        <div className="mb-1.5 px-1 text-[10px] uppercase tracking-wide text-slate-500">Recent Chats</div>
        <div className="space-y-0.5">
          {conversations.length === 0 && <div className="px-2 py-1 text-xs text-slate-600">No conversations yet</div>}
          {conversations.map((c) => (
            <ConversationRow
              key={c.id}
              convo={c}
              personaLabel={personaById[c.persona_id] ?? "Unknown persona"}
              active={view === "chat" && activeConversationId === c.id}
              onSelect={() => { onSelectConversation(c.id); onChangeView("chat"); }}
              onRename={(title) => onRenameConversation(c.id, title)}
              onDelete={() => onDeleteConversation(c.id)}
            />
          ))}
        </div>
      </div>

      <div className="mt-3 space-y-0.5 border-t border-lab-border pt-3">
        {[
          { id: "research" as View, label: "Research", icon: FlaskConical },
          { id: "settings" as View, label: "Settings", icon: Settings },
          { id: "system" as View, label: "System Status", icon: ServerCog },
          { id: "manager" as View, label: "Persona Manager", icon: LayoutDashboard },
          { id: "studio" as View, label: "Persona Studio", icon: Users },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onChangeView(id)}
            className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs ${
              view === id ? "bg-lab-accent/10 text-lab-accent" : "text-slate-400 hover:bg-white/5"
            }`}
          >
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>
    </aside>
  );
}
