export const DEFAULT_MANIFEST_URL = "../data/catalogs.json";

export const COUNTRY_LABELS = {
  DE: "Germany",
  US: "USA",
  GB: "United Kingdom",
  FR: "France",
  IT: "Italy",
};

export const DEFAULT_COMPETITIONS = [
  {
    key: "nfl",
    label: "NFL",
    sportKey: "american_football",
    kind: "league",
    primaryDisplayGroup: "country:US",
    audienceCountries: ["US"],
  },
  {
    key: "nba",
    label: "NBA",
    sportKey: "basketball",
    kind: "league",
    primaryDisplayGroup: "country:US",
    audienceCountries: ["US"],
  },
  {
    key: "uefa_champions_league",
    label: "UEFA Champions League",
    sportKey: "football",
    kind: "competition",
    primaryDisplayGroup: "international",
    audienceCountries: ["DE", "GB", "FR", "IT"],
  },
];

const DEFAULT_SPORT_DEFINITIONS = [
  ["football", "Football", "Top Sports"],
  ["tennis", "Tennis", "Top Sports"],
  ["basketball", "Basketball", "Top Sports"],
  ["handball", "Handball", "Top Sports"],
  ["american_football", "American Football", "Top Sports"],
  ["ice_hockey", "Ice Hockey", "Top Sports"],
  ["darts", "Darts", "Top Sports"],
  ["badminton", "Badminton", "Ball Sports"],
  ["beach_handball", "Beach Handball", "Ball Sports"],
  ["field_hockey", "Field Hockey", "Ball Sports"],
  ["floorball", "Floorball", "Ball Sports"],
  ["volleyball", "Volleyball", "Ball Sports"],
  ["water_polo", "Water Polo", "Ball Sports"],
  ["table_tennis", "Table Tennis", "Ball Sports"],
  ["athletics", "Athletics", "Athletics & Endurance"],
  ["marathon", "Marathon", "Athletics & Endurance"],
  ["triathlon", "Triathlon", "Athletics & Endurance"],
  ["modern_pentathlon", "Modern Pentathlon", "Athletics & Endurance"],
  ["cycling", "Cycling", "Athletics & Endurance"],
  ["biathlon", "Biathlon", "Winter Sports"],
  ["bobsleigh_skeleton", "Bobsleigh / Skeleton", "Winter Sports"],
  ["curling", "Curling", "Winter Sports"],
  ["figure_skating", "Figure Skating", "Winter Sports"],
  ["speed_skating", "Speed Skating", "Winter Sports"],
  ["freestyle_skiing", "Freestyle Skiing", "Winter Sports"],
  ["luge", "Luge", "Winter Sports"],
  ["short_track", "Short Track", "Winter Sports"],
  ["alpine_skiing", "Alpine Skiing", "Winter Sports"],
  ["nordic_skiing", "Nordic Skiing", "Winter Sports"],
  ["ski_mountaineering", "Ski Mountaineering", "Winter Sports"],
  ["snowboarding", "Snowboarding", "Winter Sports"],
  ["boxing", "Boxing", "Combat & Precision"],
  ["fencing", "Fencing", "Combat & Precision"],
  ["weightlifting", "Weightlifting", "Combat & Precision"],
  ["judo", "Judo", "Combat & Precision"],
  ["wrestling", "Wrestling", "Combat & Precision"],
  ["archery", "Archery", "Combat & Precision"],
  ["snooker", "Snooker", "Combat & Precision"],
  ["canoeing", "Canoeing", "Water & Outdoor"],
  ["rowing", "Rowing", "Water & Outdoor"],
  ["equestrian", "Equestrian", "Water & Outdoor"],
  ["sport_climbing", "Sport Climbing", "Water & Outdoor"],
  ["swimming", "Swimming", "Water & Outdoor"],
  ["chess", "Chess", "Mind & Mixed"],
  ["multi_sport", "Multi-sport", "Mind & Mixed"],
  ["gymnastics", "Gymnastics", "Mind & Mixed"],
  ["rhythmic_gymnastics", "Rhythmic Gymnastics", "Mind & Mixed"],
  ["trampoline", "Trampoline", "Mind & Mixed"],
];

