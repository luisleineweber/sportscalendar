import { readFileSync } from "node:fs";
import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCatalogTaxonomy,
  createCustomEventId,
  loadCatalog,
  loadCatalogManifest,
  normalizeCatalogManifest,
  parseCatalogTsv,
  parseCatalogTsvWithDiagnostics,
  parseDateRange,
  getAudienceScopeLabel,
} from "./catalog.mjs";

function response(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    async json() {
      return JSON.parse(body);
    },
    async text() {
      return body;
    },
  };
}

test("manifest normalizes catalog entries and keeps the default", () => {
  const manifest = normalizeCatalogManifest({
    default: "2026",
    catalogs: {
      2026: { id: "2026", year: 2026, file: "2026.tsv" },
    },
  });

  assert.equal(manifest.default, "2026");
  assert.deepEqual(manifest.catalogs.map((entry) => entry.id), ["2026"]);
});

test("manifest failures stay visible", async () => {
  await assert.rejects(() => loadCatalogManifest({ url: "catalogs.json", fetchImpl: async () => response("missing", 404) }), /404/);
  await assert.rejects(
    () => loadCatalogManifest({ fetchImpl: async () => response("broken", 500) }),
    /500/,
  );
});

test("header TSV loading preserves metadata and ignores column order", () => {
  const text = [
    "event_id\tcompetition_key\tDatum\tEreignis\tSportart\taudience_countries\tcoverage\tOrt\tseason",
    "nfl-2026-season\tnfl\t01.09.2026 - 01.01.2027\t2026 NFL season\tAmerican football\tUS\tnational\tNew York\t2026",
  ].join("\n");
  const events = parseCatalogTsv(text, { catalogYear: 2026 });

  assert.equal(events.length, 1);
  assert.equal(events[0].id, "nfl-2026-season");
  assert.equal(events[0].location, "New York");
  assert.equal(events[0].competitionKey, "nfl");
  assert.deepEqual(events[0].audienceCountries, ["US"]);
  assert.equal(events[0].endDateExclusive, "2027-01-02");
});

test("legacy catalog parsing reports invalid ranges without publishing them", () => {
  const text = readFileSync("data/sportkalender_2026.tsv", "utf8");
  const parsed = parseCatalogTsvWithDiagnostics(text, { catalogYear: 2026 });

  assert.equal(parsed.events.length, 540);
  assert.equal(parsed.diagnostics.rejectedCount, 2);
  assert.ok(parsed.diagnostics.errors.every((error) => error.reason === "invalid_date_range"));
});

test("stable published IDs survive date and location corrections", () => {
  const first = parseCatalogTsv([
    "event_id\tdate\ttitle\tsport\tlocation",
    "edition-2026\t01.01.2026\tFinal\tFootball\tBerlin",
  ].join("\n"), { catalogYear: 2026 })[0];
  const corrected = parseCatalogTsv([
    "event_id\tdate\ttitle\tsport\tlocation",
    "edition-2026\t02.01.2026\tFinal\tFootball\tMunich",
  ].join("\n"), { catalogYear: 2026 })[0];

  assert.equal(first.id, corrected.id);
  assert.notEqual(first.startDate, corrected.startDate);
  assert.notEqual(first.location, corrected.location);
});

test("custom input IDs are deterministic and correction-sensitive", () => {
  const input = {
    startDate: "2026-01-01",
    endDateExclusive: "2026-01-02",
    title: "Final",
    sport: "Football",
    location: "Berlin",
  };
  assert.equal(createCustomEventId(input), createCustomEventId(input));
  assert.notEqual(createCustomEventId(input), createCustomEventId({ ...input, location: "Munich" }));
});

test("custom input ID matches the Python fixture", () => {
  assert.equal(createCustomEventId({
    startDate: "2026-09-01",
    endDateExclusive: "2026-09-02",
    title: "Final 🎾",
    sport: "Tennis",
    location: "München, DE",
  }), "custom:1161e51ae494c4f3");
});

test("taxonomy exposes international and competition groups without duplicating events", () => {
  const events = parseCatalogTsv([
    "event_id\tdate\ttitle\tsport_key\tcompetition_key\tcoverage\taudience_countries",
    "ucl-2026\t01.06.2026\tUEFA Champions League final\tfootball\tuefa_champions_league\tshared_major\tDE;GB",
    "nfl-2026\t01.09.2026\t2026 NFL season\tamerican_football\tnfl\tnational\tUS",
  ].join("\n"), { catalogYear: 2026 });
  const taxonomy = buildCatalogTaxonomy(events);

  assert.ok(taxonomy.groups.some((group) => group.key === "international"));
  assert.ok(taxonomy.competitions.some((competition) => competition.key === "nfl"));
  assert.equal(new Set(taxonomy.groups.flatMap((group) => group.eventIds)).size, events.length);
});

test("date parser rejects reversed explicit dates and supports named months", () => {
  assert.equal(parseDateRange("10.1.2026 - 9.1.2026", { catalogYear: 2026 }), null);
  assert.deepEqual(parseDateRange("9 January 2026", { catalogYear: 2026 }), {
    startDate: "2026-01-09",
    endDateExclusive: "2026-01-10",
  });
});

test("catalog loading fetches the manifest-selected header TSV", async () => {
  const manifest = {
    default: "2028",
    catalogs: [{ id: "2028", year: 2028, file: "2028.tsv", status: "ready" }],
  };
  const catalog = await loadCatalog({
    manifest,
    catalogId: "2028",
    fetchImpl: async (url) => {
      assert.equal(url, "2028.tsv");
      return response("event_id\tdate\ttitle\tsport\nready-1\t01.01.2028\tOpening\tFootball\n");
    },
  });

  assert.equal(catalog.id, "2028");
  assert.equal(catalog.events[0].id, "ready-1");
  assert.equal(catalog.status, "ready");
});

