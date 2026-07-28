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
