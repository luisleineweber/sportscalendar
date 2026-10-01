import {
  applySportSelectionChange,
  createCatalogSessionStateKey,
  createCatalogStateKey,
  createCatalogStatePayload,
  filterEventsForExport,
  getDefaultSelectedEventIds,
  getLocalIsoDate,
  getSelectionState,
  isFromTodayExportAvailable,
  isEventVisibleForSelectedCountries,
  normalizeSelectedEventIds,
  parseStoredState,
  restoreCatalogSelection,
  safeStorageRead,
  safeStorageRemove,
  safeStorageWrite,
  updateSelectedEventIds,
} from "./app-state.mjs?v=20260928a";
import {
  buildCatalogTaxonomy,
  loadCatalog,
  loadCatalogManifest,
  getAudienceScopeLabel,
} from "./catalog.mjs?v=20261001a";
import { buildEventSummary, createIcs } from "./ics.mjs";

const EXPORT_FILE_NAME = "sportkalender-selection.ics";
const EXPORT_RANGE_FULL_YEAR = "full_year";
const EXPORT_RANGE_FROM_TODAY = "from_today";
const IDLE_EXPORT_STATUS_TEXT = "No export yet.";
const MAX_PERSISTED_STATE_BYTES = 200 * 1024;
const COUNTRY_FILTERS = [
  { key: "DE", label: "Germany" },
  { key: "US", label: "United States" },
  { key: "GB", label: "United Kingdom" },
  { key: "FR", label: "France" },
  { key: "IT", label: "Italy" },
];

const elements = {
  eventsPanel: document.querySelector("#events-panel"),
  exportDock: document.querySelector(".export-dock"),
  catalogYear: document.querySelector("#catalog-year"),
  catalogStatus: document.querySelector("#catalog-status"),
  countryFilters: document.querySelector("#country-filters"),
  countriesMeta: document.querySelector("#countries-meta"),
  countriesAll: document.querySelector("#countries-all"),
  countriesNone: document.querySelector("#countries-none"),
  sports: document.querySelector("#sports"),
  sportsMeta: document.querySelector("#sports-meta"),
  events: document.querySelector("#events"),
  statsText: document.querySelector("#stats-text"),
  eventSearch: document.querySelector("#event-search"),
  collapseEventSearch: document.querySelector("#collapse-event-search"),
  expandEventSearch: document.querySelector("#expand-event-search"),
  exportStatus: document.querySelector("#export-status"),
  exportEventsCount: document.querySelector("#export-events-count"),
  exportSportsCount: document.querySelector("#export-sports-count"),
  exportRange: document.querySelector("#export-range"),
  query: document.querySelector("#query"),
  titleFormat: document.querySelector("#title-format"),
  calendarName: document.querySelector("#calendar-name"),
  sportsAll: document.querySelector("#sports-all"),
  sportsNone: document.querySelector("#sports-none"),
  selectVisible: document.querySelector("#select-visible"),
  clearVisible: document.querySelector("#clear-visible"),
  invertVisible: document.querySelector("#invert-visible"),
  selectedOnlyToggle: document.querySelector("#selected-only-toggle"),
  exportButton: document.querySelector("#export"),
};

const state = {
  manifest: null,
  catalog: null,
  catalogId: null,
  requestToken: 0,
  events: [],
  visibleEvents: [],
  taxonomy: { sports: [], groups: [], competitions: [] },
  selectedSports: new Set(),
  selectedCountries: new Set(),
  selectedEventIds: new Set(),
  collapsedSportCategories: new Set(),
  query: "",
  titleFormat: "sport_event",
  showSelectedOnly: false,
  exportRange: EXPORT_RANGE_FULL_YEAR,
};

boot().catch((error) => {
  console.error(error);
  showCatalogError(error);
});

async function boot() {
  bindEvents();
  state.manifest = await loadCatalogManifest();
  populateCatalogYearOptions();
  setEventSearchCollapsed(false, { moveFocus: false });
  await switchCatalog(state.manifest.default, { initial: true });
  setExportStatus(IDLE_EXPORT_STATUS_TEXT);
}

