import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import assert from "node:assert/strict";

const webDirectory = dirname(fileURLToPath(import.meta.url));
const appSource = readFileSync(resolve(webDirectory, "app.js"), "utf8");

test("web app uses the current 2026 event catalog", () => {
  const dataUrlMatch = appSource.match(/const DATA_URL = "([^"]+)";/);

  assert.ok(dataUrlMatch, "DATA_URL is missing from web/app.js");
  assert.equal(dataUrlMatch[1], "../data/sportkalender_2026.tsv");

  const dataPath = resolve(webDirectory, dataUrlMatch[1]);
  const rows = readFileSync(dataPath, "utf8").split(/\r?\n/).filter(Boolean);

  assert.equal(rows[0], "Datum\tEreignis\tSportart\tOrt");
  assert.ok(rows.length > 500, "current catalog should contain the 2026 event list");
  assert.ok(rows.some((row) => row.includes("2026")), "current catalog must contain 2026 events");
});
