import { AlertTriangle, RefreshCw, Activity } from "lucide-react";
import type { ApiErrorBody } from "../types";

const COPY: Record<ApiErrorBody["error_type"], { title: string; reason: string }> = {
  timeout: {
    title: "Unable to generate a response",
    reason: "The model took too long to respond. It may still be loading — try again in a moment.",
  },
  unreachable: {
    title: "AI provider unavailable",
    reason: "Couldn't reach Groq. Check your internet connection and GROQ_API_KEY in backend/.env.",
  },
  auth: {
    title: "AI provider rejected the request",
    reason: "The configured API key was rejected. Check GROQ_API_KEY in your backend .env.",
  },
  rate_limit: {
    title: "AI provider rate limit hit",
    reason: "Too many requests right now. Wait a moment and try again.",
  },
  malformed: {
    title: "Unexpected response from the provider",
    reason: "The provider returned something the app couldn't understand. Try again, or try a different model.",
  },
  unknown: {
    title: "Unable to generate a response",
    reason: "Something went wrong. Try again, or check System Status.",
  },
};

export function ErrorNotice({
  errorType,
  onRetry,
  onCheckStatus,
}: {
  errorType: ApiErrorBody["error_type"];
  onRetry?: () => void;
  onCheckStatus?: () => void;
}) {
  const { title, reason } = COPY[errorType] ?? COPY.unknown;
  return (
    <div className="rounded-xl border border-lab-danger/30 bg-lab-danger/5 p-4">
      <div className="mb-1 flex items-center gap-2 text-sm font-medium text-lab-danger">
        <AlertTriangle size={16} />
        {title}
      </div>
      <p className="mb-3 text-sm text-slate-400">{reason}</p>
      <div className="flex gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-1 rounded-lg border border-lab-border px-3 py-1.5 text-xs text-slate-300 hover:border-lab-accent hover:text-lab-accent"
          >
            <RefreshCw size={12} /> Retry
          </button>
        )}
        {onCheckStatus && (
          <button
            onClick={onCheckStatus}
            className="flex items-center gap-1 rounded-lg border border-lab-border px-3 py-1.5 text-xs text-slate-300 hover:border-lab-accent hover:text-lab-accent"
          >
            <Activity size={12} /> Check System Status
          </button>
        )}
      </div>
    </div>
  );
}