function bindEvents() {
  elements.catalogYear?.addEventListener("change", (event) => {
    void switchCatalog(event.target.value);
  });

  elements.countryFilters.addEventListener("change", (event) => {
    if (!(event.target instanceof HTMLInputElement) || !event.target.dataset.country) {
      return;
    }
    if (event.target.checked) {
      state.selectedCountries.add(event.target.dataset.country);
    } else {
      state.selectedCountries.delete(event.target.dataset.country);
    }
    renderCountriesMeta();
    applyFilters();
    persistState();
  });

  elements.countriesAll.addEventListener("click", () => {
    state.selectedCountries = new Set(COUNTRY_FILTERS.map((country) => country.key));
    renderCountryFilters();
    applyFilters();
    persistState();
  });

  elements.countriesNone.addEventListener("click", () => {
    state.selectedCountries.clear();
    renderCountryFilters();
    applyFilters();
    persistState();
  });

  elements.query.addEventListener("input", (event) => {
    state.query = event.target.value;
    applyFilters();
    persistState();
  });

  elements.collapseEventSearch.addEventListener("click", () => {
    setEventSearchCollapsed(true);
  });

  elements.expandEventSearch.addEventListener("click", () => {
    setEventSearchCollapsed(false);
  });

  elements.titleFormat.addEventListener("change", (event) => {
    state.titleFormat = event.target.value;
    renderEvents();
    renderStats();
    persistState();
  });

  elements.exportRange.addEventListener("change", (event) => {
    state.exportRange = event.target.value === EXPORT_RANGE_FROM_TODAY
      ? EXPORT_RANGE_FROM_TODAY
      : EXPORT_RANGE_FULL_YEAR;
    renderStats();
    persistState();
  });

  elements.calendarName.addEventListener("input", persistState);

  elements.sportsAll.addEventListener("click", () => {
    applySportSelectionUpdate((nextSelectedSports) => {
      nextSelectedSports.clear();
      for (const sport of state.taxonomy.sports) {
        nextSelectedSports.add(sport.key);
      }
    });
  });

  elements.sportsNone.addEventListener("click", () => {
    applySportSelectionUpdate((nextSelectedSports) => nextSelectedSports.clear());
  });

  elements.sports.addEventListener("change", (event) => {
    if (!(event.target instanceof HTMLInputElement)) {
      return;
    }

    if (event.target.dataset.sport) {
      applySportSelectionUpdate((nextSelectedSports) => {
        if (event.target.checked) {
          nextSelectedSports.add(event.target.dataset.sport);
        } else {
          nextSelectedSports.delete(event.target.dataset.sport);
        }
      }, getSportsFocusTargetFromElement(event.target));
      return;
    }

  });

  elements.sports.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) {
      return;
    }

    const sportToggle = event.target.closest("button[data-group-toggle='collapse']");
    if (sportToggle instanceof HTMLButtonElement) {
      toggleSportCategory(sportToggle.dataset.groupName);
      return;
    }

    const sportAction = event.target.closest("button[data-group-action]");
    if (sportAction instanceof HTMLButtonElement) {
      const category = sportAction.dataset.groupName;
      const sports = getSportsForCategory(category);
      applySportSelectionUpdate((nextSelectedSports) => {
        for (const sport of sports) {
          if (sportAction.dataset.groupAction === "all") {
            nextSelectedSports.add(sport.key);
          } else {
            nextSelectedSports.delete(sport.key);
          }
        }
      }, getSportsFocusTargetFromElement(sportAction));
      return;
    }

  });

  elements.events.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) {
      return;
    }
    const actionButton = event.target.closest("button[data-event-sport-action]");
    if (!(actionButton instanceof HTMLButtonElement)) {
      return;
    }

    const { eventSportKey, eventSportAction } = actionButton.dataset;
    const eventIds = state.visibleEvents
      .filter((catalogEvent) => catalogEvent.sportKey === eventSportKey)
      .map((catalogEvent) => catalogEvent.id);
    state.selectedEventIds = updateSelectedEventIds(
      state.selectedEventIds,
      eventIds,
      eventSportAction === "select",
    );
    renderEvents();
    renderStats();
    persistState();
    const nextAction = elements.events.querySelector(
      `button[data-event-sport-key="${CSS.escape(eventSportKey)}"][data-event-sport-action="${CSS.escape(eventSportAction)}"]`,
    );
    (nextAction instanceof HTMLElement ? nextAction : elements.selectVisible).focus();
  });

  elements.events.addEventListener("change", (event) => {
    if (!(event.target instanceof HTMLInputElement) || !event.target.dataset.eventId) {
      return;
    }
    state.selectedEventIds = updateSelectedEventIds(
      state.selectedEventIds,
      [event.target.dataset.eventId],
      event.target.checked,
    );
    renderStats();
    persistState();
  });

  elements.selectVisible.addEventListener("click", () => {
    state.selectedEventIds = updateSelectedEventIds(
      state.selectedEventIds,
      state.visibleEvents.map((event) => event.id),
      true,
    );
    renderEvents();
    renderStats();
    persistState();
  });

  elements.clearVisible.addEventListener("click", () => {
    state.selectedEventIds = updateSelectedEventIds(
      state.selectedEventIds,
      state.visibleEvents.map((event) => event.id),
      false,
    );
    renderEvents();
    renderStats();
    persistState();
  });

  elements.invertVisible.addEventListener("click", () => {
    const nextSelectedEventIds = new Set(state.selectedEventIds);
    for (const event of state.visibleEvents) {
      if (nextSelectedEventIds.has(event.id)) {
        nextSelectedEventIds.delete(event.id);
      } else {
        nextSelectedEventIds.add(event.id);
      }
    }
    state.selectedEventIds = nextSelectedEventIds;
    renderEvents();
    renderStats();
    persistState();
  });

  elements.selectedOnlyToggle.addEventListener("click", () => {
    state.showSelectedOnly = !state.showSelectedOnly;
    applyFilters();
    persistState();
  });

  elements.exportButton.addEventListener("click", () => {
    void exportIcs();
  });
}