const SPORT_ALIASES = new Map([
  ["association_football", "football"],
  ["association football", "football"],
  ["soccer", "football"],
  ["ice_hockey", "ice_hockey"],
  ["ice hockey", "ice_hockey"],
  ["road_bicycle_racing", "cycling"],
  ["road cycling", "cycling"],
  ["track_cycling", "cycling"],
  ["mountain_bike_cycling", "cycling"],
  ["mountain biking", "cycling"],
  ["urban cycling", "cycling"],
  ["vollyball", "volleyball"],
  ["table tennis", "table_tennis"],
  ["table_tennis", "table_tennis"],
  ["beach handball", "beach_handball"],
  ["field hockey", "field_hockey"],
  ["floorball", "floorball"],
  ["water polo", "water_polo"],
  ["american football", "american_football"],
  ["athletics", "athletics"],
  ["multi-sport", "multi_sport"],
  ["multi sport", "multi_sport"],
  ["modern pentathlon", "modern_pentathlon"],
  ["bobsleigh and skeleton", "bobsleigh_skeleton"],
  ["figure skating", "figure_skating"],
  ["speed skating", "speed_skating"],
  ["short track", "short_track"],
  ["short-track speed skating", "short_track"],
  ["alpine skiing", "alpine_skiing"],
  ["nordic skiing", "nordic_skiing"],
  ["freestyle skiing", "freestyle_skiing"],
  ["ski mountaineering", "ski_mountaineering"],
  ["snowboarding", "snowboarding"],
  ["sport climbing", "sport_climbing"],
  ["climbing", "sport_climbing"],
  ["swimming", "swimming"],
  ["aquatics", "swimming"],
  ["artistic swimming", "swimming"],
  ["gymnastics", "gymnastics"],
  ["rhythmic gymnastics", "rhythmic_gymnastics"],
  ["trampoline", "trampoline"],
  ["canoe slalom", "canoeing"],
  ["canoeing", "canoeing"],
  ["equestrian", "equestrian"],
  ["horse racing", "equestrian"],
  ["rowing", "rowing"],
  ["weightlifting", "weightlifting"],
  ["archery", "archery"],
  ["boxing", "boxing"],
  ["amateur boxing", "boxing"],
  ["fencing", "fencing"],
  ["judo", "judo"],
  ["wrestling", "wrestling"],
  ["snooker", "snooker"],
  ["chess", "chess"],
  ["marathon", "marathon"],
  ["triathlon", "triathlon"],
  ["darts", "darts"],
]);

const MONTHS = new Map([
  ["jan", 1],
  ["january", 1],
  ["januar", 1],
  ["feb", 2],
  ["february", 2],
  ["februar", 2],
  ["mar", 3],
  ["march", 3],
  ["mär", 3],
  ["maerz", 3],
  ["mrz", 3],
  ["märz", 3],
  ["apr", 4],
  ["april", 4],
  ["may", 5],
  ["mai", 5],
  ["jun", 6],
  ["june", 6],
  ["juni", 6],
  ["jul", 7],
  ["july", 7],
  ["juli", 7],
  ["aug", 8],
  ["august", 8],
  ["sep", 9],
  ["sept", 9],
  ["september", 9],
  ["okt", 10],
  ["oct", 10],
  ["october", 10],
  ["oktober", 10],
  ["nov", 11],
  ["november", 11],
  ["dez", 12],
  ["dec", 12],
  ["december", 12],
  ["dezember", 12],
]);

const SPORT_GROUP_ORDER = [
  "Top Sports",
  "Ball Sports",
  "Athletics & Endurance",
  "Winter Sports",
  "Combat & Precision",
  "Water & Outdoor",
  "Mind & Mixed",
  "Motorsport",
  "Other Sports",
];

export class CatalogLoadError extends Error {
  constructor(message, cause = null) {
    super(message);
    this.name = "CatalogLoadError";
    this.cause = cause;
  }
}

export function normalizeKey(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase()
    .replace(/ß/g, "ss")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
}

export function normalizeHeader(value) {
  return normalizeKey(value);
}

