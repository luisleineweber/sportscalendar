from __future__ import annotations

def compare_catalogs(previous, current, explained_removals=frozenset()):
    before = {event.event_id: event for event in previous}
    after = {event.event_id: event for event in current}
    rows = []
    for event_id in sorted(before.keys() | after.keys()):
        old, new = before.get(event_id), after.get(event_id)
        if old is None:
            status = "added"
        elif new is None:
            status = "confirmed_removal" if event_id in explained_removals else "missing"
        elif (old.start_date, old.end_date_exclusive) != (new.start_date, new.end_date_exclusive):
            status = "date_changed"
        elif old.exact_values() != new.exact_values():
            status = "metadata_changed"
        else:
            continue
        rows.append({"event_id": event_id, "title": (new or old).title, "status": status,
                     "old_dates": [old.start_date.isoformat(), old.inclusive_end_date.isoformat()] if old else None,
                     "new_dates": [new.start_date.isoformat(), new.inclusive_end_date.isoformat()] if new else None})
    return rows
