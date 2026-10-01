from __future__ import annotations

from collections import Counter


def discover_wikipedia(source, snapshot, year):
    from scripts.fetch_wikipedia_merged import (
        build_final_candidates, clean_text, is_de_sport_table, is_en_sport_table,
        normalize_de_table, normalize_en_table, normalize_text_fields, parse_tables,
    )
    from lxml.etree import ParserError
    import pandas as pd

    try:
        tables = parse_tables(snapshot.content.decode("utf-8"), source.language)
    except (UnicodeDecodeError, ValueError, ParserError) as error:
        return {"status": "parse_failed", "reason": f"The sport tables could not be read: {error}", "parsed_count": 0}
    frames = []
    for index, (table, context) in enumerate(tables):
        accepted = is_de_sport_table(table) if source.language == "de" else is_en_sport_table(table)
        if accepted:
            normalize = normalize_de_table if source.language == "de" else normalize_en_table
            frames.append(normalize(table, index, snapshot.url, context))
    if not frames:
        return {"status": "parse_failed", "reason": "No expected sport table is present.", "parsed_count": 0}
    candidates = build_final_candidates(normalize_text_fields(pd.concat(frames, ignore_index=True)), year)
    rejected = Counter(str(row["drop_reason"]) for _, row in candidates.iterrows() if not row["is_valid_final_row"])
    rows = []
    for _, row in candidates.iterrows():
        rows.append({
            "title": str(clean_text(row["event_raw"])), "sport": str(clean_text(row["sport_raw"])),
            "date_raw": str(clean_text(row["date_raw"])), "date": str(row["date"]) if row["is_valid_final_row"] else None,
            "status": "pending_review" if row["is_valid_final_row"] else "rejected",
            "reason": None if row["is_valid_final_row"] else str(row["drop_reason"]),
            "source_table_index": int(row["source_table_index"]), "blocks_ready": False,
        })
    return {"status": "discovery", "parsed_count": len(rows), "rejected_by_reason": dict(rejected), "discovered_events": rows}
