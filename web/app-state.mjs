export const STORAGE_SCHEMA_VERSION = 3;

export function getDefaultSelectedEventIds(events) {
  return new Set(events.map((event) => event.id));
}

export function getLocalIsoDate(value = new Date()) {
  if (typeof value === "string") {
    return value;
  }

  const pad = (part) => String(part).padStart(2, "0");
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}`;
}

export function isFromTodayExportAvailable(events, todayIsoDate, exportYear = null) {
  const currentYear = Number(todayIsoDate.slice(0, 4));
  if (exportYear !== null) {
    return exportYear === currentYear;
  }

  return events.some((event) => Number(event.startDate.slice(0, 4)) === currentYear);
}

export function filterEventsForExport(events, exportRange, todayIsoDate) {
  if (exportRange !== "from_today") {
    return [...events];
  }

  return events.filter((event) => event.endDateExclusive > todayIsoDate);
}

export function isEventVisibleForSelectedCountries(event, selectedCountries) {
  if (event.coverage !== "national") {
    return true;
  }

  return Array.isArray(event.audienceCountries)
    && event.audienceCountries.some((country) => selectedCountries.has(country));
}

export function normalizeSelectedEventIds(events, selectedEventIds) {
  const validEventIds = new Set(events.map((event) => event.id));
  return new Set([...selectedEventIds].filter((id) => validEventIds.has(id)));
}

export function getKnownEventIds(events) {
  return new Set(events.map((event) => event.id));
}

export function restoreSelectedEventIds({
  events,
  storedSelectedEventIds,
  storedKnownEventIds,
  selectionInitialized,
}) {
  const defaultSelectedEventIds = getDefaultSelectedEventIds(events);
  if (!Array.isArray(storedSelectedEventIds)) {
    return defaultSelectedEventIds;
  }

  const normalizedSelectedEventIds = normalizeSelectedEventIds(events, storedSelectedEventIds);
  if (normalizedSelectedEventIds.size > 0 || selectionInitialized) {
    return normalizedSelectedEventIds;
  }

  if (Array.isArray(storedKnownEventIds) && storedKnownEventIds.length > 0) {
    return new Set();
  }

  return defaultSelectedEventIds;
}

export function restoreCatalogSelection({ events, storedState }) {
  const state = storedState && typeof storedState === "object" ? storedState : null;
  return restoreSelectedEventIds({
    events,
    storedSelectedEventIds: state?.selectedEventIds,
    storedKnownEventIds: state?.knownEventIds,
    selectionInitialized: state?.selectionInitialized === true,
  });
}

export function createCatalogStateKey(catalogId, version = STORAGE_SCHEMA_VERSION) {
  return `sportkalender:web-state:v${version}:${catalogId}`;
}

export function createCatalogSessionStateKey(catalogId, version = STORAGE_SCHEMA_VERSION) {
  return `sportkalender:web-state:session:v${version}:${catalogId}`;
}

export function createCatalogStatePayload({
  catalogId,
  selectedEventIds,
  events,
  selectedSports,
  selectedCountries = new Set(),
  collapsedSportCategories,
  query,
  titleFormat,
  calendarName,
  showSelectedOnly,
  exportRange,
}) {
  return {
    schemaVersion: STORAGE_SCHEMA_VERSION,
    catalogId,
    selectedEventIds: [...selectedEventIds],
    knownEventIds: [...getKnownEventIds(events)],
    selectionInitialized: true,
    selectedSports: [...selectedSports],
    selectedCountries: [...selectedCountries],
    collapsedSportCategories: [...collapsedSportCategories],
    query,
    titleFormat,
    calendarName,
    showSelectedOnly,
    exportRange,
  };
}

export function applySportSelectionChange({
  events,
  selectedSports,
  selectedEventIds,
  updateSelectedSports,
}) {
  const nextSelectedSports = new Set(selectedSports);
  updateSelectedSports(nextSelectedSports);

  return {
    selectedSports: nextSelectedSports,
    selectedEventIds: normalizeSelectedEventIds(events, selectedEventIds),
  };
}

export function getSelectionState(eventIds, selectedEventIds) {
  const ids = [...new Set(eventIds)];
  const selectedCount = ids.filter((id) => selectedEventIds.has(id)).length;
  return {
    availableCount: ids.length,
    selectedCount,
    checked: ids.length > 0 && selectedCount === ids.length,
    mixed: selectedCount > 0 && selectedCount < ids.length,
  };
}

export function updateSelectedEventIds(selectedEventIds, eventIds, selected) {
  const nextSelectedEventIds = new Set(selectedEventIds);
  for (const eventId of new Set(eventIds)) {
    if (selected) {
      nextSelectedEventIds.add(eventId);
    } else {
      nextSelectedEventIds.delete(eventId);
    }
  }
  return nextSelectedEventIds;
}

export function safeStorageRead(storage, key) {
  try {
    return storage?.getItem(key) ?? null;
  } catch {
    return null;
  }
}

export function safeStorageWrite(storage, key, value) {
  try {
    storage?.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

export function safeStorageRemove(storage, key) {
  try {
    storage?.removeItem(key);
  } catch {
    return false;
  }
  return true;
}

export function parseStoredState(value) {
  if (!value) {
    return null;
  }

  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}
