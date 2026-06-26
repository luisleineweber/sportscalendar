# Lessons Learned

## 2026-03-08 - Legacy empty selections need an explicit migration path

- What went wrong (pattern):
  - Resetting storage keys alone did not guarantee that event selection would boot back to the intended default.
  - A persisted empty `selectedEventIds` array can look identical whether it came from a stale experiment or from an explicit user choice.
- The fix:
  - Added a restore helper that treats empty selections without an initialization marker as legacy/uninitialized state.
  - Started persisting an explicit `selectionInitialized` marker so future intentional empty selections remain valid.
- Prevention rule:
  - When persisted empty collections can mean both "not initialized yet" and "user intentionally chose none", store an explicit marker that disambiguates those cases.
  - Add a regression test for both the legacy-empty and explicit-empty restore paths.

## 2026-03-08 - Persisted web state must be versioned when UI experiments change defaults

- What went wrong (pattern):
  - Browser storage from earlier UI experiments kept overriding the intended default boot state.
  - This made the app look broken on revisit, with all sports active but zero selected events.
- The fix:
  - Bumped the persisted storage keys for the web app.
  - Reset visible UI copy to the current English baseline so stale state no longer reinforced the experimental branch behavior.
- Prevention rule:
  - Whenever client-side defaults or major UI experiments change persisted state semantics, bump the storage key version.
  - Treat browser persistence as part of the release surface, not just a local convenience.

## 2026-03-08 - Wikipedia table fetches need an explicit user agent and HTML-first parsing

- What went wrong (pattern):
  - The initial assumption was that `pandas.read_html(url)` would work directly against Wikipedia pages.
  - Wikipedia returned HTTP 403 for direct `read_html(url)` requests in this environment.
  - Pulling all page tables at once also made it hard to align table data with surrounding month headings.
- The fix:
  - Fetched page HTML explicitly with `urllib.request` and a user agent.
  - Parsed per-table HTML snippets instead of bulk-reading the whole page.
  - Used DOM context to keep heading/month metadata available for downstream normalization.
- Prevention rule:
  - For third-party HTML sources, do not assume `read_html(url)` is production-safe; fetch HTML explicitly first.
  - When table context matters, parse individual table nodes so surrounding headings remain available.

## 2026-03-07 - Sport filter updates should not overwrite finer-grained event intent

- What went wrong (pattern):
  - Sport-level selection changes rebuilt `selectedEventIds` from scratch.
  - This erased manual event deselections and made broad filters override more specific user choices.
- The fix:
  - Split sport-selection state transition into a pure helper that preserves valid event ids.
  - Stopped sport toggles from re-selecting all events in active sports.
  - Added an executable regression test for toggling sports off/on after manual event deselection.
- Prevention rule:
  - When multiple selection layers exist, coarse filters must not silently overwrite finer-grained selections unless explicitly requested.
  - Add a regression test whenever state reconciliation changes selected-id sets.

## 2026-03-03 - Sport group collapse toggle ignored SVG taps

- What went wrong (pattern):
  - Delegated click handling in `#sports` accepted only `HTMLElement` targets.
  - Taps on inline SVG/path inside the collapse button can produce `SVGElement` targets, so the handler returned early.
- The fix:
  - Switched target guard from `HTMLElement` to `Element` in delegated click handling.
  - Added `pointer-events: none` on `.sport-group-toggle-icon` so taps resolve to the button reliably.
- Prevention rule:
  - For delegated click handlers that use `closest(...)`, guard with `Element`, not `HTMLElement`.
  - For icon-only controls, disable pointer events on decorative SVG icons by default.

## 2026-02-27 - Collapsible sports categories first implementation was not robust enough

- What went wrong (pattern):
  - Collapse interaction was attached mainly to a small text button, and visibility relied on `hidden` only.
  - This made the UX unclear and increased risk that user taps did not hit the expected target.
- The fix:
  - Made the whole category heading area toggle collapse/expand.
  - Switched to an icon-only chevron control with clear visual direction.
  - Added explicit CSS hiding for collapsed grids (`.is-collapsed .sport-group-grid { display: none; }`).
- Prevention rule:
  - For mobile-first interactions, never rely on tiny hit targets for primary actions.
  - Add explicit CSS state rules (not only HTML attributes) for visibility-critical UI behavior.
