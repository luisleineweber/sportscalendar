export function getDefaultSelectedEventIds(events) {
  return new Set(events.map((event) => event.id));
}

export function normalizeSelectedEventIds(events, selectedEventIds) {
  const validEventIds = new Set(events.map((event) => event.id));
  return new Set([...selectedEventIds].filter((id) => validEventIds.has(id)));
}

export function restoreSelectedEventIds({
  events,
  storedSelectedEventIds,
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

  return defaultSelectedEventIds;
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