async function switchCatalog(catalogId, { initial = false } = {}) {
  const requestToken = ++state.requestToken;
  if (!initial) {
    elements.catalogStatus.textContent = `Loading catalog ${catalogId}...`;
  }

  try {
    const catalog = await loadCatalog({ manifest: state.manifest, catalogId });
    if (requestToken !== state.requestToken) {
      return;
    }
    applyCatalog(catalog);
  } catch (error) {
    if (requestToken !== state.requestToken) {
      return;
    }
    console.error(error);
    if (state.catalogId) {
      elements.catalogYear.value = state.catalogId;
      elements.catalogStatus.textContent = error instanceof Error ? error.message : String(error);
    } else {
      showCatalogError(error);
    }
  }
}

function applyCatalog(catalog) {
  const storedState = readStoredState(catalog.id);
  state.catalog = catalog;
  state.catalogId = catalog.id;
  state.events = catalog.events;
  state.taxonomy = catalog.taxonomy ?? buildCatalogTaxonomy(catalog.events, state.manifest);
  state.selectedSports = new Set(state.taxonomy.sports.map((sport) => sport.key));
  state.selectedCountries = new Set(COUNTRY_FILTERS.map((country) => country.key));
  state.selectedEventIds = getDefaultSelectedEventIds(state.events);
  state.collapsedSportCategories = getDefaultCollapsedSportCategories();
  hydrateStateFromStorage(storedState);
  elements.catalogYear.value = catalog.id;
  elements.catalogStatus.textContent = formatCatalogStatus(catalog);
  renderCountryFilters();
  renderSports();
  applyFilters();
  persistState();
}

function populateCatalogYearOptions() {
  elements.catalogYear.replaceChildren();
  const entries = [...state.manifest.catalogs].sort((left, right) => Number(left.year) - Number(right.year));
  for (const entry of entries) {
    const option = document.createElement("option");
    option.value = entry.id;
    option.textContent = String(entry.year ?? entry.id);
    elements.catalogYear.append(option);
  }
}

function formatCatalogStatus(catalog) {
  const rejected = catalog.diagnostics?.rejectedCount ?? 0;
  return rejected > 0
    ? `${catalog.status ?? "preview"} · ${rejected} rows rejected for review`
    : `${catalog.events.length} entries available`;
}