test("catalog loading resolves files relative to the manifest URL", async () => {
  const manifest = await loadCatalogManifest({
    url: "http://localhost/web/../data/catalogs.json",
    fetchImpl: async (url) => {
      assert.equal(url, "http://localhost/web/../data/catalogs.json");
      return response(JSON.stringify({
        default: "2026",
        catalogs: [{ id: "2026", year: 2026, file: "releases/catalog_2026.tsv", status: "ready" }],
      }));
    },
  });
  await loadCatalog({
    manifest,
    catalogId: "2026",
    fetchImpl: async (url) => {
      assert.equal(url, "http://localhost/data/releases/catalog_2026.tsv");
      return response("event_id\tdate\ttitle\tsport\nready-1\t01.01.2026\tOpening\tFootball\n");
    },
  });
});

test("untagged legacy rows do not inherit invented country audiences", () => {
  const events = parseCatalogTsv([
    "event_id\tdate\ttitle\tsport_key\tcompetition_key\tcoverage\taudience_countries",
    "preview-1\t01.01.2026\tExample\tfootball\tcatalog_football\tnot_tagged\t",
  ].join("\n"), {
    catalogYear: 2026,
    manifest: { competitions: [{ key: "catalog_football", sportKey: "football", audienceCountries: ["DE", "US"], primaryDisplayGroup: "international" }] },
  });
  assert.deepEqual(events[0].audienceCountries, []);
  assert.equal(events[0].displayGroupKey, "unassigned");
});

test("published catalog loading rejects rows with missing IDs", async () => {
  const manifest = {
    default: "2026",
    catalogs: [{ id: "2026", year: 2026, file: "catalog.tsv", evidence: "catalog.json", event_count: 1 }],
  };
  await assert.rejects(() => loadCatalog({
    manifest,
    fetchImpl: async () => response("date\ttitle\tsport\n01.01.2026\tOpening\tFootball\n"),
  }), /published row checks/);
});

test("published catalog loading attaches its event evidence", async () => {
  const eventId = `event-${"a".repeat(64)}`;
  const manifest = {
    default: "2026",
    catalogs: [{ id: "2026", year: 2026, file: "catalog.tsv", evidence: "catalog.json", event_count: 1 }],
  };
  const catalog = await loadCatalog({
    manifest,
    fetchImpl: async (url) => url === "catalog.tsv"
      ? response(`event_id\tdate\ttitle\tsport\n${eventId}\t01.01.2026\tOpening\tFootball\n`)
      : response(JSON.stringify({ event_evidence: { [eventId]: [{ source_id: "official-schedule" }] } })),
  });
  assert.deepEqual(catalog.events[0].sourceEvidence, []);
  assert.equal(catalog.events[0].coverage, "not_tagged");
});

test("scope labels keep unresolved rows separate from international events", () => {
  assert.equal(getAudienceScopeLabel({ coverage: "not_tagged" }), "Unresolved audience scope");
  assert.equal(getAudienceScopeLabel({ coverage: "shared_major" }), "International");
  assert.equal(getAudienceScopeLabel({ coverage: "national", audienceCountries: ["DE", "FR"] }), "Germany, France");
});

const reviewedEventId = `event-${"b".repeat(64)}`;
const reviewedEventTsv = [
  "event_id\tdate\ttitle\tsport_key\tcompetition_key\tseason\tstage\tcoverage\taudience_countries",
  `${reviewedEventId}\t21.08.2026\tLeague opener\tfootball\tpremier_league\t2026-27\tseason_opener\tnational\tGB`,
].join("\n");
const reviewedEventEvidence = {
  source_id: "organizer", source_url: "https://example.test/schedule",
  competition_key: "premier_league", season: "2026-27", stage: "season_opener",
  date_decision: "verified", date_checked_at: "2026-10-01", date_statement: "The opener is on 21 August.",
  confirmed_start_date: "2026-08-21", confirmed_end_date: "2026-08-21",
  audience_decision: "verified", audience_checked_at: "2026-10-01", audience_statement: "This is a domestic league.",
  coverage: "national", audience_countries: ["GB"],
};

function loadReviewedEvent(record = reviewedEventEvidence, status = "ready") {
  return loadCatalog({
    manifest: { default: "2026", catalogs: [{ id: "2026", year: 2026, file: "catalog.tsv", evidence: "catalog.json", event_count: 1, status }] },
    fetchImpl: async (url) => response(url === "catalog.tsv"
      ? reviewedEventTsv : JSON.stringify({ event_evidence: { [reviewedEventId]: [record] } })),
  });
}

test("reviewed national scope and exact source dates remain visible", async () => {
  const { events } = await loadReviewedEvent();
  assert.equal(events[0].coverage, "national");
  assert.deepEqual(events[0].audienceCountries, ["GB"]);
  assert.deepEqual(events[0].sourceEvidence, ["https://example.test/schedule"]);
});

test("source links require the current event dates", async () => {
  const { events } = await loadReviewedEvent({ ...reviewedEventEvidence, confirmed_start_date: "2026-08-22" });
  assert.deepEqual(events[0].sourceEvidence, []);
});

test("Ready rejects unresolved audience scope and Preview labels it", async () => {
  const record = { ...reviewedEventEvidence, audience_decision: "pending_review" };
  await assert.rejects(() => loadReviewedEvent(record), /unresolved audience scope/);
  const { events } = await loadReviewedEvent(record, "preview");
  assert.equal(events[0].coverage, "not_tagged");
  assert.deepEqual(events[0].audienceCountries, []);
});
