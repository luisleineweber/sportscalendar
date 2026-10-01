from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from sportkalender.catalog_model import normalize_key, normalize_text


class RegistryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SportDefinition:
    key: str
    display_name: str
    group_key: str
    order: int
    aliases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompetitionDefinition:
    key: str
    display_name: str
    sport_key: str
    kind: str
    primary_display_group: str
    audience_countries: tuple[str, ...]
    aliases: tuple[str, ...]
    closing_stage: str = ""


@dataclass(frozen=True, slots=True)
class CatalogRegistry:
    sports: dict[str, SportDefinition]
    sports_by_alias: dict[str, str]
    competitions: dict[str, CompetitionDefinition]
    competitions_by_alias: dict[str, str]


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise RegistryError(f"cannot read registry {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise RegistryError(f"invalid JSON in registry {path}: {error}") from error


def _string(value: object, field_name: str, index: int) -> str:
    result = normalize_text(value)
    if not result:
        raise RegistryError(f"registry entry {index} has no {field_name}")
    return result


def _aliases(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise RegistryError("registry aliases must be arrays")
    return tuple(normalize_text(item) for item in value if normalize_text(item))


def _alias_map(entries: list[tuple[str, tuple[str, ...]]], label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, aliases in entries:
        for alias in (key, *aliases):
            normalized = normalize_key(alias)
            previous = result.get(normalized)
            if previous and previous != key:
                raise RegistryError(f"{label} alias {alias!r} maps to both {previous!r} and {key!r}")
            result[normalized] = key
    return result


def load_sports_registry(path: Path) -> tuple[dict[str, SportDefinition], dict[str, str]]:
    raw = _load_json(path)
    if not isinstance(raw, dict) or not isinstance(raw.get("sports"), list):
        raise RegistryError(f"{path} must contain a sports array")
    groups = raw.get("groups", [])
    if not isinstance(groups, list):
        raise RegistryError(f"{path} groups must be an array")
    group_keys: set[str] = set()
    for index, item in enumerate(groups, start=1):
        if not isinstance(item, dict):
            raise RegistryError(f"group entry {index} is not an object")
        group_keys.add(_string(item.get("key"), "key", index))

    definitions: dict[str, SportDefinition] = {}
    aliases: list[tuple[str, tuple[str, ...]]] = []
    for index, item in enumerate(raw["sports"], start=1):
        if not isinstance(item, dict):
            raise RegistryError(f"sport entry {index} is not an object")
        key = _string(item.get("key"), "key", index).casefold()
        if key in definitions:
            raise RegistryError(f"duplicate sport key {key!r}")
        definition = SportDefinition(
            key=key,
            display_name=_string(item.get("display_name"), "display_name", index),
            group_key=_string(item.get("group_key"), "group_key", index),
            order=int(item.get("order", index)),
            aliases=_aliases(item.get("aliases")),
        )
        if group_keys and definition.group_key not in group_keys:
            raise RegistryError(f"sport {key!r} references unknown group {definition.group_key!r}")
        definitions[key] = definition
        aliases.append((key, definition.aliases))
    return definitions, _alias_map(aliases, "sport")


def load_competitions_registry(path: Path) -> tuple[dict[str, CompetitionDefinition], dict[str, str]]:
    raw = _load_json(path)
    if not isinstance(raw, dict) or not isinstance(raw.get("competitions"), list):
        raise RegistryError(f"{path} must contain a competitions array")

    definitions: dict[str, CompetitionDefinition] = {}
    aliases: list[tuple[str, tuple[str, ...]]] = []
    for index, item in enumerate(raw["competitions"], start=1):
        if not isinstance(item, dict):
            raise RegistryError(f"competition entry {index} is not an object")
        key = _string(item.get("key"), "key", index).casefold()
        if key in definitions:
            raise RegistryError(f"duplicate competition key {key!r}")
        countries = item.get("audience_countries", [])
        if not isinstance(countries, list):
            raise RegistryError(f"competition {key!r} audience_countries must be an array")
        definition = CompetitionDefinition(
            key=key,
            display_name=_string(item.get("display_name"), "display_name", index),
            sport_key=_string(item.get("sport_key"), "sport_key", index).casefold(),
            kind=_string(item.get("kind"), "kind", index).casefold(),
            primary_display_group=_string(item.get("primary_display_group"), "primary_display_group", index),
            audience_countries=tuple(normalize_text(country).upper() for country in countries if normalize_text(country)),
            aliases=_aliases(item.get("aliases")),
            closing_stage=normalize_key(item.get("closing_stage")),
        )
        definitions[key] = definition
        aliases.append((key, definition.aliases))
    return definitions, _alias_map(aliases, "competition")


def load_registry(sports_path: Path, competitions_path: Path) -> CatalogRegistry:
    sports, sports_by_alias = load_sports_registry(sports_path)
    competitions, competitions_by_alias = load_competitions_registry(competitions_path)
    unknown_sports = sorted({definition.sport_key for definition in competitions.values() if definition.sport_key not in sports})
    if unknown_sports:
        raise RegistryError(f"competition registry references unknown sports: {', '.join(unknown_sports)}")
    for sport in sports.values():
        key = f"catalog_{sport.key}"
        if key not in competitions:
            competitions[key] = CompetitionDefinition(
                key=key,
                display_name=f"Other {sport.display_name} events",
                sport_key=sport.key,
                kind="competition",
                primary_display_group="unassigned",
                audience_countries=(),
                aliases=(),
            )
    return CatalogRegistry(
        sports=sports,
        sports_by_alias=sports_by_alias,
        competitions=competitions,
        competitions_by_alias=competitions_by_alias,
    )
