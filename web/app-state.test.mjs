import test from "node:test";
import assert from "node:assert/strict";

import {
  applySportSelectionChange,
  filterEventsForExport,
  isFromTodayExportAvailable,
  normalizeSelectedEventIds,
  restoreSelectedEventIds,
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
