/**
 * Brand identity for the project — renamed from "Anchora" to "RAISE".
 *
 * ## Naming
 *
 * Short wordmark: "RAISE". Full name: "Role Alignment & Integrity
 * Stability Engine". Tagline: "Consistency in Every Interaction".
 *
 * ## Logo asset — a real designed image, not a hand-coded SVG
 *
 * Earlier versions of this brand identity used a hand-authored inline
 * SVG (`LogoMarkFallback` below) as a rough geometric approximation of
 * the intended concept, explicitly flagged as visually unverified.
 *
 * The actual logo is now a designed raster image
 * (`/logo-icon.png` — square icon mark, transparent background,
 * cropped from the full designed lockup; `/logo-raise.png` — the full
 * horizontal lockup with wordmark and tagline baked in, for contexts
 * like a large About-page hero where the complete designed composition
 * should be shown as-is). Favicons at 16/32/48/64/192px were generated
 * from the same source (`/favicon-*.png`, `/favicon.ico`).
 *
 * Concept (for anyone asked to describe the mark): an infinity/möbius
 * loop combining a human-profile silhouette with circuit-board tracery
 * (AI/monitoring), wrapped around a checkmark-and-target motif
 * (alignment verification) sitting on an upward trend arrow
 * (stability/improvement over time) — chosen to read as "AI
 * continuously verifying and correcting alignment," not a generic
 * chatbot/robot icon.
 */
export const PROJECT_NAME = "RAISE";
export const PROJECT_FULL_NAME = "Role Alignment & Integrity Stability Engine";
export const PROJECT_TAGLINE = "Consistency in Every Interaction";
export const PROJECT_FORMER_NAMES = ["Anchora", "SPASM++"]; // kept for institutional memory / anyone searching old references

/** Square icon mark only (no wordmark) — sidebar, avatars, anywhere compact. */
export function LogoIcon({ size = 24, className = "" }: { size?: number; className?: string }) {
  return (
    <img
      src="/logo-icon.png"
      width={size}
      height={size}
      alt="RAISE logo"
      className={className}
      style={{ objectFit: "contain" }}
    />
  );
}

/** The full designed horizontal lockup (icon + wordmark + tagline baked into
 * the image) — use for a large, prominent placement (About page hero) where
 * showing the complete composition as originally designed matters more than
 * layout flexibility. Do NOT use this at small sizes — the baked-in text
 * becomes illegible; use `Wordmark` (icon + live HTML text) instead. */
export function FullLockupImage({ maxWidth = 480, className = "" }: { maxWidth?: number; className?: string }) {
  return (
    <img
      src="/logo-raise.png"
      alt={`${PROJECT_NAME} — ${PROJECT_FULL_NAME}`}
      style={{ maxWidth, width: "100%", height: "auto" }}
      className={className}
    />
  );
}

/** Hand-coded SVG fallback — kept only for contexts where an <img> can't be
 * used (e.g. inlining into a non-web export). Prefer LogoIcon everywhere
 * else; this is a rough geometric approximation, not the designed mark. */
export function LogoMarkFallback({ size = 24, className = "" }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} role="img" aria-label="RAISE logo (fallback)">
      <circle cx="24" cy="24" r="17" stroke="#334155" strokeWidth="1.75" strokeDasharray="3.5 3.5" fill="none" />
      <path d="M 40 11 C 33 9, 24 12, 20 19 C 17.5 23.5, 19 27.5, 24 26.5" stroke="#22d3ee" strokeWidth="2.25" strokeLinecap="round" fill="none" />
      <path d="M 24 26.5 L 20.7 24.3 M 24 26.5 L 22.6 30.2" stroke="#22d3ee" strokeWidth="2.25" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      <circle cx="24" cy="24" r="6" fill="#22d3ee" />
      <circle cx="24" cy="24" r="6" fill="none" stroke="#0a0e14" strokeWidth="1" />
    </svg>
  );
}

export function Wordmark({
  showFullName = false, size = "md",
}: { showFullName?: boolean; size?: "sm" | "md" | "lg" }) {
  const markSize = { sm: 18, md: 22, lg: 32 }[size];
  const nameClass = { sm: "text-xs", md: "text-sm", lg: "text-xl" }[size];
  return (
    <div className="flex items-center gap-2">
      <LogoIcon size={markSize} />
      <div>
        <div className={`mono font-semibold tracking-wide text-lab-accent ${nameClass}`}>{PROJECT_NAME}</div>
        {showFullName && (
          <div className="text-[10px] leading-tight text-slate-500">{PROJECT_FULL_NAME}</div>
        )}
      </div>
    </div>
  );
}