export function normalizeCatalogManifest(manifest) {
  if (!manifest || typeof manifest !== "object") {
    throw new CatalogLoadError("Catalog manifest is not an object.");
  }

  const rawCatalogs = Array.isArray(manifest.catalogs)
    ? manifest.catalogs
    : manifest.catalogs && typeof manifest.catalogs === "object"
      ? Object.values(manifest.catalogs)
      : Array.isArray(manifest.entries)
        ? manifest.entries
        : [];
  const catalogs = rawCatalogs.map((catalog) => ({ ...catalog, id: String(catalog.id ?? catalog.year ?? "") }));
  if (catalogs.length === 0 || catalogs.some((catalog) => !catalog.id || !catalog.file)) {
    throw new CatalogLoadError("Catalog manifest has no usable catalog entries.");
  }

  const defaultId = String(manifest.default ?? catalogs[0].id);
  if (!catalogs.some((catalog) => catalog.id === defaultId)) {
    throw new CatalogLoadError(`Catalog manifest default ${defaultId} is not available.`);
  }

  return {
    ...manifest,
    default: defaultId,
    catalogs,
  };
}

function resolveManifestPath(path, manifestUrl) {
  if (!manifestUrl || typeof path !== "string") {
    return path;
  }
  try {
    return new URL(path, new URL(manifestUrl, globalThis.location?.href ?? manifestUrl)).toString();
  } catch {
    return path;
  }
}

export async function loadCatalogManifest({
  url = DEFAULT_MANIFEST_URL,
  fetchImpl = globalThis.fetch,
} = {}) {
  if (typeof fetchImpl !== "function") {
    throw new CatalogLoadError("The browser does not provide fetch().");
  }

  let response;
  try {
    response = await fetchImpl(url, { cache: "no-cache" });
  } catch (error) {
    throw new CatalogLoadError(`Could not load catalog manifest from ${url}.`, error);
  }

  if (!response.ok) {
    throw new CatalogLoadError(`Could not load catalog manifest from ${url}: ${response.status}.`);
  }

  try {
    return {
      ...normalizeCatalogManifest(await response.json()),
      manifestUrl: url,
    };
  } catch (error) {
    if (error instanceof CatalogLoadError) {
      throw error;
    }
    throw new CatalogLoadError(`Catalog manifest from ${url} is not valid JSON.`, error);
  }
}

export function getCatalogEntry(manifest, catalogId) {
  const normalizedManifest = normalizeCatalogManifest(manifest);
  const entry = normalizedManifest.catalogs.find((catalog) => catalog.id === String(catalogId));
  if (!entry) {
    throw new CatalogLoadError(`Catalog ${catalogId} is not available.`);
  }
  return entry;
}

