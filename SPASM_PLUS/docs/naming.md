# Naming: the "SPASM" collision, and what to do about it

**Second update: the project has been renamed again**, from Anchora
to **RAISE** (Role Alignment & Integrity Stability Engine, tagline
"Consistency in Every Interaction"). This was a deliberate brand
redesign (a professionally designed logo image replaced the earlier
hand-coded SVG approximation — see `frontend/src/components/Logo.tsx`),
not a reaction to a new naming collision. The "Anchora" section below
is kept for the historical record of the FIRST rename (from SPASM++)
and its reasoning; skip to "What's done" for current status.

## Why Anchora (superseded — kept for history)

Picked for continuity with vocabulary ALREADY inside this codebase
rather than an arbitrary new word: the repair engine's most
aggressive operator is literally named `strong_reanchor_regenerate`
(`backend/app/repair/engine.py`) — "anchoring" a drifted response
back to the persona was already this project's own internal metaphor
for correction, before any renaming was considered. Anchora made
that existing metaphor the brand, rather than introducing a second,
disconnected one.

**Why RAISE replaced it**: this was a design-driven decision (a
commissioned/generated logo composition already existed under the
RAISE name) rather than a conceptual objection to Anchora — the
"anchor" metaphor is still accurate to how the repair engine works,
it just isn't the branding anymore. If the mark or name changes
again, update this section rather than deleting the history — it's
useful for anyone who finds old references to either prior name.

## What's done

- **RAISE rebrand (second rename)**: a real designed logo image
  (`frontend/public/logo-raise.png` — full lockup; `logo-icon.png` —
  cropped square mark; `favicon-*.png`/`favicon.ico` — generated from
  the same source) replaced the earlier hand-coded SVG approximation.
  `frontend/src/components/Logo.tsx` now serves the image asset
  (`LogoIcon`, `FullLockupImage`, `Wordmark`) with the old SVG kept
  only as `LogoMarkFallback` for contexts that can't use an `<img>`.
  Updated everywhere the Anchora wordmark appeared: `Sidebar.tsx`,
  `index.html` (title + favicon links), Settings "About" section (now
  shows the full designed lockup image), `DriftAlert.tsx`, `api.ts`
  comment, `README.md`'s title, and the three version-string constants
  (`DETECTOR_VERSION`, `POLICY_VERSION`, `FUSION_VERSION` — again safe
  to bump, still no real experiment data logged under any prior name).
- **First rename (SPASM++ → Anchora)**: frontend wordmark/title/About
  section, `DriftAlert.tsx`, `api.ts` comment, `README.md` title
  header — all since superseded by the RAISE rebrand above, but this
  is what established the pattern of keeping former names listed in
  the About section (`PROJECT_FORMER_NAMES`, now `["Anchora",
  "SPASM++"]`) rather than erasing history.

## What's still open (the original checklist, still accurate)

The deeper mechanical rename below was NOT done — it's lower-visibility
than what's listed above (nobody using the app sees these), and
riskier to do quickly (touches the DB filename and would require
another `rm spasm.db`, which nobody should do without noticing):

## Rename checklist (name is decided: RAISE — the placeholders below just need substituting)

Do this as ONE deliberate pass, not scattered edits, so you can
verify it in one test run:

1. `grep -ril "spasm" --include="*.py" --include="*.md" --include="*.ts" --include="*.tsx" --include="*.yml" --include="*.yaml" .` (excluding `node_modules`) to get the remaining file list.
2. Case-sensitive replace `SPASM++` → `RAISE`, `SPASM-DriftBench` → `RAISE-DriftBench`, `spasm` (lowercase, e.g. `spasm.db`, env var prefixes if any) → `raise` — do these as separate passes since case matters for filenames/identifiers. Watch for `raise` colliding with the Python keyword when grepping/renaming identifiers (not a problem for the DB filename or prose, but worth a second look before any code-identifier rename beyond the version strings already done).
3. Rename `backend/spasm.db` → `backend/raise.db` and update `database_url` default in `backend/app/core/config.py`. **Not done yet** — do this deliberately, since it requires deleting the dev DB file again.
4. ~~Update `DETECTOR_VERSION`, `POLICY_VERSION` (policy.py), `FUSION_VERSION` (fusion.py)~~ — **done**, see "What's done" above. `THRESHOLD_VERSION` (scoring.py) was not part of that pass — check whether it still says `spasm-*`/`manual-v1` and bump it too for consistency.
5. `docker-compose.yml` service names, if you want them to match (optional — internal service names don't leak to a paper, lower priority than the rest).
6. Re-run the full test suite (`pytest backend/tests/`) and `research/tests/` after the rename — a rename that silently breaks an import is worse than not renaming yet.
7. Update RESEARCH.md, BENCHMARK.md, EXPERIMENTS.md, METHODOLOGY.md, REPRODUCIBILITY.md, RESEARCH_CONTRIBUTION.md headers and any prose that says "SPASM++", "Anchora", or "SPASM-DriftBench" — README's title is done, these longer research docs are not.

## What NOT to do

Don't rename incrementally across multiple commits while running
experiments in between — half-renamed state makes `research/results/`
provenance genuinely confusing (which `DETECTOR_VERSION` string maps
to which name?). Do the rename before you start the real experiment
runs that will produce your paper's numbers, not after.
