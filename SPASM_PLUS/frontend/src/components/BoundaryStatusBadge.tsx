import { Check, ShieldAlert, ShieldCheck, ShieldX, XCircle } from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * Spec Part 26: "use meaningful status indicators... use a professional
 * visual system... do not overuse colors." One shared component so this
 * vocabulary is rendered identically everywhere it appears (chat bubbles,
 * the analysis pane's pipeline, turn history) instead of each call site
 * inventing its own colors/wording.
 *
 * Deliberately a SMALL, closed set of statuses — exactly the ones spec
 * Part 26 names — rather than a generic "any string, any color" badge,
 * so the visual language stays consistent instead of accumulating ad hoc
 * one-off variants over time.
 */
export type BoundaryStatus =
  | "in_scope"
  | "out_of_scope"
  | "drift_attempt"
  | "drift_prevented"
  | "drift_detected"
  | "correction_successful"
  | "correction_failed";

const META: Record<BoundaryStatus, { label: string; icon: LucideIcon; classes: string }> = {
  in_scope: { label: "In Scope", icon: Check, classes: "bg-slate-700/30 text-slate-300 border-slate-600/40" },
  out_of_scope: { label: "Out of Scope", icon: XCircle, classes: "bg-lab-warn/10 text-lab-warn border-lab-warn/30" },
  drift_attempt: { label: "Drift Attempt", icon: ShieldAlert, classes: "bg-purple-500/10 text-purple-400 border-purple-500/30" },
  drift_prevented: { label: "Drift Prevented", icon: ShieldCheck, classes: "bg-lab-ok/10 text-lab-ok border-lab-ok/30" },
  drift_detected: { label: "Drift Detected", icon: ShieldX, classes: "bg-lab-danger/10 text-lab-danger border-lab-danger/30" },
  correction_successful: { label: "Correction Successful", icon: ShieldCheck, classes: "bg-lab-ok/10 text-lab-ok border-lab-ok/30" },
  correction_failed: { label: "Correction Failed", icon: ShieldX, classes: "bg-lab-danger/10 text-lab-danger border-lab-danger/30" },
};

export function BoundaryStatusBadge({ status, size = "sm" }: { status: BoundaryStatus; size?: "sm" | "xs" }) {
  const { label, icon: Icon, classes } = META[status];
  const sizeClasses = size === "xs" ? "px-1.5 py-0.5 text-[10px] gap-1" : "px-2 py-1 text-xs gap-1.5";
  return (
    <span className={`mono inline-flex items-center rounded-md border ${sizeClasses} ${classes}`}>
      <Icon size={size === "xs" ? 10 : 12} />
      {label}
    </span>
  );
}