export async function loadCatalog({ manifest, catalogId, fetchImpl = globalThis.fetch } = {}) {
  const entry = getCatalogEntry(manifest, catalogId ?? manifest.default);
  let response;
  try {
    response = await fetchImpl(resolveManifestPath(entry.file, manifest.manifestUrl));
  } catch (error) {
    throw new CatalogLoadError(`Could not load catalog ${entry.id}.`, error);
  }
  if (!response.ok) {
    throw new CatalogLoadError(`Could not load catalog ${entry.id}: ${response.status}.`);
  }

  const parsed = parseCatalogTsvWithDiagnostics(await response.text(), {
    catalogYear: Number(entry.year ?? entry.id),
    manifest,
  });
  if (entry.evidence && (
    parsed.diagnostics.rejectedCount > 0 ||
    parsed.events.some((event) => !/^event-[0-9a-f]{64}$/.test(event.id)) ||
    parsed.events.length !== entry.event_count
  )) {
    throw new CatalogLoadError(`Catalog ${entry.id} failed published row checks.`);
  }
  let events = parsed.events;
  if (entry.evidence) {
    const evidenceUrl = resolveManifestPath(entry.evidence, manifest.manifestUrl);
    let evidenceResponse;
    try {
      evidenceResponse = await fetchImpl(evidenceUrl);
    } catch (error) {
      throw new CatalogLoadError(`Could not load evidence for catalog ${entry.id}.`, error);
    }
    if (!evidenceResponse.ok) {
      throw new CatalogLoadError(`Could not load evidence for catalog ${entry.id}: ${evidenceResponse.status}.`);
    }
    const evidence = await evidenceResponse.json();
    const eventEvidence = evidence?.event_evidence;
    if (!eventEvidence || typeof eventEvidence !== "object" ||
      Object.keys(eventEvidence).length !== events.length ||
      events.some((event) => !Object.hasOwn(eventEvidence, event.id))) {
      throw new CatalogLoadError(`Catalog ${entry.id} evidence IDs do not match the events.`);
    }
    events = events.map((event) => {
      const records = Array.isArray(eventEvidence[event.id]) ? eventEvidence[event.id] : [];
      const scopeVerified = records.some((item) =>
        item?.audience_decision === "verified" && item.audience_checked_at && item.audience_statement
        && item.source_url && item.source_id && item.coverage === event.coverage
        && item.source_current !== false
        && Array.isArray(item.audience_countries)
        && [...item.audience_countries].sort().join(";") === [...event.audienceCountries].sort().join(";")
        && ["national", "shared_major"].includes(event.coverage)
        && (event.coverage !== "national" || event.audienceCountries.length > 0));
      if (entry.status === "ready" && !scopeVerified) {
        throw new CatalogLoadError(`Catalog ${entry.id} has unresolved audience scope.`);
      }
      return {
        ...event,
        coverage: scopeVerified ? event.coverage : "not_tagged",
        audienceCountries: scopeVerified ? event.audienceCountries : [],
      };
    });
  }
  return {
    ...entry,
    id: entry.id,
    year: Number(entry.year ?? entry.id),
    events,
    diagnostics: parsed.diagnostics,
    taxonomy: buildCatalogTaxonomy(events, manifest),
  };
}

export function parseCatalogTsv(text, options = {}) {
  return parseCatalogTsvWithDiagnostics(text, options).events;
}

export function parseCatalogTsvWithDiagnostics(text, { catalogYear = null, manifest = {} } = {}) {
  const lines = String(text ?? "").replace(/^\uFEFF/, "").split(/\r?\n/);
  const headerIndex = lines.findIndex((line) => line.trim() && !line.trim().startsWith("###"));
  if (headerIndex < 0) {
    throw new CatalogLoadError("Catalog TSV has no header.");
  }

  const headers = lines[headerIndex].split("\t").map(normalizeHeader);
  const headerSet = new Set(headers);
  if (!findHeader(headers, "title") || (!findHeader(headers, "date") && !findHeader(headers, "start_date"))) {
    throw new CatalogLoadError("Catalog TSV is missing a date or title header.");
  }

  const events = [];
  const errors = [];
  const seenIds = new Set();
  for (let index = headerIndex + 1; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.trim() || line.trim().startsWith("###")) {
      continue;
    }

    const values = line.split("\t");
    const row = Object.fromEntries(headers.map((header, columnIndex) => [header, (values[columnIndex] ?? "").trim()]));
    const parsed = parseCatalogRow(row, { catalogYear, manifest });
    if (!parsed.event) {
      errors.push({ line: index + 1, reason: parsed.reason, row });
      continue;
    }
    if (seenIds.has(parsed.event.id)) {
      errors.push({ line: index + 1, reason: "duplicate_event_id", row });
      continue;
    }
    seenIds.add(parsed.event.id);
    events.push(parsed.event);
  }

  events.sort(compareCatalogEvents);
  return {
    events,
    diagnostics: {
      headerSet,
      rowCount: lines.length - headerIndex - 1,
      acceptedCount: events.length,
      rejectedCount: errors.length,
      errors,
    },
  };
}

