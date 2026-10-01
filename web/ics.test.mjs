import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEventSummary,
  compareIcsEvents,
  createIcs,
  escapeIcsText,
  foldIcsLine,
} from "./ics.mjs";

function byteLength(value) {
  return new TextEncoder().encode(value).length;
}

test("ICS uses stable event IDs and deterministic date ordering", () => {
  const events = [
    { id: "z-event", startDate: "2026-01-01", endDateExclusive: "2026-01-02", title: "Later" },
    { id: "a-event", startDate: "2026-01-01", endDateExclusive: "2026-01-02", title: "Earlier by ID" },
  ];
  const ics = createIcs(events, "My, Calendar", "event_only");

  assert.match(ics, /UID:a-event@sportkalender/);
  assert.match(ics, /UID:z-event@sportkalender/);
  assert.ok(ics.indexOf("UID:a-event@sportkalender") < ics.indexOf("UID:z-event@sportkalender"));
  assert.match(ics, /X-WR-CALNAME:My\\, Calendar/);
  assert.match(ics, /DTEND;VALUE=DATE:20260102/);
  assert.equal(createIcs(events, "My, Calendar", "event_only"), createIcs([...events].reverse(), "My, Calendar", "event_only"));
});

test("ICS escapes punctuation and line breaks", () => {
  assert.equal(escapeIcsText("A\\B;C,D\nE"), "A\\\\B\\;C\\,D\\nE");
  assert.equal(buildEventSummary({ title: "Final", sportLabel: "Football", sport: "football" }), "Football - Final");
});

test("UTF-8 folding stays within 75 bytes and keeps code points intact", () => {
  const line = `SUMMARY:${"äöü é 🚴 ".repeat(30)}`;
  const folded = foldIcsLine(line);
  assert.ok(folded.length > 1);
  assert.ok(folded.every((physicalLine) => byteLength(physicalLine) <= 75));
  assert.equal(folded[0] + folded.slice(1).map((physicalLine) => physicalLine.slice(1)).join(""), line);
  assert.ok(folded.slice(1).every((physicalLine) => physicalLine.startsWith(" ")));
});

test("comparison uses the stable ID as its final ordinal", () => {
  const base = { startDate: "2026-01-01", endDateExclusive: "2026-01-02" };
  assert.ok(compareIcsEvents({ ...base, id: "a" }, { ...base, id: "b" }) < 0);
});

test("long UTF-8 location values are folded in the exported file", () => {
  const ics = createIcs([
    {
      id: "unicode-location",
      startDate: "2026-05-01",
      endDateExclusive: "2026-05-02",
      title: "München 🚴",
      sportLabel: "Cycling",
      location: "Lange Straße, München – Zielbereich 🚴 ".repeat(8),
    },
  ], "Kalender", "sport_event");
  const physicalLines = ics.split("\r\n").filter(Boolean);

  assert.ok(physicalLines.every((line) => byteLength(line) <= 75));
  assert.match(ics, /UID:unicode-location@sportkalender/);
});
