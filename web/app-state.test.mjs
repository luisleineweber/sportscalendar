import test from "node:test";
import assert from "node:assert/strict";

import {
  applySportSelectionChange,
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