export function parseCatalogRow(row, { catalogYear = null, manifest = {} } = {}) {
  const title = readField(row, "title");
  const sportRaw = readField(row, "sport") || readField(row, "sport_key");
  const location = readField(row, "location");
  const dateRange = readField(row, "date");
  const startDateRaw = readField(row, "start_date");
  const endDateRaw = readField(row, "end_date_exclusive") || readField(row, "end_date");

  if (!title || !sportRaw) {
    return { event: null, reason: "missing_title_or_sport" };
  }

  const dateResult = startDateRaw
    ? parseExplicitDateRange(startDateRaw, endDateRaw, catalogYear)
    : parseDateRange(dateRange, { catalogYear });
  if (!dateResult) {
    return { event: null, reason: "invalid_date_range" };
  }

  const sportKey = normalizeSportKey(readField(row, "sport_key") || sportRaw);
  const competitionKey = readField(row, "competition_key") || deriveCompetitionKey(title);
  const competition = getCompetitionDefinition(competitionKey, manifest);
  const audienceCountries = parseList(readField(row, "audience_countries"));
  const coverage = readField(row, "coverage");
  const resolvedAudienceCountries = coverage === "not_tagged"
    ? []
    : audienceCountries.length > 0
    ? audienceCountries
    : competition?.audienceCountries ?? [];
  const eventId = readField(row, "event_id") || createCustomEventId({
    startDate: dateResult.startDate,
    endDateExclusive: dateResult.endDateExclusive,
    title,
    sport: sportRaw,
    location,
  });
  if (!/^[A-Za-z0-9._:-]+$/.test(eventId)) {
    return { event: null, reason: "invalid_event_id" };
  }

  const displayGroupKey = readField(row, "display_group") || resolveDisplayGroupKey({
    coverage,
    audienceCountries: resolvedAudienceCountries,
    competition,
  });
  const sportDefinition = getSportDefinition(sportKey, manifest);
  const event = {
    id: eventId,
    eventId,
    startDate: dateResult.startDate,
    endDateExclusive: dateResult.endDateExclusive,
    title,
    sport: sportKey,
    sportKey,
    sportLabel: sportDefinition.label,
    sportGroup: sportDefinition.group,
    rawSport: sportRaw,
    disciplineKey: readField(row, "discipline_key"),
    location,
    competitionKey: competitionKey || "unassigned",
    competitionLabel: competition?.label || readField(row, "competition_name") || "Not assigned",
    competitionKind: readField(row, "competition_kind") || competition?.kind || "catalog",
    season: readField(row, "season"),
    stage: readField(row, "stage"),
    coverage: coverage || "not_tagged",
    audienceCountries: resolvedAudienceCountries,
    ukHomeNations: parseList(readField(row, "uk_home_nations")),
    hostCountries: parseList(readField(row, "host_countries")),
    eventKind: readField(row, "event_kind") || inferEventKind(title),
    displayGroupKey,
  };

  return { event, reason: null };
}

export function createCustomEventId({ startDate, endDateExclusive, title, sport, location = "" }) {
  const source = [startDate, endDateExclusive, title, sport, location]
    .map((value) => String(value ?? "").trim().normalize("NFC"))
    .join("\u001f");
  return `custom:${hashFnv1a64(source)}`;
}

export function parseDateRange(value, { catalogYear = null, contextMonth = null } = {}) {
  const raw = String(value ?? "").trim();
  if (!raw) {
    return null;
  }

  const numericDates = [...raw.matchAll(/(\d{1,2})[./](\d{1,2})[./](\d{4})/g)].map((match) => ({
    day: Number(match[1]),
    month: Number(match[2]),
    year: Number(match[3]),
  }));
  if (numericDates.length > 0) {
    const start = toValidDate(numericDates[0]);
    const end = toValidDate(numericDates[1] ?? numericDates[0]);
    return toDateRange(start, end);
  }

  const normalized = raw.replace(/[–—−]/g, "-").replace(/\s+/g, " ");
  const monthMatches = [...normalized.matchAll(/([A-Za-zÄÖÜäöü.]+)\s*(\d{4})?/g)]
    .map((match) => ({ month: monthNumber(match[1]), year: match[2] ? Number(match[2]) : null }))
    .filter((match) => match.month);
  if (monthMatches.length === 0 || !catalogYear) {
    return null;
  }

  const dayMatches = [...normalized.matchAll(/\b(\d{1,2})\b/g)].map((match) => Number(match[1]));
  if (dayMatches.length === 0) {
    return null;
  }

  const startMonth = monthMatches[0].month;
  const startYear = monthMatches[0].year ?? catalogYear;
  let endMonth = monthMatches[1]?.month ?? startMonth;
  let endYear = monthMatches[1]?.year ?? startYear;
  let startDay = dayMatches[0];
  let endDay = dayMatches[1] ?? startDay;

  if (monthMatches.length === 1 && contextMonth && startMonth <= 2 && contextMonth >= 8 && dayMatches.length > 1) {
    const contextualStart = toValidDate({ day: startDay, month: contextMonth, year: catalogYear });
    if (contextualStart) {
      endMonth = startMonth;
      endYear = catalogYear + 1;
    }
  }

  const start = toValidDate({ day: startDay, month: startMonth, year: startYear });
  const end = toValidDate({ day: endDay, month: endMonth, year: endYear });
  return toDateRange(start, end);
}