function renderCountryFilters() {
  elements.countryFilters.replaceChildren();
  for (const country of COUNTRY_FILTERS) {
    const label = document.createElement("label");
    label.className = "country-filter-option";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = state.selectedCountries.has(country.key);
    checkbox.dataset.country = country.key;
    const text = document.createElement("span");
    text.textContent = country.label;
    label.append(checkbox, text);
    elements.countryFilters.append(label);
  }
  renderCountriesMeta();
}

function renderCountriesMeta() {
  const selectedCount = state.selectedCountries.size;
  const selectionSummary = selectedCount === COUNTRY_FILTERS.length
    ? "All five countries active"
    : `${selectedCount} of ${COUNTRY_FILTERS.length} countries active`;
  elements.countriesMeta.textContent = `${selectionSummary} · Only national events are filtered; international events always show`;
}

function applyFilters() {
  const query = state.query.trim().toLocaleLowerCase();
  state.visibleEvents = state.events
    .filter(isEventEligibleForCurrentFilters)
    .filter((event) => !state.showSelectedOnly || state.selectedEventIds.has(event.id))
    .filter((event) => {
      if (!query) {
        return true;
      }
      const text = [
        event.title,
        event.sportLabel,
        event.location,
        event.competitionLabel,
        event.season,
        event.audienceCountries.join(" "),
      ].join(" ").toLocaleLowerCase();
      return text.includes(query);
    })
    .sort(compareVisibleEvents);

  renderEvents();
  renderStats();
}

function isEventEligibleForCurrentFilters(event) {
  return state.selectedSports.has(event.sportKey)
    && isEventVisibleForSelectedCountries(event, state.selectedCountries);
}

function renderSports() {
  elements.sports.replaceChildren();
  const fragment = document.createDocumentFragment();
  for (const group of getSportGroups()) {
    const isCollapsed = state.collapsedSportCategories.has(group.category);
    const section = document.createElement("section");
    section.className = "sport-group";
    section.classList.toggle("is-collapsed", isCollapsed);

    const header = document.createElement("header");
    header.className = "sport-group-header";
    const heading = document.createElement("button");
    heading.type = "button";
    heading.className = "sport-group-heading";
    heading.dataset.groupToggle = "collapse";
    heading.dataset.groupName = group.category;
    heading.setAttribute("aria-expanded", String(!isCollapsed));
    heading.setAttribute("aria-label", isCollapsed ? `Expand ${group.category}` : `Collapse ${group.category}`);
    const title = document.createElement("h3");
    title.className = "sport-group-title";
    title.textContent = group.category;
    const headingMeta = document.createElement("span");
    headingMeta.className = "sport-group-heading-meta";
    const count = document.createElement("span");
    count.className = "sport-group-count";
    count.textContent = `${group.sports.filter((sport) => state.selectedSports.has(sport.key)).length}/${group.sports.length}`;
    const toggleIcon = document.createElement("span");
    toggleIcon.className = "sport-group-toggle";
    toggleIcon.innerHTML = '<svg class="sport-group-toggle-icon" aria-hidden="true" viewBox="0 0 20 20"><path d="M5.5 7.5 10 12l4.5-4.5" fill="none" stroke="currentColor" stroke-width="2"/></svg>';
    headingMeta.append(count, toggleIcon);
    heading.append(title, headingMeta);

    const actions = document.createElement("div");
    actions.className = "sport-group-actions";
    actions.append(
      createSportActionButton(group.category, "all", "All"),
      createSportActionButton(group.category, "none", "None"),
    );
    const meta = document.createElement("div");
    meta.className = "sport-group-meta";
    meta.append(actions);
    header.append(heading, meta);

    const grid = document.createElement("div");
    grid.className = "sport-group-grid";
    for (const sport of group.sports) {
      grid.append(renderSportEntry(sport));
    }
    section.append(header, grid);
    fragment.append(section);
  }
  elements.sports.append(fragment);
  elements.sportsMeta.textContent = `${state.selectedSports.size}/${state.taxonomy.sports.length} sports active`;
}

