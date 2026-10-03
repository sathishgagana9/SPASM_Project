import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Sidebar, type View } from "./components/Sidebar";
import { ChatPage } from "./pages/ChatPage";
import { Research } from "./pages/Research";
import { Settings } from "./pages/Settings";
import { Overview } from "./pages/Overview";
import { Dashboard } from "./pages/Dashboard";
import { Personas } from "./pages/Personas";
import { api } from "./services/api";
import type { Persona } from "./types";

function useLocalStorage<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = localStorage.getItem(key);
      return raw !== null ? (JSON.parse(raw) as T) : initial;
    } catch {
      return initial;
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // storage unavailable — silently ignore, settings just won't persist
    }
  }, [key, value]);
  return [value, setValue] as const;
}

export default function App() {
  const queryClient = useQueryClient();
  const [view, setView] = useState<View>("chat");
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [focusPersonaId, setFocusPersonaId] = useState<string | null>(null);

  const [theme, setTheme] = useLocalStorage<"dark" | "light">("spasm-theme", "dark");
  const [monitoringEnabled, setMonitoringEnabled] = useLocalStorage<boolean>("spasm-monitoring-enabled", true);
  const [defaultPersonaId, setDefaultPersonaId] = useLocalStorage<string | null>("spasm-default-persona", null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.classList.toggle("light", theme === "light");
  }, [theme]);

  const conversations = useQuery({ queryKey: ["conversations"], queryFn: api.listConversations });
  const personas = useQuery({ queryKey: ["personas"], queryFn: api.listPersonas });

  const renameConversation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => api.renameConversation(id, title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["conversations"] }),
  });
  const deleteConversation = useMutation({
    mutationFn: (id: string) => api.deleteConversation(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      if (activeConversationId === id) setActiveConversationId(null);
    },
  });

  const openPersonaSettings = (p: Persona) => {
    setFocusPersonaId(p.id);
    setView("studio");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-lab-bg">
      {/* Very subtle global depth: a soft radial cyan glow + faint grid, well
          below the sidebar's own glow in opacity so it reads as ambient
          depth rather than a visual effect competing for attention. */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.06]"
        style={{
          backgroundImage:
            "linear-gradient(#22d3ee 1px, transparent 1px), linear-gradient(90deg, #22d3ee 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />
      <div
        className="pointer-events-none fixed left-0 top-0 z-0 h-[600px] w-[600px] rounded-full opacity-[0.08] blur-3xl"
        style={{ background: "radial-gradient(circle, #22d3ee 0%, transparent 70%)" }}
      />

      <Sidebar
        view={view}
        onChangeView={setView}
        conversations={conversations.data ?? []}
        personas={personas.data ?? []}
        activeConversationId={activeConversationId}
        defaultPersonaId={defaultPersonaId}
        onSelectConversation={setActiveConversationId}
        onNewChat={() => { setActiveConversationId(null); setView("chat"); }}
        onRenameConversation={(id, title) => renameConversation.mutate({ id, title })}
        onDeleteConversation={(id) => deleteConversation.mutate(id)}
        onSelectPersonaForNewChat={(personaId) => {
          // Reuses the existing default-persona mechanism (Settings' own
          // defaultPersonaId) rather than a second, parallel selection
          // system — picking a persona here pre-fills the SAME PersonaPicker
          // that Settings' "default persona" already feeds, then takes the
          // user straight to a fresh chat with it pre-selected.
          setDefaultPersonaId(personaId);
          setActiveConversationId(null);
          setView("chat");
        }}
      />

      <main className="relative z-10 flex flex-1 overflow-hidden">
        {view === "chat" && (
          <ChatPage
            conversationId={activeConversationId}
            defaultPersonaId={defaultPersonaId}
            monitoringEnabled={monitoringEnabled}
            onConversationCreated={setActiveConversationId}
          />
        )}
        {view === "research" && <div className="flex-1 overflow-y-auto"><Research /></div>}
        {view === "settings" && (
          <div className="flex-1 overflow-y-auto">
            <Settings
              theme={theme}
              onThemeChange={setTheme}
              monitoringEnabled={monitoringEnabled}
              onMonitoringChange={setMonitoringEnabled}
              defaultPersonaId={defaultPersonaId}
              onDefaultPersonaChange={setDefaultPersonaId}
            />
          </div>
        )}
        {view === "system" && <div className="flex-1 overflow-y-auto"><Overview /></div>}
        {view === "manager" && <div className="flex-1 overflow-y-auto p-8"><Dashboard onOpenSettings={openPersonaSettings} /></div>}
        {view === "studio" && <div className="flex-1 overflow-y-auto p-8"><Personas focusPersonaId={focusPersonaId} /></div>}
      </main>
    </div>
  );
}