export function compareCatalogEvents(left, right) {
  return left.startDate.localeCompare(right.startDate) ||
    left.endDateExclusive.localeCompare(right.endDateExclusive) ||
    compareOrdinal(left.id, right.id);
}

export function buildCatalogTaxonomy(events, manifest = {}) {
  const sportDefinitions = new Map(events.map((event) => [event.sportKey, getSportDefinition(event.sportKey, manifest)]));
  const sports = [...sportDefinitions.entries()]
    .map(([key, definition]) => ({ key, ...definition, eventIds: events.filter((event) => event.sportKey === key).map((event) => event.id) }))
    .sort((left, right) => groupOrder(left.group) - groupOrder(right.group) || compareOrdinal(left.label, right.label));
  const groups = new Map();
  const competitions = new Map();
  for (const event of events) {
    const groupKey = event.displayGroupKey || "unassigned";
    const group = groups.get(`${event.sportKey}|${groupKey}`) ?? {
      key: groupKey,
      sportKey: event.sportKey,
      label: getDisplayGroupLabel(groupKey),
      eventIds: [],
      competitions: new Map(),
    };
    group.eventIds.push(event.id);
    const competition = group.competitions.get(event.competitionKey) ?? {
      key: event.competitionKey,
      label: event.competitionLabel,
      sportKey: event.sportKey,
      eventIds: [],
    };
    competition.eventIds.push(event.id);
    group.competitions.set(event.competitionKey, competition);
    groups.set(`${event.sportKey}|${groupKey}`, group);
    competitions.set(`${event.sportKey}|${event.competitionKey}`, competition);
  }

  const configuredCompetitions = Array.isArray(manifest.competitions)
    ? manifest.competitions
    : Object.values(manifest.competitions ?? {});
  for (const configured of configuredCompetitions) {
    const sportKey = String(configured.sportKey ?? configured.sport_key ?? "");
    if (!sportDefinitions.has(sportKey)) {
      continue;
    }
    const competitionKey = String(configured.key ?? "");
    if (!competitionKey || competitions.has(`${sportKey}|${competitionKey}`)) {
      continue;
    }
    const displayGroupKey = resolveDisplayGroupKey({
      coverage: "",
      audienceCountries: parseList(configured.audienceCountries ?? configured.audience_countries),
      competition: getCompetitionDefinition(competitionKey, manifest),
    });
    const group = groups.get(`${sportKey}|${displayGroupKey}`) ?? {
      key: displayGroupKey,
      sportKey,
      label: getDisplayGroupLabel(displayGroupKey),
      eventIds: [],
      competitions: new Map(),
    };
    const competition = {
      key: competitionKey,
      label: configured.label ?? configured.display_name ?? competitionKey,
      sportKey,
      eventIds: [],
    };
    group.competitions.set(competitionKey, competition);
    groups.set(`${sportKey}|${displayGroupKey}`, group);
    competitions.set(`${sportKey}|${competitionKey}`, competition);
  }

  return {
    sports,
    groups: [...groups.values()]
      .map((group) => ({ ...group, competitions: [...group.competitions.values()].sort((left, right) => compareOrdinal(left.label, right.label)) }))
      .sort((left, right) => groupOrder(getSportDefinition(left.sportKey, manifest).group) - groupOrder(getSportDefinition(right.sportKey, manifest).group) || compareOrdinal(left.label, right.label)),
    competitions: [...competitions.values()].sort((left, right) => compareOrdinal(left.label, right.label)),
  };
}