function renderSportEntry(sport) {
  const entry = document.createElement("div");
  entry.className = "sport-entry";
  const label = document.createElement("label");
  label.className = "sport-item";
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = state.selectedSports.has(sport.key);
  checkbox.dataset.sport = sport.key;
  const text = document.createElement("span");
  text.textContent = sport.label;
  label.append(checkbox, text);
  entry.append(label);
  return entry;
}

function renderEvents() {
  elements.events.replaceChildren();
  if (state.visibleEvents.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = state.showSelectedOnly
      ? "No selected events match the current filter."
      : "No events match the current filter.";
    elements.events.append(empty);
    return;
  }

  const fragment = document.createDocumentFragment();
  const eventGroups = new Map();
  for (const event of state.visibleEvents) {
    if (!eventGroups.has(event.sportKey)) {
      eventGroups.set(event.sportKey, []);
    }
    eventGroups.get(event.sportKey).push(event);
  }

  for (const [sportKey, events] of eventGroups) {
    fragment.append(renderEventSportHeading(sportKey, events));
    for (const event of events) {
    const row = document.createElement("label");
    row.className = "event-row";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.eventId = event.id;
    checkbox.checked = state.selectedEventIds.has(event.id);
    const summary = document.createElement("div");
    summary.className = "event-summary";
    summary.textContent = buildEventSummary(event, state.titleFormat);
    const meta = document.createElement("div");
    meta.className = "event-meta";
    const metaItems = [
      { label: formatDateRange(event.startDate, event.endDateExclusive), className: "event-date" },
      { label: event.location },
      { label: event.competitionKey !== "unassigned" && !event.competitionKey.startsWith("catalog_") ? event.competitionLabel : "" },
      { label: event.season },
      { label: getAudienceScopeLabel(event) },
    ].filter((item) => item.label);
    for (const item of metaItems) {
      const metaItem = document.createElement("span");
      metaItem.className = `event-meta-item ${item.className ?? ""}`.trim();
      metaItem.textContent = item.label;
      meta.append(metaItem);
    }
    for (const sourceUrl of event.sourceEvidence ?? []) {
      const link = document.createElement("a");
      link.className = "event-meta-item event-source";
      link.href = sourceUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Reviewed source";
      link.setAttribute("aria-label", `Reviewed source for ${event.title}`);
      meta.append(link);
    }
    const content = document.createElement("div");
    content.className = "event-content";
    content.append(summary, meta);
    row.append(checkbox, content);
    fragment.append(row);
    }
  }
  elements.events.append(fragment);
}

function renderEventSportHeading(sportKey, events) {
  const header = document.createElement("header");
  header.className = "event-sport-group-heading";
  const title = document.createElement("h3");
  title.className = "event-sport-heading";
  title.textContent = events[0].sportLabel;
  const selection = getSelectionState(events.map((event) => event.id), state.selectedEventIds);
  const count = document.createElement("span");
  count.className = "event-sport-count";
  count.textContent = `${selection.selectedCount}/${selection.availableCount} selected`;
  const actions = document.createElement("div");
  actions.className = "event-sport-actions";
  actions.append(
    createEventSportActionButton(sportKey, events[0].sportLabel, "select", "Select visible"),
    createEventSportActionButton(sportKey, events[0].sportLabel, "clear", "Clear visible"),
  );
  header.append(title, count, actions);
  return header;
}

function renderStats() {
  updateExportRangeOptions();
  const selectedSummary = getSelectedSummary();
  const exportSummary = getExportSummary();
  const selectedOnlyLabel = state.showSelectedOnly ? " · View: selected only" : "";
  elements.statsText.textContent = `${state.catalog?.year ?? "Catalog"}: ${state.events.length} available · ${selectedSummary.eventsCount} selected · ${state.visibleEvents.length} visible${selectedOnlyLabel}`;
  elements.selectedOnlyToggle.setAttribute("aria-pressed", String(state.showSelectedOnly));
  elements.exportButton.textContent = getExportButtonLabel(exportSummary.eventsCount);
  elements.exportEventsCount.textContent = String(exportSummary.eventsCount);
  elements.exportSportsCount.textContent = String(exportSummary.sportsCount);
}

