export const FIXED_DTSTAMP = "20000101T000000Z";
export const ICS_PRODID = "-//Sportkalender Web//Calendar Export//EN";

export function createIcs(events, calendarName, titleFormat = "sport_event") {
  const sortedEvents = [...events].sort(compareIcsEvents);
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "CALSCALE:GREGORIAN",
    `PRODID:${ICS_PRODID}`,
    `X-WR-CALNAME:${escapeIcsText(calendarName)}`,
  ];

  for (const event of sortedEvents) {
    const eventId = getEventId(event);
    if (!eventId) {
      throw new Error("Cannot export an event without a stable event ID.");
    }

    lines.push(
      "BEGIN:VEVENT",
      `UID:${eventId}@sportkalender`,
      `DTSTAMP:${FIXED_DTSTAMP}`,
      `DTSTART;VALUE=DATE:${toBasicDate(event.startDate)}`,
      `DTEND;VALUE=DATE:${toBasicDate(event.endDateExclusive)}`,
      `SUMMARY:${escapeIcsText(buildEventSummary(event, titleFormat))}`,
    );
    if (event.location) {
      lines.push(`LOCATION:${escapeIcsText(event.location)}`);
    }
    lines.push("END:VEVENT");
  }

  lines.push("END:VCALENDAR");
  return lines.flatMap((line) => foldIcsLine(line)).join("\r\n") + "\r\n";
}

export function compareIcsEvents(left, right) {
  return left.startDate.localeCompare(right.startDate) ||
    left.endDateExclusive.localeCompare(right.endDateExclusive) ||
    compareOrdinal(getEventId(left), getEventId(right));
}

export function getEventId(event) {
  return String(event.eventId ?? event.id ?? "");
}

export function buildEventSummary(event, titleFormat = "sport_event") {
  if (titleFormat === "event_only") {
    return event.title;
  }

  const sportLabel = event.sportLabel ?? event.sport ?? "";
  const noPrefixSports = new Set(["diverse", "multisportveranstaltung", "marathon", "multi_sport"]);
  if (!sportLabel || noPrefixSports.has(String(event.sport ?? sportLabel).toLocaleLowerCase())) {
    return event.title;
  }
  return `${sportLabel} - ${event.title}`;
}

export function escapeIcsText(value) {
  return String(value ?? "")
    .replaceAll("\\", "\\\\")
    .replaceAll(";", "\\;")
    .replaceAll(",", "\\,")
    .replace(/\r\n|\r|\n/g, "\\n");
}

export function foldIcsLine(line, maxBytes = 75) {
  const value = String(line);
  if (utf8ByteLength(value) <= maxBytes) {
    return [value];
  }

  const folded = [];
  let segment = "";
  let segmentBytes = 0;
  let firstLine = true;
  let limit = maxBytes;

  for (const character of value) {
    const characterBytes = utf8ByteLength(character);
    if (segment && segmentBytes + characterBytes > limit) {
      folded.push(`${firstLine ? "" : " "}${segment}`);
      firstLine = false;
      segment = "";
      segmentBytes = 0;
      limit = maxBytes - 1;
    }
    segment += character;
    segmentBytes += characterBytes;
  }

  if (segment || folded.length === 0) {
    folded.push(`${firstLine ? "" : " "}${segment}`);
  }
  return folded;
}

export const foldLine = foldIcsLine;

export function toBasicDate(isoDate) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(isoDate))) {
    throw new Error(`Invalid ISO date: ${isoDate}`);
  }
  return String(isoDate).replaceAll("-", "");
}

function utf8ByteLength(value) {
  if (typeof TextEncoder === "function") {
    return new TextEncoder().encode(value).length;
  }
  return unescape(encodeURIComponent(value)).length;
}

function compareOrdinal(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}