export function normalizeSportKey(value) {
  const normalized = normalizeKey(value).replace(/_/g, " ");
  return SPORT_ALIASES.get(normalized) ?? SPORT_ALIASES.get(normalizeKey(value)) ?? (normalizeKey(value) || "unknown");
}

export function getSportDefinition(sportKey, manifest = {}) {
  const rawDefinitions = Array.isArray(manifest.sports)
    ? manifest.sports
    : manifest.sports && typeof manifest.sports === "object"
      ? Object.values(manifest.sports)
      : [];
  const configured = rawDefinitions.find((definition) => String(definition.key) === String(sportKey));
  if (configured) {
    return {
      label: configured.label ?? configured.name ?? sportKey,
      group: configured.group ?? "Other Sports",
    };
  }
  const fallback = DEFAULT_SPORT_DEFINITIONS.find(([key]) => key === sportKey);
  return fallback ? { label: fallback[1], group: fallback[2] } : { label: humanizeKey(sportKey), group: "Other Sports" };
}

export function getCompetitionDefinition(competitionKey, manifest = {}) {
  const rawDefinitions = [
    ...DEFAULT_COMPETITIONS,
    ...(Array.isArray(manifest.competitions) ? manifest.competitions : Object.values(manifest.competitions ?? {})),
  ];
  const definition = rawDefinitions.find((candidate) => String(candidate.key) === String(competitionKey));
  return definition
    ? {
        ...definition,
        label: definition.label ?? definition.name ?? definition.key,
        audienceCountries: parseList(definition.audienceCountries ?? definition.audience_countries),
        primaryDisplayGroup: definition.primaryDisplayGroup ?? definition.primary_display_group,
      }
    : null;
}

export function resolveDisplayGroupKey({ coverage, audienceCountries, competition }) {
  if (coverage === "not_tagged") {
    return "unassigned";
  }
  if (coverage === "shared_major" || competition?.primaryDisplayGroup === "international") {
    return "international";
  }
  if (competition?.primaryDisplayGroup) {
    return competition.primaryDisplayGroup;
  }
  return audienceCountries[0] ? `country:${audienceCountries[0]}` : "unassigned";
}

export function getEventDisplayTitle(title) {
  return title
    .replace(/\b(?:19|20)\d{2}(?:\s*[-\u2013\u2014/]\s*(?:\d{4}|\d{2}))?\b/g, "")
    .replace(/\(\s*\)|\[\s*\]/g, "")
    .replace(/\s+/g, " ")
    .replace(/^[\s\-\u2013\u2014/]+|[\s\-\u2013\u2014/]+$/g, "");
}

export function getAudienceScopeLabel(event) {
  if (event.coverage === "shared_major") return "International";
  if (event.coverage === "national" && event.audienceCountries?.length) {
    return event.audienceCountries.map((country) => COUNTRY_LABELS[country] ?? country).join(", ");
  }
  return "";
}

function readField(row, field) {
  const aliases = {
    date: ["date", "datum", "date_range", "dates"],
    start_date: ["start_date", "start", "startdate"],
    end_date_exclusive: ["end_date_exclusive", "end_exclusive", "enddateexclusive"],
    end_date: ["end_date", "end", "enddate"],
    title: ["title", "event", "ereignis", "name"],
    sport: ["sport", "sportart", "sport_name"],
    location: ["location", "ort", "venue", "place"],
    event_id: ["event_id", "eventid", "id"],
    competition_key: ["competition_key", "competition", "league_key"],
    competition_name: ["competition_name", "competition_label"],
    competition_kind: ["competition_kind"],
    sport_key: ["sport_key"],
    discipline_key: ["discipline_key"],
    coverage: ["coverage"],
    audience_countries: ["audience_countries", "audience", "countries"],
    uk_home_nations: ["uk_home_nations"],
    host_countries: ["host_countries", "host_country"],
    event_kind: ["event_kind", "kind"],
    season: ["season", "edition"],
    display_group: ["display_group", "primary_display_group"],
    source_ids: ["source_ids", "sources"],
    source_urls: ["source_urls", "source_url"],
  };
  const keys = aliases[field] ?? [field];
  for (const key of keys) {
    if (row[key]) {
      return String(row[key]).trim();
    }
  }
  return "";
}