async function exportIcs() {
  const summary = getExportSummary();
  if (summary.events.length === 0) {
    setExportStatus(state.exportRange === EXPORT_RANGE_FROM_TODAY
      ? "No selected events are available from today onward."
      : "Select at least one event before exporting.");
    return;
  }

  const calendarName = elements.calendarName.value.trim() || "Sportkalender Selection";
  const icsContent = createIcs(summary.events, calendarName, state.titleFormat);
  const blob = new Blob([icsContent], { type: "text/calendar;charset=utf-8" });
  const icsFile = createIcsFile(blob);
  if (icsFile && canShareIcsFile(icsFile)) {
    try {
      await navigator.share({
        files: [icsFile],
        title: calendarName,
        text: `Sportkalender export (${summary.eventsCount} events)`,
      });
      setExportStatus(`Shared ${summary.eventsCount} events across ${summary.sportsCount} sports.`);
      return;
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        setExportStatus("Share canceled. You can try again or download instead.");
        return;
      }
    }
  }
  triggerIcsDownload(blob, EXPORT_FILE_NAME);
  setExportStatus(`Downloaded ${summary.eventsCount} events across ${summary.sportsCount} sports.`);
}

function getSelectedSummary() {
  const events = state.events.filter((event) => isEventEligibleForCurrentFilters(event) && state.selectedEventIds.has(event.id));
  return {
    events,
    eventsCount: events.length,
    sportsCount: new Set(events.map((event) => event.sportKey)).size,
  };
}

function getExportSummary() {
  const selectedSummary = getSelectedSummary();
  const events = filterEventsForExport(selectedSummary.events, state.exportRange, getLocalIsoDate());
  return {
    events,
    eventsCount: events.length,
    sportsCount: new Set(events.map((event) => event.sportKey)).size,
  };
}

function updateExportRangeOptions() {
  const option = elements.exportRange.querySelector('option[value="from_today"]');
  if (!option) {
    return;
  }
  const available = isFromTodayExportAvailable(state.events, getLocalIsoDate(), state.catalog?.year ?? null);
  option.hidden = !available;
  option.disabled = !available;
  if (!available) {
    state.exportRange = EXPORT_RANGE_FULL_YEAR;
  }
  elements.exportRange.value = state.exportRange;
}

function setExportStatus(message) {
  elements.exportStatus.textContent = message;
  elements.exportDock.dataset.status = message === IDLE_EXPORT_STATUS_TEXT ? "idle" : "active";
}

function getExportButtonLabel(eventsCount) {
  return canAttemptNativeShare() ? `Share or download ICS (${eventsCount})` : `Download ICS (${eventsCount})`;
}

function canAttemptNativeShare() {
  return typeof navigator.share === "function" && typeof navigator.canShare === "function" && typeof File === "function";
}

function createIcsFile(blob) {
  return typeof File === "function" ? new File([blob], EXPORT_FILE_NAME, { type: "text/calendar;charset=utf-8" }) : null;
}

function canShareIcsFile(file) {
  if (!canAttemptNativeShare()) {
    return false;
  }
  try {
    return navigator.canShare({ files: [file] });
  } catch {
    return false;
  }
}

function triggerIcsDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function hydrateStateFromStorage(stored) {
  if (!stored || typeof stored !== "object") {
    elements.query.value = state.query;
    elements.titleFormat.value = state.titleFormat;
    elements.exportRange.value = state.exportRange;
    return;
  }

  if (Array.isArray(stored.selectedSports)) {
    const availableSports = new Set(state.taxonomy.sports.map((sport) => sport.key));
    state.selectedSports = new Set(stored.selectedSports.filter((sport) => availableSports.has(sport)));
  }
  const availableSportGroups = new Set(getSportGroups().map((group) => group.category));
  if (Array.isArray(stored.collapsedSportCategories)) {
    state.collapsedSportCategories = new Set(stored.collapsedSportCategories.filter((category) => availableSportGroups.has(category)));
  }
  if (Array.isArray(stored.selectedCountries)) {
    const availableCountries = new Set(COUNTRY_FILTERS.map((country) => country.key));
    state.selectedCountries = new Set(stored.selectedCountries.filter((country) => availableCountries.has(country)));
  }
  state.selectedEventIds = restoreCatalogSelection({ events: state.events, storedState: stored });
  if (typeof stored.query === "string") {
    state.query = stored.query;
  }
  if (stored.titleFormat === "sport_event" || stored.titleFormat === "event_only") {
    state.titleFormat = stored.titleFormat;
  }
  if (typeof stored.calendarName === "string" && stored.calendarName.trim()) {
    elements.calendarName.value = stored.calendarName.trim();
  }
  if (typeof stored.showSelectedOnly === "boolean") {
    state.showSelectedOnly = stored.showSelectedOnly;
  }
  if (stored.exportRange === EXPORT_RANGE_FROM_TODAY || stored.exportRange === EXPORT_RANGE_FULL_YEAR) {
    state.exportRange = stored.exportRange;
  }
  elements.query.value = state.query;
  elements.titleFormat.value = state.titleFormat;
  elements.exportRange.value = state.exportRange;
}

function persistState() {
  if (!state.catalogId) {
    return;
  }
  const payload = createCatalogStatePayload({
    catalogId: state.catalogId,
    selectedEventIds: state.selectedEventIds,
    events: state.events,
    selectedSports: state.selectedSports,
    selectedCountries: state.selectedCountries,
    collapsedSportCategories: state.collapsedSportCategories,
    query: state.query,
    titleFormat: state.titleFormat,
    calendarName: elements.calendarName.value.trim(),
    showSelectedOnly: state.showSelectedOnly,
    exportRange: state.exportRange,
  });
  const serialized = JSON.stringify(payload);
  const localStorageKey = createCatalogStateKey(state.catalogId);
  const sessionStorageKey = createCatalogSessionStateKey(state.catalogId);
  if (getUtf8ByteLength(serialized) <= MAX_PERSISTED_STATE_BYTES) {
    safeStorageWrite(getStorage("localStorage"), localStorageKey, serialized);
    safeStorageRemove(getStorage("sessionStorage"), sessionStorageKey);
  } else {
    safeStorageWrite(getStorage("sessionStorage"), sessionStorageKey, serialized);
    safeStorageRemove(getStorage("localStorage"), localStorageKey);
  }
}

function readStoredState(catalogId) {
  const localState = parseStoredState(safeStorageRead(getStorage("localStorage"), createCatalogStateKey(catalogId)));
  if (localState) {
    return localState;
  }
  return parseStoredState(safeStorageRead(getStorage("sessionStorage"), createCatalogSessionStateKey(catalogId)));
}

function getStorage(name) {
  try {
    return globalThis[name] ?? null;
  } catch {
    return null;
  }
}

function applySportSelectionUpdate(updateSelectedSports, focusTarget = getSportsFocusTarget()) {
  const nextState = applySportSelectionChange({
    events: state.events,
    selectedSports: state.selectedSports,
    selectedEventIds: state.selectedEventIds,
    updateSelectedSports,
  });
  state.selectedSports = nextState.selectedSports;
  state.selectedEventIds = nextState.selectedEventIds;
  renderSports();
  restoreSportsFocus(focusTarget);
  applyFilters();
  persistState();
}

function setEventSearchCollapsed(collapsed, { moveFocus = true } = {}) {
  elements.eventsPanel.classList.toggle("search-collapsed", collapsed);
  elements.collapseEventSearch.setAttribute("aria-expanded", String(!collapsed));
  elements.expandEventSearch.setAttribute("aria-expanded", String(!collapsed));
  if (!moveFocus) {
    return;
  }
  if (collapsed) {
    elements.expandEventSearch.focus();
  } else {
    elements.query.focus();
  }
}

function getSportGroups() {
  const groups = new Map();
  for (const sport of state.taxonomy.sports) {
    if (!groups.has(sport.group)) {
      groups.set(sport.group, []);
    }
    groups.get(sport.group).push(sport);
  }
  return [...groups.entries()].map(([category, sports]) => ({ category, sports }));
}

