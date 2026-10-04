import test from "node:test";
import assert from "node:assert/strict";

import {
  applySportSelectionChange,
  createCatalogSessionStateKey,
  createCatalogStateKey,
  createCatalogStatePayload,
  filterEventsForExport,
  getSelectionState,
  isFromTodayExportAvailable,
  isEventVisibleForSelectedCountries,
  normalizeSelectedEventIds,
  restoreSelectedEventIds,
  restoreCatalogSelection,
  updateSelectedEventIds,
} from "./app-state.mjs";

test("sport changes preserve manual event deselection", () => {
  const events = [
    { id: "run-a", sport: "Running" },
    { id: "run-b", sport: "Running" },
    { id: "tennis-a", sport: "Tennis" },
  ];

  let selectionState = {
    selectedSports: new Set(["Running", "Tennis"]),
    selectedEventIds: new Set(["run-a", "tennis-a"]),
  };

  selectionState = applySportSelectionChange({
    events,
    selectedSports: selectionState.selectedSports,
    selectedEventIds: selectionState.selectedEventIds,
    updateSelectedSports(nextSelectedSports) {
      nextSelectedSports.delete("Running");
    },
  });

  selectionState = applySportSelectionChange({
    events,
    selectedSports: selectionState.selectedSports,
    selectedEventIds: selectionState.selectedEventIds,
    updateSelectedSports(nextSelectedSports) {
      nextSelectedSports.add("Running");
    },
  });

  assert.deepEqual([...selectionState.selectedSports].sort(), ["Running", "Tennis"]);
  assert.deepEqual([...selectionState.selectedEventIds].sort(), ["run-a", "tennis-a"]);
  assert.equal(selectionState.selectedEventIds.has("run-b"), false);
});

test("selection normalization removes stale event ids", () => {
  const events = [{ id: "one" }, { id: "two" }];
  const selectedEventIds = normalizeSelectedEventIds(events, ["one", "ghost"]);

  assert.deepEqual([...selectedEventIds].sort(), ["one"]);
});

test("legacy empty stored selection restores to all events", () => {
  const events = [{ id: "one" }, { id: "two" }];
  const selectedEventIds = restoreSelectedEventIds({
    events,
    storedSelectedEventIds: [],
    selectionInitialized: false,
  });

  assert.deepEqual([...selectedEventIds].sort(), ["one", "two"]);
});

test("explicit empty stored selection remains empty after initialization", () => {
  const events = [{ id: "one" }, { id: "two" }];
  const selectedEventIds = restoreSelectedEventIds({
    events,
    storedSelectedEventIds: [],
    selectionInitialized: true,
  });

  assert.deepEqual([...selectedEventIds], []);
});

test("from today keeps events that are active today and later", () => {
  const events = [
    { id: "past", startDate: "2026-01-01", endDateExclusive: "2026-07-28" },
    { id: "today", startDate: "2026-07-28", endDateExclusive: "2026-07-29" },
    { id: "future", startDate: "2026-08-01", endDateExclusive: "2026-08-02" },
  ];

  assert.deepEqual(
    filterEventsForExport(events, "from_today", "2026-07-28").map((event) => event.id),
    ["today", "future"]
  );
  assert.deepEqual(
    filterEventsForExport(events, "full_year", "2026-07-28").map((event) => event.id),
    ["past", "today", "future"]
  );
});

test("from today is offered only when the loaded year has started", () => {
  const futureEvents = [{ startDate: "2027-01-01", endDateExclusive: "2027-01-02" }];
  const startedEvents = [{ startDate: "2026-01-01", endDateExclusive: "2026-01-02" }];

  assert.equal(isFromTodayExportAvailable(futureEvents, "2026-07-28", 2027), false);
  assert.equal(isFromTodayExportAvailable(startedEvents, "2026-07-28", 2026), true);
  assert.equal(isFromTodayExportAvailable(startedEvents, "2026-07-28", 2025), false);
  assert.equal(isFromTodayExportAvailable(startedEvents, "2026-07-28"), true);
});

test("country selection filters only national events", () => {
  const selectedCountries = new Set(["DE"]);

  assert.equal(isEventVisibleForSelectedCountries({
    coverage: "national",
    audienceCountries: ["DE"],
  }, selectedCountries), true);
  assert.equal(isEventVisibleForSelectedCountries({
    coverage: "national",
    audienceCountries: ["US"],
    hostCountries: ["DE"],
  }, selectedCountries), false);
  assert.equal(isEventVisibleForSelectedCountries({
    coverage: "shared_major",
    audienceCountries: ["US", "GB"],
  }, new Set()), true);
  assert.equal(isEventVisibleForSelectedCountries({
    coverage: "not_tagged",
    title: "World Championships",
    audienceCountries: [],
  }, new Set()), true);
});

test("a national event needs only one of its assigned countries", () => {
  const event = { id: "shared-national", coverage: "national", audienceCountries: ["DE", "FR"] };
  assert.equal(isEventVisibleForSelectedCountries(event, new Set(["DE"])), true);
  assert.equal(isEventVisibleForSelectedCountries(event, new Set(["FR"])), true);
  assert.equal(isEventVisibleForSelectedCountries(event, new Set(["US"])), false);
  assert.equal(isEventVisibleForSelectedCountries(event, new Set()), false);
});

test("catalog state keys are scoped by catalog year", () => {
  assert.equal(createCatalogStateKey("2026"), "sportkalender:web-state:v3:2026");
  assert.equal(createCatalogSessionStateKey("2027"), "sportkalender:web-state:session:v3:2027");
});

test("new catalog events are not selected after an update", () => {
  const oldEvents = [{ id: "old" }, { id: "kept" }];
  const newEvents = [...oldEvents, { id: "new" }];
  const storedState = createCatalogStatePayload({
    catalogId: "2026",
    selectedEventIds: new Set(["old", "kept"]),
    events: oldEvents,
    selectedSports: new Set(["football"]),
    collapsedSportCategories: new Set(),
    collapsedCatalogGroups: new Set(),
    query: "",
    titleFormat: "sport_event",
    calendarName: "Calendar",
    showSelectedOnly: false,
    exportRange: "full_year",
  });

  assert.deepEqual(
    [...restoreCatalogSelection({ events: newEvents, storedState })].sort(),
    ["kept", "old"],
  );
});

test("selection state exposes checked, mixed, and unchecked values", () => {
  assert.deepEqual(getSelectionState(["a", "b"], new Set(["a"])), {
    availableCount: 2,
    selectedCount: 1,
    checked: false,
    mixed: true,
  });
  assert.equal(getSelectionState(["a"], new Set(["a"])).checked, true);
  assert.equal(getSelectionState(["a"], new Set()).mixed, false);
});

test("group actions only change their event ids", () => {
  const next = updateSelectedEventIds(new Set(["a", "outside"]), ["a", "b"], false);
  assert.deepEqual([...next].sort(), ["outside"]);
});