function findHeader(headers, field) {
  const aliases = {
    date: ["date", "datum", "date_range", "dates"],
    start_date: ["start_date", "start", "startdate"],
    title: ["title", "event", "ereignis", "name"],
  };
  return (aliases[field] ?? [field]).find((alias) => headers.includes(alias));
}

function parseExplicitDateRange(startRaw, endRaw, catalogYear) {
  const start = parseDateValue(startRaw, catalogYear);
  const end = endRaw ? parseDateValue(endRaw, catalogYear) : start;
  return toDateRange(start, end, endRaw ? "exclusive" : "inclusive");
}

function parseDateValue(value, catalogYear) {
  const numeric = String(value).match(/^(\d{1,2})[./](\d{1,2})[./](\d{4})$/);
  if (numeric) {
    return toValidDate({ day: Number(numeric[1]), month: Number(numeric[2]), year: Number(numeric[3]) });
  }
  const named = String(value).match(/^(\d{1,2})\s+([A-Za-zÄÖÜäöü.]+)\s*(\d{4})?$/);
  if (named) {
    return toValidDate({ day: Number(named[1]), month: monthNumber(named[2]), year: Number(named[3] ?? catalogYear) });
  }
  return null;
}

function toDateRange(start, end, endMode = "inclusive") {
  if (!start || !end || end.getTime() < start.getTime()) {
    return null;
  }
  const exclusiveEnd = endMode === "exclusive" ? end : new Date(end.getTime() + 86400000);
  return {
    startDate: toIsoDate(start),
    endDateExclusive: toIsoDate(exclusiveEnd),
  };
}

function toValidDate({ day, month, year }) {
  if (!day || !month || !year) {
    return null;
  }
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day
    ? date
    : null;
}

function monthNumber(value) {
  return MONTHS.get(String(value).toLocaleLowerCase().replace(/\./g, "")) ?? null;
}

function toIsoDate(date) {
  return date.toISOString().slice(0, 10);
}

function parseList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  return String(value ?? "")
    .split(/[;,|]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function deriveCompetitionKey(title) {
  const normalized = String(title).toLocaleLowerCase();
  if (/\bnfl\b|super bowl/.test(normalized)) {
    return "nfl";
  }
  if (/\bnba\b/.test(normalized)) {
    return "nba";
  }
  if (normalized.includes("uefa champions league")) {
    return "uefa_champions_league";
  }
  return "unassigned";
}

function inferEventKind(title) {
  const normalized = String(title).toLocaleLowerCase();
  if (normalized.includes("final") || normalized.includes("super bowl")) {
    return "cup_final";
  }
  if (normalized.includes("season") || normalized.includes("league")) {
    return "season";
  }
  if (normalized.includes("championship") || normalized.includes("championships")) {
    return "national_championship";
  }
  return "tournament";
}

function humanizeKey(value) {
  return String(value ?? "unknown")
    .split("_")
    .map((part) => part ? part[0].toLocaleUpperCase() + part.slice(1) : part)
    .join(" ");
}

function getDisplayGroupLabel(key) {
  if (key === "international") {
    return "International";
  }
  if (key === "unassigned") {
    return "Not tagged";
  }
  if (key.startsWith("country:")) {
    const countryCode = key.slice("country:".length);
    return COUNTRY_LABELS[countryCode] ? `${COUNTRY_LABELS[countryCode]} (${countryCode})` : countryCode;
  }
  return humanizeKey(key);
}

function groupOrder(group) {
  const index = SPORT_GROUP_ORDER.indexOf(group);
  return index < 0 ? SPORT_GROUP_ORDER.length : index;
}

function compareOrdinal(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function hashFnv1a64(value) {
  let hash = 14695981039346656037n;
  for (const byte of new TextEncoder().encode(value)) {
    hash ^= BigInt(byte);
    hash = BigInt.asUintN(64, hash * 1099511628211n);
  }
  return hash.toString(16).padStart(16, "0");
}