function getSportsForCategory(category) {
  return getSportGroups().find((group) => group.category === category)?.sports ?? [];
}

function getDefaultCollapsedSportCategories() {
  return new Set(getSportGroups().slice(3).map((group) => group.category));
}

function toggleSportCategory(category) {
  const focusTarget = getSportsFocusTarget();
  if (state.collapsedSportCategories.has(category)) {
    state.collapsedSportCategories.delete(category);
  } else {
    state.collapsedSportCategories.add(category);
  }
  renderSports();
  restoreSportsFocus(focusTarget);
  persistState();
}

function createSportActionButton(category, action, label) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "sport-group-action";
  button.dataset.groupAction = action;
  button.dataset.groupName = category;
  button.textContent = label;
  return button;
}

function createEventSportActionButton(sportKey, sportLabel, action, label) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "event-sport-action";
  button.dataset.eventSportAction = action;
  button.dataset.eventSportKey = sportKey;
  button.setAttribute("aria-label", `${action === "select" ? "Select" : "Clear"} all visible ${sportLabel} events`);
  button.textContent = label;
  return button;
}

function getSportsFocusTarget() {
  return document.activeElement instanceof Element && elements.sports.contains(document.activeElement)
    ? getSportsFocusTargetFromElement(document.activeElement)
    : null;
}

function getSportsFocusTargetFromElement(element) {
  if (!(element instanceof Element)) {
    return null;
  }
  const sportInput = element.closest("input[data-sport]");
  if (sportInput instanceof HTMLInputElement) {
    return { type: "sport", sport: sportInput.dataset.sport };
  }
  const sportToggle = element.closest("button[data-group-toggle='collapse']");
  if (sportToggle instanceof HTMLButtonElement) {
    return { type: "toggle", category: sportToggle.dataset.groupName };
  }
  return null;
}

function restoreSportsFocus(focusTarget) {
  if (!focusTarget) {
    return;
  }
  let nextFocus = null;
  if (focusTarget.type === "sport") {
    nextFocus = elements.sports.querySelector(`input[data-sport="${CSS.escape(focusTarget.sport)}"]`);
  } else if (focusTarget.type === "toggle") {
    nextFocus = elements.sports.querySelector(`button[data-group-toggle="collapse"][data-group-name="${CSS.escape(focusTarget.category)}"]`);
  }
  if (nextFocus instanceof HTMLElement) {
    nextFocus.focus();
  }
}

function compareVisibleEvents(left, right) {
  const leftSportOrder = state.taxonomy.sports.findIndex((sport) => sport.key === left.sportKey);
  const rightSportOrder = state.taxonomy.sports.findIndex((sport) => sport.key === right.sportKey);
  return leftSportOrder - rightSportOrder ||
    left.startDate.localeCompare(right.startDate) ||
    left.endDateExclusive.localeCompare(right.endDateExclusive) ||
    (left.id < right.id ? -1 : left.id > right.id ? 1 : 0);
}

function formatDateRange(startDate, endDateExclusive) {
  const start = new Date(`${startDate}T00:00:00Z`);
  const end = new Date(`${endDateExclusive}T00:00:00Z`);
  end.setUTCDate(end.getUTCDate() - 1);
  const startLabel = start.toLocaleDateString("de-DE");
  const endLabel = end.toLocaleDateString("de-DE");
  return startLabel === endLabel ? startLabel : `${startLabel} - ${endLabel}`;
}

function getUtf8ByteLength(value) {
  if (typeof TextEncoder === "function") {
    return new TextEncoder().encode(value).length;
  }
  return encodeURIComponent(value).replace(/%[0-9A-F]{2}/g, "x").length;
}

function showCatalogError(error) {
  const message = error instanceof Error ? error.message : String(error);
  elements.catalogStatus.textContent = `Catalog error: ${message}`;
  elements.statsText.textContent = "Could not load events.";
  elements.events.replaceChildren();
  const empty = document.createElement("p");
  empty.className = "empty";
  empty.textContent = "The selected catalog could not be loaded.";
  elements.events.append(empty);
}
