import math
import random
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

APP_TITLE = "Dating'n'Ranking"
DATA_PATH = Path(__file__).with_name("data.xlsx")

AVATAR_OPTIONS = ["🧑", "👨", "🕺", "🤠", "🧔", "👦", "🧙", "🕴️", "🥷"]

POINT_CATEGORIES = {
    "communication": "Communication",
    "effort": "Effort",
    "respect": "Respect",
    "consistency": "Consistency",
    "future_fit": "Future Compatibility",
    "fun": "Fun Together",
    "spicy_time": "Spicy Time",
    "extra": "Extra",
}

RELATIONSHIP_STATUS_OPTIONS = [
    "Single",
    "It's complicated",
    "In a relationship",
    "Married to me",
    "Married to other people",
]

RELATIONSHIP_STATUS_DEFAULT_POINTS = {
    "Single": 6,
    "It's complicated": -3,
    "In a relationship": -10,
    "Married to me": 10,
    "Married to other people": -12,
}

LOOKING_FOR_OPTIONS = [
    "Serious relationship",
    "Open to serious",
    "Casual only",
    "Not sure",
]

LOOKING_FOR_DEFAULT_POINTS = {
    "Serious relationship": 6,
    "Open to serious": 3,
    "Casual only": -4,
    "Not sure": 0,
}

SETTINGS_COLUMNS = ["scope", "option", "points"]

SPICY_SETTINGS_DEFAULT_POINTS = {
    "spicy_foreplay": 1,
    "spicy_connection_strength": 1,
    "spicy_orgasm_count": 2,
    "spicy_orgasm_intensity": 1,
}

# Keep spicy scoring comparable to regular gestures.
SPICY_SCORE_DIVISOR = 4
SPICY_SCORE_CAP = 15

SPICY_EVENT_COLUMNS = [
    "id",
    "candidate_id",
    "created_at",
    "happened_at",
    "foreplay",
    "connection_strength",
    "orgasm_count",
    "orgasm_intensity",
    "session_intensity",
    "extra_points",
    "extra_reason",
    "points",
]

SIN_COLUMNS = ["id", "label", "life_percent", "created_at"]
SIN_EVENT_COLUMNS = ["id", "candidate_id", "sin_id", "sin_label", "life_percent", "created_at", "notes"]

LEVEL_COLUMNS = [
    "friend_zone_unlocked",
    "dating_zone_unlocked",
    "sleeping_together_unlocked",
    "relationship_zone_unlocked",
]

CANDIDATE_COLUMNS = [
    "id",
    "name",
    "avatar",
    "dating_since",
    "communication",
    "effort",
    "respect",
    "consistency",
    "future_fit",
    "fun",
    "spicy_time",
    "extra",
    "looks_base",
    "relationship_status",
    "looking_for",
    "friend_zone_unlocked",
    "dating_zone_unlocked",
    "sleeping_together_unlocked",
    "relationship_zone_unlocked",
    "sins_life_remaining",
    "sins_life_cap",
    "red_flags",
    "notes",
    "created_at",
]

ACTION_COLUMNS = ["id", "label", "category", "points", "created_at"]


def default_actions() -> pd.DataFrame:
    now = datetime.utcnow().isoformat(timespec="seconds")
    defaults = [
        {"id": 1, "label": "Quick reply", "category": "communication", "points": 3, "created_at": now},
        {"id": 2, "label": "Flowers", "category": "effort", "points": 5, "created_at": now},
        {"id": 3, "label": "Plans a date", "category": "consistency", "points": 4, "created_at": now},
        {"id": 4, "label": "Shows respect", "category": "respect", "points": 4, "created_at": now},
        {"id": 5, "label": "Great time together", "category": "fun", "points": 3, "created_at": now},
        {"id": 6, "label": "Late reply", "category": "communication", "points": -2, "created_at": now},
        {"id": 7, "label": "Cancelled plans", "category": "consistency", "points": -4, "created_at": now},
        {"id": 8, "label": "Disrespectful behavior", "category": "respect", "points": -6, "created_at": now},
    ]
    return pd.DataFrame(defaults, columns=ACTION_COLUMNS)


def default_settings() -> pd.DataFrame:
    rows: list[dict] = []
    for option in RELATIONSHIP_STATUS_OPTIONS:
        rows.append(
            {
                "scope": "relationship_status",
                "option": option,
                "points": int(RELATIONSHIP_STATUS_DEFAULT_POINTS[option]),
            }
        )
    for option in LOOKING_FOR_OPTIONS:
        rows.append(
            {
                "scope": "looking_for",
                "option": option,
                "points": int(LOOKING_FOR_DEFAULT_POINTS[option]),
            }
        )

    for scope_key, default_points in SPICY_SETTINGS_DEFAULT_POINTS.items():
        rows.append(
            {
                "scope": scope_key,
                "option": "default",
                "points": int(default_points),
            }
        )

    return pd.DataFrame(rows, columns=SETTINGS_COLUMNS)


def default_sins() -> pd.DataFrame:
    now = datetime.utcnow().isoformat(timespec="seconds")
    defaults = [
        {"id": 1, "label": "Ignored message", "life_percent": 10, "created_at": now},
        {"id": 2, "label": "Last-minute cancel", "life_percent": 20, "created_at": now},
        {"id": 3, "label": "Dishonesty", "life_percent": 35, "created_at": now},
    ]
    return pd.DataFrame(defaults, columns=SIN_COLUMNS)


def normalize_candidates(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()

    if "effort" not in normalized.columns and "chemistry" in normalized.columns:
        normalized["effort"] = normalized["chemistry"]

    for column in CANDIDATE_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = 0 if column in POINT_CATEGORIES else None

    if "sins_life_remaining" not in df.columns:
        normalized["sins_life_remaining"] = 300
    if "sins_life_cap" not in df.columns:
        normalized["sins_life_cap"] = 300

    normalized["avatar"] = normalized["avatar"].fillna("🧑").astype(str)

    if "relationship_status" not in df.columns and "relationship_status_base" in df.columns:
        rel_lookup = {v: k for k, v in RELATIONSHIP_STATUS_DEFAULT_POINTS.items()}
        normalized["relationship_status"] = (
            pd.to_numeric(df["relationship_status_base"], errors="coerce")
            .map(rel_lookup)
            .fillna("It's complicated")
        )

    if "looking_for" not in df.columns and "looking_for_base" in df.columns:
        look_lookup = {v: k for k, v in LOOKING_FOR_DEFAULT_POINTS.items()}
        normalized["looking_for"] = (
            pd.to_numeric(df["looking_for_base"], errors="coerce")
            .map(look_lookup)
            .fillna("Not sure")
        )

    normalized["relationship_status"] = normalized["relationship_status"].fillna("It's complicated").astype(str)
    normalized["looking_for"] = normalized["looking_for"].fillna("Not sure").astype(str)

    normalized.loc[
        ~normalized["relationship_status"].isin(RELATIONSHIP_STATUS_OPTIONS),
        "relationship_status",
    ] = "It's complicated"
    normalized.loc[
        ~normalized["looking_for"].isin(LOOKING_FOR_OPTIONS),
        "looking_for",
    ] = "Not sure"

    for column in POINT_CATEGORIES:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce").fillna(0).astype(int)

    normalized["looks_base"] = pd.to_numeric(normalized["looks_base"], errors="coerce").fillna(0).astype(int)
    normalized["sins_life_remaining"] = (
        pd.to_numeric(normalized["sins_life_remaining"], errors="coerce").fillna(300).clip(lower=0, upper=300).astype(int)
    )
    normalized["sins_life_cap"] = (
        pd.to_numeric(normalized["sins_life_cap"], errors="coerce").fillna(300).clip(lower=0, upper=300).astype(int)
    )
    normalized["sins_life_remaining"] = normalized[["sins_life_remaining", "sins_life_cap"]].min(axis=1)

    def as_bool(value: object) -> bool:
        if isinstance(value, bool):
            return value
        if pd.isna(value):
            return False
        if isinstance(value, (int, float)):
            return bool(int(value))
        text = str(value).strip().lower()
        return text in {"1", "true", "yes", "y", "t"}

    for column in LEVEL_COLUMNS:
        normalized[column] = normalized[column].map(as_bool)

    # Legacy column kept for compatibility; Friend status is no longer used.
    normalized["friend_zone_unlocked"] = False

    normalized["id"] = pd.to_numeric(normalized["id"], errors="coerce").fillna(0).astype(int)
    return normalized[CANDIDATE_COLUMNS]


def normalize_actions(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in ACTION_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = None

    normalized["id"] = pd.to_numeric(normalized["id"], errors="coerce").fillna(0).astype(int)
    normalized["points"] = pd.to_numeric(normalized["points"], errors="coerce").fillna(0).astype(int)
    normalized["category"] = normalized["category"].astype(str)
    normalized = normalized[normalized["category"].isin(POINT_CATEGORIES.keys())]
    return normalized[ACTION_COLUMNS]


def normalize_settings(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in SETTINGS_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = None

    normalized["scope"] = normalized["scope"].astype(str)
    normalized["option"] = normalized["option"].astype(str)
    normalized["points"] = pd.to_numeric(normalized["points"], errors="coerce").fillna(0).astype(int)

    allowed_scopes = {
        "relationship_status",
        "looking_for",
        "spicy_foreplay",
        "spicy_connection_strength",
        "spicy_orgasm_count",
        "spicy_orgasm_intensity",
    }
    normalized = normalized[normalized["scope"].isin(allowed_scopes)]
    return normalized[SETTINGS_COLUMNS]


def normalize_spicy_events(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in SPICY_EVENT_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = 0 if column not in {"created_at", "happened_at", "extra_reason"} else None

    normalized["id"] = pd.to_numeric(normalized["id"], errors="coerce").fillna(0).astype(int)
    normalized["candidate_id"] = pd.to_numeric(normalized["candidate_id"], errors="coerce").fillna(0).astype(int)
    normalized["foreplay"] = pd.to_numeric(normalized["foreplay"], errors="coerce").fillna(0).astype(int)
    normalized["connection_strength"] = pd.to_numeric(
        normalized["connection_strength"], errors="coerce"
    ).fillna(0).astype(int)
    normalized["orgasm_count"] = pd.to_numeric(normalized["orgasm_count"], errors="coerce").fillna(0).astype(int)
    normalized["orgasm_intensity"] = pd.to_numeric(
        normalized["orgasm_intensity"], errors="coerce"
    ).fillna(0).astype(int)
    normalized["session_intensity"] = pd.to_numeric(
        normalized["session_intensity"], errors="coerce"
    ).fillna(0).astype(int)
    normalized["extra_points"] = pd.to_numeric(normalized["extra_points"], errors="coerce").fillna(0).astype(int)
    normalized["extra_reason"] = normalized["extra_reason"].fillna("").astype(str)
    normalized["points"] = pd.to_numeric(normalized["points"], errors="coerce").fillna(0).astype(int)
    return normalized[SPICY_EVENT_COLUMNS]


def normalize_sins(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in SIN_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = None

    normalized["id"] = pd.to_numeric(normalized["id"], errors="coerce").fillna(0).astype(int)
    normalized["label"] = normalized["label"].fillna("").astype(str)
    normalized["life_percent"] = pd.to_numeric(normalized["life_percent"], errors="coerce").fillna(0).astype(int)
    return normalized[SIN_COLUMNS]


def normalize_sin_events(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in SIN_EVENT_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = None

    normalized["id"] = pd.to_numeric(normalized["id"], errors="coerce").fillna(0).astype(int)
    normalized["candidate_id"] = pd.to_numeric(normalized["candidate_id"], errors="coerce").fillna(0).astype(int)
    normalized["sin_id"] = pd.to_numeric(normalized["sin_id"], errors="coerce").fillna(0).astype(int)
    normalized["sin_label"] = normalized["sin_label"].fillna("").astype(str)
    normalized["life_percent"] = pd.to_numeric(normalized["life_percent"], errors="coerce").fillna(0).astype(int)
    normalized["notes"] = normalized["notes"].fillna("").astype(str)
    return normalized[SIN_EVENT_COLUMNS]


def read_sins_storage() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not DATA_PATH.exists():
        return default_sins(), pd.DataFrame(columns=SIN_EVENT_COLUMNS)

    xls = pd.ExcelFile(DATA_PATH)
    if "sins" in xls.sheet_names:
        sins = pd.read_excel(DATA_PATH, sheet_name="sins")
    else:
        sins = default_sins()

    if "sin_events" in xls.sheet_names:
        sin_events = pd.read_excel(DATA_PATH, sheet_name="sin_events")
    else:
        sin_events = pd.DataFrame(columns=SIN_EVENT_COLUMNS)

    return normalize_sins(sins), normalize_sin_events(sin_events)


def build_point_maps(settings_df: pd.DataFrame) -> tuple[dict[str, int], dict[str, int]]:
    relationship_map = dict(RELATIONSHIP_STATUS_DEFAULT_POINTS)
    looking_for_map = dict(LOOKING_FOR_DEFAULT_POINTS)

    relationship_rows = settings_df[settings_df["scope"] == "relationship_status"]
    for _, row in relationship_rows.iterrows():
        relationship_map[str(row["option"])] = int(row["points"])

    looking_rows = settings_df[settings_df["scope"] == "looking_for"]
    for _, row in looking_rows.iterrows():
        looking_for_map[str(row["option"])] = int(row["points"])

    return relationship_map, looking_for_map


def build_spicy_points_map(settings_df: pd.DataFrame) -> dict[str, int]:
    spicy_map = dict(SPICY_SETTINGS_DEFAULT_POINTS)
    for scope_key in SPICY_SETTINGS_DEFAULT_POINTS:
        rows = settings_df[settings_df["scope"] == scope_key]
        if not rows.empty:
            spicy_map[scope_key] = int(rows.iloc[0]["points"])
    return spicy_map


def init_storage() -> None:
    candidates = pd.DataFrame(columns=CANDIDATE_COLUMNS)
    actions = default_actions()
    settings = default_settings()
    spicy_events = pd.DataFrame(columns=SPICY_EVENT_COLUMNS)
    sins = default_sins()
    sin_events = pd.DataFrame(columns=SIN_EVENT_COLUMNS)
    write_workbook(candidates, actions, settings, spicy_events, sins=sins, sin_events=sin_events)


def total_score(row: pd.Series, relationship_points: dict[str, int], looking_for_points: dict[str, int]) -> int:
    dynamic_points = sum(int(row[key]) for key in POINT_CATEGORIES)
    base_points = int(row["looks_base"])
    base_points += int(relationship_points.get(str(row["relationship_status"]), 0))
    base_points += int(looking_for_points.get(str(row["looking_for"]), 0))
    return int(dynamic_points + base_points)


def read_workbook() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not DATA_PATH.exists():
        return (
            pd.DataFrame(columns=CANDIDATE_COLUMNS),
            default_actions(),
            default_settings(),
            pd.DataFrame(columns=SPICY_EVENT_COLUMNS),
        )

    xls = pd.ExcelFile(DATA_PATH)
    if "candidates" in xls.sheet_names:
        candidates = pd.read_excel(DATA_PATH, sheet_name="candidates")
    else:
        candidates = pd.read_excel(DATA_PATH, sheet_name=xls.sheet_names[0])

    if "actions" in xls.sheet_names:
        actions = pd.read_excel(DATA_PATH, sheet_name="actions")
    else:
        actions = default_actions()

    if "settings" in xls.sheet_names:
        settings = pd.read_excel(DATA_PATH, sheet_name="settings")
    else:
        settings = default_settings()

    if "spicy_events" in xls.sheet_names:
        spicy_events = pd.read_excel(DATA_PATH, sheet_name="spicy_events")
    else:
        spicy_events = pd.DataFrame(columns=SPICY_EVENT_COLUMNS)

    return (
        normalize_candidates(candidates),
        normalize_actions(actions),
        normalize_settings(settings),
        normalize_spicy_events(spicy_events),
    )


def write_workbook(
    candidates: pd.DataFrame,
    actions: pd.DataFrame,
    settings: pd.DataFrame,
    spicy_events: pd.DataFrame,
    sins: pd.DataFrame | None = None,
    sin_events: pd.DataFrame | None = None,
) -> None:
    existing_sins, existing_sin_events = read_sins_storage()
    if sins is None:
        sins = existing_sins
    if sin_events is None:
        sin_events = existing_sin_events

    with pd.ExcelWriter(DATA_PATH, engine="openpyxl", mode="w") as writer:
        normalize_candidates(candidates).to_excel(writer, sheet_name="candidates", index=False)
        normalize_actions(actions).to_excel(writer, sheet_name="actions", index=False)
        normalize_settings(settings).to_excel(writer, sheet_name="settings", index=False)
        normalize_spicy_events(spicy_events).to_excel(writer, sheet_name="spicy_events", index=False)
        normalize_sins(sins).to_excel(writer, sheet_name="sins", index=False)
        normalize_sin_events(sin_events).to_excel(writer, sheet_name="sin_events", index=False)


def import_workbook_bytes(file_bytes: bytes) -> tuple[bool, str]:
    try:
        xls = pd.ExcelFile(BytesIO(file_bytes))

        if "candidates" in xls.sheet_names:
            candidates = pd.read_excel(xls, sheet_name="candidates")
        elif xls.sheet_names:
            candidates = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
        else:
            candidates = pd.DataFrame(columns=CANDIDATE_COLUMNS)

        if "actions" in xls.sheet_names:
            actions = pd.read_excel(xls, sheet_name="actions")
        else:
            actions = default_actions()

        if "settings" in xls.sheet_names:
            settings = pd.read_excel(xls, sheet_name="settings")
        else:
            settings = default_settings()

        if "spicy_events" in xls.sheet_names:
            spicy_events = pd.read_excel(xls, sheet_name="spicy_events")
        else:
            spicy_events = pd.DataFrame(columns=SPICY_EVENT_COLUMNS)

        if "sins" in xls.sheet_names:
            sins = pd.read_excel(xls, sheet_name="sins")
        else:
            sins = default_sins()

        if "sin_events" in xls.sheet_names:
            sin_events = pd.read_excel(xls, sheet_name="sin_events")
        else:
            sin_events = pd.DataFrame(columns=SIN_EVENT_COLUMNS)

        write_workbook(candidates, actions, settings, spicy_events, sins=sins, sin_events=sin_events)
        return True, "Data imported successfully."
    except Exception as exc:
        return False, f"Import failed: {exc}"


def insert_candidate(payload: dict) -> None:
    candidates, actions, settings, spicy_events = read_workbook()
    next_id = int(candidates["id"].max()) + 1 if not candidates.empty else 1

    row = {
        "id": next_id,
        "name": payload["name"],
        "avatar": payload["avatar"],
        "dating_since": payload["dating_since"],
        "communication": 0,
        "effort": 0,
        "respect": 0,
        "consistency": 0,
        "future_fit": 0,
        "fun": 0,
        "spicy_time": 0,
        "extra": 0,
        "looks_base": payload["looks_base"],
        "relationship_status": payload["relationship_status"],
        "looking_for": payload["looking_for"],
        "friend_zone_unlocked": False,
        "dating_zone_unlocked": False,
        "sleeping_together_unlocked": False,
        "relationship_zone_unlocked": False,
        "sins_life_remaining": 300,
        "sins_life_cap": 300,
        "red_flags": payload["red_flags"],
        "notes": payload["notes"],
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
    }

    updated = pd.concat([candidates, pd.DataFrame([row])], ignore_index=True)
    write_workbook(updated, actions, settings, spicy_events)


def insert_action(payload: dict) -> None:
    candidates, actions, settings, spicy_events = read_workbook()
    next_id = int(actions["id"].max()) + 1 if not actions.empty else 1

    row = {
        "id": next_id,
        "label": payload["label"],
        "category": payload["category"],
        "points": payload["points"],
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
    }

    updated = pd.concat([actions, pd.DataFrame([row])], ignore_index=True)
    write_workbook(candidates, updated, settings, spicy_events)


def delete_action(action_id: int) -> None:
    candidates, actions, settings, spicy_events = read_workbook()
    updated = actions[actions["id"] != action_id].copy()
    write_workbook(candidates, updated, settings, spicy_events)


def apply_action(candidate_id: int, action_id: int) -> None:
    candidates, actions, settings, spicy_events = read_workbook()
    action_row = actions[actions["id"] == action_id]
    if action_row.empty:
        return

    category = str(action_row.iloc[0]["category"])
    points = int(action_row.iloc[0]["points"])

    idx = candidates.index[candidates["id"] == candidate_id]
    if len(idx) == 0 or category not in POINT_CATEGORIES:
        return

    current_value = int(candidates.loc[idx[0], category])
    candidates.loc[idx[0], category] = current_value + points
    write_workbook(candidates, actions, settings, spicy_events)


def add_spicy_rating(
    candidate_id: int,
    happened_at: str,
    foreplay: int,
    connection_strength: int,
    orgasm_count: int,
    orgasm_intensity: int,
    session_intensity: int,
    extra_points: int,
    extra_reason: str,
) -> int:
    candidates, actions, settings, spicy_events = read_workbook()
    idx = candidates.index[candidates["id"] == candidate_id]
    if len(idx) == 0:
        return 0

    spicy_map = build_spicy_points_map(settings)
    raw_spicy_points = int(
        (foreplay * spicy_map["spicy_foreplay"])
        + (connection_strength * spicy_map["spicy_connection_strength"])
        + (orgasm_count * spicy_map["spicy_orgasm_count"])
        + (orgasm_intensity * spicy_map["spicy_orgasm_intensity"])
    )
    spicy_points = int(round(raw_spicy_points / SPICY_SCORE_DIVISOR))
    spicy_points = max(-SPICY_SCORE_CAP, min(SPICY_SCORE_CAP, spicy_points))
    total_points = spicy_points + int(extra_points)

    next_event_id = int(spicy_events["id"].max()) + 1 if not spicy_events.empty else 1
    event_row = {
        "id": next_event_id,
        "candidate_id": int(candidate_id),
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
        "happened_at": happened_at,
        "foreplay": int(foreplay),
        "connection_strength": int(connection_strength),
        "orgasm_count": int(orgasm_count),
        "orgasm_intensity": int(orgasm_intensity),
        "session_intensity": int(session_intensity),
        "extra_points": int(extra_points),
        "extra_reason": extra_reason.strip(),
        "points": total_points,
    }
    updated_events = pd.concat([spicy_events, pd.DataFrame([event_row])], ignore_index=True)

    row_idx = idx[0]
    current_value = int(candidates.loc[row_idx, "spicy_time"])
    candidates.loc[row_idx, "spicy_time"] = current_value + spicy_points
    current_extra_value = int(candidates.loc[row_idx, "extra"])
    candidates.loc[row_idx, "extra"] = current_extra_value + int(extra_points)

    if int(extra_points) != 0 or extra_reason.strip():
        existing = str(candidates.loc[row_idx, "notes"]) if pd.notna(candidates.loc[row_idx, "notes"]) else ""
        reason_part = f" | {extra_reason.strip()}" if extra_reason.strip() else ""
        note_line = f"[{datetime.utcnow().isoformat(timespec='seconds')}] SPICY EXTRA {int(extra_points):+d}{reason_part}"
        candidates.loc[row_idx, "notes"] = f"{existing}\n{note_line}".strip()

    write_workbook(candidates, actions, settings, updated_events)
    return total_points


def add_extra_points(candidate_id: int, points: int, reason: str) -> tuple[bool, str]:
    candidates, actions, settings, spicy_events = read_workbook()
    idx = candidates.index[candidates["id"] == candidate_id]
    if len(idx) == 0:
        return False, "Person not found."

    row_idx = idx[0]
    current_value = int(candidates.loc[row_idx, "extra"])
    candidates.loc[row_idx, "extra"] = current_value + int(points)

    if reason.strip():
        existing = str(candidates.loc[row_idx, "notes"]) if pd.notna(candidates.loc[row_idx, "notes"]) else ""
        timestamp = datetime.utcnow().isoformat(timespec="seconds")
        extra_note = f"[{timestamp}] EXTRA {points:+d}: {reason.strip()}"
        candidates.loc[row_idx, "notes"] = f"{existing}\n{extra_note}".strip()

    write_workbook(candidates, actions, settings, spicy_events)
    return True, f"Added {points:+d} extra points."


def update_candidate_notes(candidate_id: int, red_flags: str, notes: str) -> None:
    candidates, actions, settings, spicy_events = read_workbook()
    idx = candidates.index[candidates["id"] == candidate_id]
    if len(idx) == 0:
        return

    candidates.loc[idx[0], "red_flags"] = red_flags
    candidates.loc[idx[0], "notes"] = notes
    write_workbook(candidates, actions, settings, spicy_events)


def update_candidate_base_points(
    candidate_id: int,
    looks_base: int,
    relationship_status: str,
    looking_for: str,
) -> None:
    candidates, actions, settings, spicy_events = read_workbook()
    idx = candidates.index[candidates["id"] == candidate_id]
    if len(idx) == 0:
        return

    candidates.loc[idx[0], "looks_base"] = int(looks_base)
    candidates.loc[idx[0], "relationship_status"] = relationship_status
    candidates.loc[idx[0], "looking_for"] = looking_for
    write_workbook(candidates, actions, settings, spicy_events)


def update_global_point_settings(settings_payload: dict[str, dict[str, int]]) -> None:
    candidates, actions, current_settings, spicy_events = read_workbook()
    rows: list[dict] = []

    relationship_values = settings_payload.get("relationship_status", {})
    for option in RELATIONSHIP_STATUS_OPTIONS:
        rows.append(
            {
                "scope": "relationship_status",
                "option": option,
                "points": int(relationship_values.get(option, RELATIONSHIP_STATUS_DEFAULT_POINTS[option])),
            }
        )

    looking_values = settings_payload.get("looking_for", {})
    for option in LOOKING_FOR_OPTIONS:
        rows.append(
            {
                "scope": "looking_for",
                "option": option,
                "points": int(looking_values.get(option, LOOKING_FOR_DEFAULT_POINTS[option])),
            }
        )

    spicy_rows = current_settings[
        current_settings["scope"].isin(SPICY_SETTINGS_DEFAULT_POINTS.keys())
    ].copy()
    if spicy_rows.empty:
        defaults_df = default_settings()
        spicy_rows = defaults_df[defaults_df["scope"].isin(SPICY_SETTINGS_DEFAULT_POINTS.keys())].copy()

    merged_settings = pd.concat([pd.DataFrame(rows, columns=SETTINGS_COLUMNS), spicy_rows], ignore_index=True)
    write_workbook(candidates, actions, merged_settings, spicy_events)


def update_spicy_point_settings(spicy_payload: dict[str, int]) -> None:
    candidates, actions, current_settings, spicy_events = read_workbook()

    rel_rows = current_settings[current_settings["scope"] == "relationship_status"].copy()
    look_rows = current_settings[current_settings["scope"] == "looking_for"].copy()

    if rel_rows.empty or look_rows.empty:
        defaults_df = default_settings()
        if rel_rows.empty:
            rel_rows = defaults_df[defaults_df["scope"] == "relationship_status"].copy()
        if look_rows.empty:
            look_rows = defaults_df[defaults_df["scope"] == "looking_for"].copy()

    spicy_rows: list[dict] = []
    for scope_key, default_value in SPICY_SETTINGS_DEFAULT_POINTS.items():
        spicy_rows.append(
            {
                "scope": scope_key,
                "option": "default",
                "points": int(spicy_payload.get(scope_key, default_value)),
            }
        )

    merged_settings = pd.concat(
        [
            rel_rows[SETTINGS_COLUMNS],
            look_rows[SETTINGS_COLUMNS],
            pd.DataFrame(spicy_rows, columns=SETTINGS_COLUMNS),
        ],
        ignore_index=True,
    )
    write_workbook(candidates, actions, merged_settings, spicy_events)


def set_level_state(candidate_id: int, level: str, unlock: bool) -> tuple[bool, str]:
    candidates, actions, settings, spicy_events = read_workbook()
    idx = candidates.index[candidates["id"] == candidate_id]
    if len(idx) == 0:
        return False, "Person not found."

    row_idx = idx[0]
    dating_unlocked = bool(candidates.loc[row_idx, "dating_zone_unlocked"])
    sleeping_unlocked = bool(candidates.loc[row_idx, "sleeping_together_unlocked"])
    relationship_unlocked = bool(candidates.loc[row_idx, "relationship_zone_unlocked"])

    if level == "friend":
        return False, "Friend status is not used."

    if unlock:
        if level == "dating":
            if dating_unlocked:
                return False, "Dating zone already unlocked."
            candidates.loc[row_idx, "dating_zone_unlocked"] = True
            write_workbook(candidates, actions, settings, spicy_events)
            return True, "Dating zone unlocked."

        if level == "sleeping":
            if not dating_unlocked:
                return False, "Unlock Dating zone first."
            if sleeping_unlocked:
                return False, "Sleeping together zone already unlocked."
            candidates.loc[row_idx, "sleeping_together_unlocked"] = True
            write_workbook(candidates, actions, settings, spicy_events)
            return True, "Sleeping together zone unlocked."

        if level == "relationship":
            if not dating_unlocked:
                return False, "Unlock Dating zone first."
            if relationship_unlocked:
                return False, "Relationship zone already unlocked."
            candidates.loc[row_idx, "relationship_zone_unlocked"] = True
            write_workbook(candidates, actions, settings, spicy_events)
            return True, "Relationship zone unlocked."

    if level == "relationship":
        if not relationship_unlocked:
            return False, "Relationship zone already locked."
        candidates.loc[row_idx, "relationship_zone_unlocked"] = False
        write_workbook(candidates, actions, settings, spicy_events)
        return True, "Relationship zone locked."

    if level == "sleeping":
        if not sleeping_unlocked:
            return False, "Sleeping together zone already locked."
        candidates.loc[row_idx, "sleeping_together_unlocked"] = False
        write_workbook(candidates, actions, settings, spicy_events)
        return True, "Sleeping together zone locked."

    if level == "dating":
        if not dating_unlocked:
            return False, "Dating zone already locked."
        candidates.loc[row_idx, "dating_zone_unlocked"] = False
        candidates.loc[row_idx, "sleeping_together_unlocked"] = False
        candidates.loc[row_idx, "relationship_zone_unlocked"] = False
        write_workbook(candidates, actions, settings, spicy_events)
        return True, "Dating zone locked. Dependent levels were also locked."

    return False, "Unknown level."


def load_candidates() -> pd.DataFrame:
    df, _, settings, _ = read_workbook()

    if df.empty:
        return df

    relationship_points, looking_for_points = build_point_maps(settings)
    df["base_looks_points"] = df["looks_base"].astype(int)
    df["base_relationship_points"] = df["relationship_status"].map(relationship_points).fillna(0).astype(int)
    df["base_looking_for_points"] = df["looking_for"].map(looking_for_points).fillna(0).astype(int)
    df["score"] = df.apply(total_score, axis=1, args=(relationship_points, looking_for_points))
    df = df.sort_values(by=["score", "created_at"], ascending=[False, False]).reset_index(drop=True)
    df.index = df.index + 1
    return df


def load_actions() -> pd.DataFrame:
    _, actions, _, _ = read_workbook()
    if actions.empty:
        return actions
    return actions.sort_values(by=["points", "created_at"], ascending=[False, False]).reset_index(drop=True)


def load_global_point_settings() -> tuple[dict[str, int], dict[str, int]]:
    _, _, settings, _ = read_workbook()
    return build_point_maps(settings)


def load_spicy_point_settings() -> dict[str, int]:
    _, _, settings, _ = read_workbook()
    return build_spicy_points_map(settings)


def load_spicy_events_for_candidate(candidate_id: int) -> pd.DataFrame:
    _, _, _, spicy_events = read_workbook()
    filtered = spicy_events[spicy_events["candidate_id"] == candidate_id].copy()
    if filtered.empty:
        return filtered
    return filtered.sort_values(by=["created_at", "id"], ascending=[False, False]).reset_index(drop=True)


def load_sins() -> pd.DataFrame:
    sins, _ = read_sins_storage()
    if sins.empty:
        return sins
    return sins.sort_values(by=["life_percent", "created_at"], ascending=[False, False]).reset_index(drop=True)


def load_sin_events_for_candidate(candidate_id: int) -> pd.DataFrame:
    _, sin_events = read_sins_storage()
    filtered = sin_events[sin_events["candidate_id"] == candidate_id].copy()
    if filtered.empty:
        return filtered
    return filtered.sort_values(by=["created_at", "id"], ascending=[False, False]).reset_index(drop=True)


def insert_sin_rule(label: str, life_percent: int) -> tuple[bool, str]:
    clean_label = label.strip()
    if not clean_label:
        return False, "Sin label is required."

    sins, sin_events = read_sins_storage()
    next_id = int(sins["id"].max()) + 1 if not sins.empty else 1
    row = {
        "id": next_id,
        "label": clean_label,
        "life_percent": int(life_percent),
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
    }
    updated_sins = pd.concat([sins, pd.DataFrame([row])], ignore_index=True)

    candidates, actions, settings, spicy_events = read_workbook()
    write_workbook(candidates, actions, settings, spicy_events, sins=updated_sins, sin_events=sin_events)
    return True, "Sin rule added."


def delete_sin_rule(sin_id: int) -> tuple[bool, str]:
    sins, sin_events = read_sins_storage()
    if sins[sins["id"] == sin_id].empty:
        return False, "Sin rule not found."

    updated_sins = sins[sins["id"] != sin_id].copy()
    candidates, actions, settings, spicy_events = read_workbook()
    write_workbook(candidates, actions, settings, spicy_events, sins=updated_sins, sin_events=sin_events)
    return True, "Sin rule deleted."


def apply_sin(candidate_id: int, sin_id: int, notes: str) -> tuple[bool, str]:
    candidates, actions, settings, spicy_events = read_workbook()
    sins, sin_events = read_sins_storage()

    sin_rows = sins[sins["id"] == sin_id]
    if sin_rows.empty:
        return False, "Sin rule not found."

    idx = candidates.index[candidates["id"] == candidate_id]
    if len(idx) == 0:
        return False, "Person not found."

    sin_row = sin_rows.iloc[0]
    penalty = max(0, int(sin_row["life_percent"]))
    row_idx = idx[0]
    current_life = int(candidates.loc[row_idx, "sins_life_remaining"])
    current_cap = int(candidates.loc[row_idx, "sins_life_cap"])
    applied_penalty = min(current_life, penalty)
    new_life = max(0, current_life - penalty)

    hearts_before = (current_life + 99) // 100 if current_life > 0 else 0
    hearts_after = (new_life + 99) // 100 if new_life > 0 else 0
    hearts_lost = max(0, hearts_before - hearts_after)
    new_cap = max(0, current_cap - (hearts_lost * 100))

    candidates.loc[row_idx, "sins_life_cap"] = new_cap
    candidates.loc[row_idx, "sins_life_remaining"] = new_life

    next_event_id = int(sin_events["id"].max()) + 1 if not sin_events.empty else 1
    event_row = {
        "id": next_event_id,
        "candidate_id": int(candidate_id),
        "sin_id": int(sin_id),
        "sin_label": str(sin_row["label"]),
        "life_percent": int(applied_penalty),
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
        "notes": notes.strip(),
    }
    updated_sin_events = pd.concat([sin_events, pd.DataFrame([event_row])], ignore_index=True)

    write_workbook(
        candidates,
        actions,
        settings,
        spicy_events,
        sins=sins,
        sin_events=updated_sin_events,
    )
    cap_note = f" (heart lost: -{hearts_lost})" if hearts_lost > 0 else ""
    return True, f"Applied sin: -{applied_penalty}% life.{cap_note}"


def delete_sin_event(event_id: int) -> tuple[bool, str]:
    candidates, actions, settings, spicy_events = read_workbook()
    sins, sin_events = read_sins_storage()

    event_rows = sin_events[sin_events["id"] == event_id]
    if event_rows.empty:
        return False, "Sin event not found."

    event = event_rows.iloc[0]
    candidate_id = int(event["candidate_id"])
    life_percent = max(0, int(event["life_percent"]))

    idx = candidates.index[candidates["id"] == candidate_id]
    if len(idx) > 0:
        row_idx = idx[0]
        current_life = int(candidates.loc[row_idx, "sins_life_remaining"])
        life_cap = int(candidates.loc[row_idx, "sins_life_cap"])
        candidates.loc[row_idx, "sins_life_remaining"] = min(life_cap, current_life + life_percent)

    updated_sin_events = sin_events[sin_events["id"] != event_id].copy()
    write_workbook(
        candidates,
        actions,
        settings,
        spicy_events,
        sins=sins,
        sin_events=updated_sin_events,
    )
    return True, f"Sin event #{event_id} removed and life restored."


def necromancer_restore_heart(candidate_id: int, super_deed: str) -> tuple[bool, str]:
    deed = super_deed.strip()
    if not deed:
        return False, "Describe what super thing he did first."

    candidates, actions, settings, spicy_events = read_workbook()
    sins, sin_events = read_sins_storage()

    idx = candidates.index[candidates["id"] == candidate_id]
    if len(idx) == 0:
        return False, "Person not found."

    row_idx = idx[0]
    cap = int(candidates.loc[row_idx, "sins_life_cap"])
    life = int(candidates.loc[row_idx, "sins_life_remaining"])
    if cap >= 300:
        return False, "No lost hearts to restore."

    new_cap = min(300, cap + 100)
    new_life = min(new_cap, life + 100)
    candidates.loc[row_idx, "sins_life_cap"] = new_cap
    candidates.loc[row_idx, "sins_life_remaining"] = new_life

    existing_notes = str(candidates.loc[row_idx, "notes"]) if pd.notna(candidates.loc[row_idx, "notes"]) else ""
    timestamp = datetime.utcnow().isoformat(timespec="seconds")
    note_line = f"[{timestamp}] NECROMANCER +1 heart: {deed}"
    candidates.loc[row_idx, "notes"] = f"{existing_notes}\n{note_line}".strip()

    write_workbook(
        candidates,
        actions,
        settings,
        spicy_events,
        sins=sins,
        sin_events=sin_events,
    )
    return True, "Necromancer restored one heart."


def add_points_per_day_metrics(df: pd.DataFrame) -> pd.DataFrame:
    metrics = df.copy()
    today = pd.Timestamp.now().normalize()

    dating_since = pd.to_datetime(metrics["dating_since"], errors="coerce")
    days_known = (today - dating_since.dt.normalize()).dt.days + 1
    metrics["days_known"] = days_known.fillna(1).clip(lower=1).astype(int)
    metrics["points_per_day"] = (metrics["score"] / metrics["days_known"]).round(3)
    return metrics


def render_board_ranking(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No players on the board yet.")
        return

    max_score = int(df["score"].max())
    board_cells = max(1, max_score)
    columns_count = 10 if board_cells >= 10 else max(1, board_cells)
    board_rows = int(math.ceil(board_cells / columns_count))

    # Group player markers by board cell.
    cells: dict[int, list[str]] = {i: [] for i in range(board_cells)}
    for _, row in df.iterrows():
        score = int(row["score"])
        # Scores <= 0 stay on first tile; positive scores map directly to tile number.
        position = min(board_cells - 1, max(0, score - 1))
        avatar = str(row["avatar"]) if pd.notna(row["avatar"]) else "🧑"
        safe_name = str(row["name"])
        cells[position].append(f"<span title='{safe_name} ({score})'>{avatar}</span>")

    trail_order: list[int] = []
    for r in range(board_rows):
        start_idx = r * columns_count
        end_idx = min(start_idx + columns_count, board_cells)
        row_indexes = [i for i in range(start_idx, end_idx)]
        if r % 2 == 1:
            row_indexes.reverse()
        trail_order.extend(row_indexes)

    trail_rank = {cell_index: rank for rank, cell_index in enumerate(trail_order)}

    cell_html = []
    for idx in range(board_cells):
        pawn_items = "".join(f"<div class='pawn'>{pawn}</div>" for pawn in cells[idx])
        cell_number = trail_rank[idx] + 1
        tile_rng = random.Random(idx + 137)
        tile_icon = tile_rng.choice(["🍄", "🌸"])
        start_tag = ""
        if cell_number == 1:
            start_tag = "<div class='milestone'>START</div>"

        cell_html.append(
            "<div class='board-cell'>"
            f"<div class='cell-id'>Tile {cell_number}</div>"
            f"<div class='mushrooms'>{tile_icon}</div>"
            f"{start_tag}"
            f"<div class='pawn-stack'>{pawn_items}</div>"
            "</div>"
        )

    board_html = "".join(cell_html)

    st.markdown(
        f"""
        <style>
        .board-wrap {{
            border: 1px solid #d5c6a1;
            border-radius: 14px;
            padding: 12px;
            background: linear-gradient(180deg, #fff8e7 0%, #f3ecd6 100%);
        }}
        .board-grid {{
            display: grid;
            grid-template-columns: repeat({columns_count}, minmax(56px, 1fr));
            gap: 6px;
        }}
        .board-cell {{
            border: 1px solid #ccb88f;
            border-radius: 9px;
            min-height: 68px;
            padding: 4px;
            background: radial-gradient(circle at top right, #fff6dc 0%, #f8eed0 55%, #efe0b9 100%);
        }}
        .cell-id {{
            font-size: 10px;
            color: #5f4a2f;
            margin-bottom: 1px;
            font-weight: 600;
        }}
        .mushrooms {{
            font-size: 11px;
            margin-bottom: 2px;
        }}
        .milestone {{
            font-size: 9px;
            display: inline-block;
            border-radius: 999px;
            padding: 1px 5px;
            background: #e4d4ab;
            color: #4d3a23;
            border: 1px solid #c7ae7b;
            margin-bottom: 2px;
        }}
        .pawn-stack {{
            display: flex;
            flex-wrap: wrap;
            gap: 3px;
        }}
        .pawn {{
            font-size: 19px;
            line-height: 1;
            border-radius: 7px;
            background: #f5f0df;
            padding: 2px 4px;
            color: #3d2d1d;
            border: 1px solid #d1bd91;
        }}
        .board-scale {{
            margin-top: 8px;
            color: #5f4a2f;
            font-size: 12px;
        }}
        </style>
        <div class="board-wrap">
            <div class="board-grid">{board_html}</div>
            <div class="board-scale">Mushroom trail: {board_cells} tiles (1 tile = 1 point)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def delete_candidate(candidate_id: int) -> None:
    candidates, actions, settings, spicy_events = read_workbook()
    sins, sin_events = read_sins_storage()
    updated = candidates[candidates["id"] != candidate_id].copy()
    updated_events = spicy_events[spicy_events["candidate_id"] != candidate_id].copy()
    updated_sin_events = sin_events[sin_events["candidate_id"] != candidate_id].copy()
    write_workbook(updated, actions, settings, updated_events, sins=sins, sin_events=updated_sin_events)


def delete_spicy_event(event_id: int) -> tuple[bool, str]:
    candidates, actions, settings, spicy_events = read_workbook()
    event_row = spicy_events[spicy_events["id"] == event_id]
    if event_row.empty:
        return False, "Event not found."

    event = event_row.iloc[0]
    candidate_id = int(event["candidate_id"])
    extra_points = int(event["extra_points"])
    spicy_core_points = int(event["points"]) - extra_points

    idx = candidates.index[candidates["id"] == candidate_id]
    if len(idx) > 0:
        row_idx = idx[0]
        candidates.loc[row_idx, "spicy_time"] = int(candidates.loc[row_idx, "spicy_time"]) - spicy_core_points
        candidates.loc[row_idx, "extra"] = int(candidates.loc[row_idx, "extra"]) - extra_points

    updated_events = spicy_events[spicy_events["id"] != event_id].copy()
    write_workbook(candidates, actions, settings, updated_events)
    return True, f"Event #{event_id} deleted."


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="💘", layout="wide")
    if not DATA_PATH.exists():
        init_storage()

    st.title(APP_TITLE)
    st.caption("Dating can be an emotional whirlpool where details get lost and feelings cloud judgment. Dating'n'Rating brings logic and math back into the equation. Track your dating journey using objective scoring and custom action tiles — because data doesn't forget, and numbers don't lie.")

    col_form, col_rank = st.columns([1, 1.6])

    relationship_point_map, looking_for_point_map = load_global_point_settings()
    spicy_point_map = load_spicy_point_settings()

    with st.sidebar:
        with st.expander("Data backup (download/upload)", expanded=False):
            if not DATA_PATH.exists():
                init_storage()

            st.caption(
                "Download your current data file or upload an existing one to restore full state (people, tiles, parameters, events)."
            )
            try:
                download_payload = DATA_PATH.read_bytes() if DATA_PATH.exists() else b""
            except Exception:
                download_payload = b""

            if not download_payload:
                st.warning("No local file available to download yet.")
            else:
                st.caption(f"File ready: data.xlsx ({len(download_payload)} bytes)")

            st.download_button(
                "Download data.xlsx",
                data=download_payload,
                file_name="data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                disabled=not bool(download_payload),
                key="download_data_xlsx",
                on_click="ignore",
            )

            uploaded_data_file = st.file_uploader(
                "Upload data.xlsx",
                type=["xlsx"],
                accept_multiple_files=False,
                key="data_upload_file",
            )
            if st.button("Import uploaded file", use_container_width=True, type="secondary"):
                if uploaded_data_file is None:
                    st.info("Choose an .xlsx file first.")
                else:
                    ok, msg = import_workbook_bytes(uploaded_data_file.getvalue())
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown("---")

        with st.expander("Add Person", expanded=False):
            with st.form("add_candidate", clear_on_submit=True):
                name = st.text_input("Name", max_chars=60)
                avatar = st.selectbox("Icon", AVATAR_OPTIONS, index=0)
                dating_since = st.date_input("Dating since")

                st.markdown("### Base profile points")
                looks_base = st.slider("Looks", min_value=-2, max_value=10, value=5, step=1)
                relationship_status_label = st.selectbox(
                    "Relationship status",
                    options=RELATIONSHIP_STATUS_OPTIONS,
                    format_func=lambda opt: f"{opt} ({relationship_point_map.get(opt, 0):+d})",
                )
                looking_for_label = st.selectbox(
                    "Looking for",
                    options=LOOKING_FOR_OPTIONS,
                    format_func=lambda opt: f"{opt} ({looking_for_point_map.get(opt, 0):+d})",
                )

                red_flags = st.text_area("Red Flags")
                notes = st.text_area("Notes")
                submitted = st.form_submit_button("Save")

                if submitted:
                    if not name.strip():
                        st.error("Name is required.")
                    else:
                        insert_candidate(
                            {
                                "name": name.strip(),
                                "avatar": avatar,
                                "dating_since": dating_since.isoformat(),
                                "looks_base": int(looks_base),
                                "relationship_status": relationship_status_label,
                                "looking_for": looking_for_label,
                                "red_flags": red_flags.strip(),
                                "notes": notes.strip(),
                            }
                        )
                        st.success("Saved.")
                        st.rerun()

        st.markdown("---")
        with st.expander("Global base points", expanded=False):
            with st.form("global_base_points"):
                st.caption("These values apply to everyone with a given status/looking-for option.")

                rel_inputs: dict[str, int] = {}
                for option in RELATIONSHIP_STATUS_OPTIONS:
                    rel_inputs[option] = int(
                        st.number_input(
                            f"Relationship status: {option}",
                            min_value=-30,
                            max_value=30,
                            value=int(relationship_point_map.get(option, RELATIONSHIP_STATUS_DEFAULT_POINTS[option])),
                            step=1,
                        )
                    )

                look_inputs: dict[str, int] = {}
                for option in LOOKING_FOR_OPTIONS:
                    look_inputs[option] = int(
                        st.number_input(
                            f"Looking for: {option}",
                            min_value=-30,
                            max_value=30,
                            value=int(looking_for_point_map.get(option, LOOKING_FOR_DEFAULT_POINTS[option])),
                            step=1,
                        )
                    )

                save_global_points = st.form_submit_button("Save global points")
                if save_global_points:
                    update_global_point_settings(
                        {
                            "relationship_status": rel_inputs,
                            "looking_for": look_inputs,
                        }
                    )
                    st.success("Global base points updated.")
                    st.rerun()

            with st.form("global_spicy_points"):
                st.caption("Spicy-time event weights used for each new spicy-time rating.")
                spicy_foreplay_points = st.number_input(
                    "Foreplay points per rating point",
                    min_value=-10,
                    max_value=10,
                    value=int(spicy_point_map.get("spicy_foreplay", SPICY_SETTINGS_DEFAULT_POINTS["spicy_foreplay"])),
                    step=1,
                )
                spicy_connection_points = st.number_input(
                    "Connection points per rating point",
                    min_value=-10,
                    max_value=10,
                    value=int(
                        spicy_point_map.get(
                            "spicy_connection_strength",
                            SPICY_SETTINGS_DEFAULT_POINTS["spicy_connection_strength"],
                        )
                    ),
                    step=1,
                )
                spicy_orgasm_count_points = st.number_input(
                    "Orgasm count points per orgasm",
                    min_value=-10,
                    max_value=10,
                    value=int(
                        spicy_point_map.get(
                            "spicy_orgasm_count",
                            SPICY_SETTINGS_DEFAULT_POINTS["spicy_orgasm_count"],
                        )
                    ),
                    step=1,
                )
                spicy_orgasm_intensity_points = st.number_input(
                    "Orgasm intensity points per rating point",
                    min_value=-10,
                    max_value=10,
                    value=int(
                        spicy_point_map.get(
                            "spicy_orgasm_intensity",
                            SPICY_SETTINGS_DEFAULT_POINTS["spicy_orgasm_intensity"],
                        )
                    ),
                    step=1,
                )

                save_spicy_points = st.form_submit_button("Save spicy-time points")
                if save_spicy_points:
                    update_spicy_point_settings(
                        {
                            "spicy_foreplay": int(spicy_foreplay_points),
                            "spicy_connection_strength": int(spicy_connection_points),
                            "spicy_orgasm_count": int(spicy_orgasm_count_points),
                            "spicy_orgasm_intensity": int(spicy_orgasm_intensity_points),
                        }
                    )
                    st.success("Spicy-time points updated.")
                    st.rerun()

        with st.expander("Point Rules", expanded=False):
            with st.form("add_action", clear_on_submit=True):
                action_label = st.text_input("Tile label", placeholder="e.g. Quick reply")
                action_category = st.selectbox(
                    "Category",
                    options=list(POINT_CATEGORIES.keys()),
                    format_func=lambda k: POINT_CATEGORIES[k],
                )
                action_points = st.number_input("Points", min_value=-20, max_value=50, value=3, step=1)
                add_action_submit = st.form_submit_button("Add tile")

                if add_action_submit:
                    if not action_label.strip():
                        st.error("Tile label is required.")
                    else:
                        insert_action(
                            {
                                "label": action_label.strip(),
                                "category": action_category,
                                "points": int(action_points),
                            }
                        )
                        st.success("Tile added.")
                        st.rerun()

            actions_df = load_actions()
            if not actions_df.empty:
                delete_options = {
                    f"{row['label']} ({row['points']} pts -> {POINT_CATEGORIES[str(row['category'])]})": int(row["id"])
                    for _, row in actions_df.iterrows()
                }
                selected_action = st.selectbox("Delete tile", list(delete_options.keys()))
                if st.button("Delete selected tile", type="secondary"):
                    delete_action(delete_options[selected_action])
                    st.warning("Tile deleted.")
                    st.rerun()

    with st.container():
        st.subheader("Ranking Board")
        df = load_candidates()
        actions_df = load_actions()

        if df.empty:
            st.info("No entries yet.")
            return

        board_points_mode = "Core connection"
        _, _, _, spicy_events_all = read_workbook()
        spicy_chart_mode = "Total spicy-time points"

        board_df = df.copy()
        if board_points_mode == "Core connection":
            board_df["board_score"] = board_df["score"] - board_df["spicy_time"]
        elif board_points_mode == "Intimate connection":
            board_df["board_score"] = board_df["spicy_time"]
        else:
            board_df["board_score"] = board_df["score"]

        board_df["board_score"] = pd.to_numeric(board_df["board_score"], errors="coerce").fillna(0).astype(int)

        data_min_score = int(board_df["board_score"].min()) if not board_df.empty else 0
        data_max_score = int(board_df["board_score"].max()) if not board_df.empty else 0
        slider_min = min(-20, data_min_score)
        slider_max = max(20, data_max_score)
        min_filter_score = st.slider(
            "Minimum points for board",
            min_value=slider_min,
            max_value=slider_max,
            value=slider_min,
            step=1,
        )
        filtered = board_df[board_df["board_score"] >= min_filter_score].copy()
        filtered = add_points_per_day_metrics(filtered)

        board_ranking_df = filtered.copy()
        board_ranking_df["score"] = board_ranking_df["board_score"]
        render_board_ranking(board_ranking_df)

        if filtered.empty:
            st.info("No data for charts with the current filter.")
        else:
            chart_df = filtered[["name", "points_per_day", "days_known", "score", "spicy_time"]].copy()
            chart_df = chart_df.sort_values(by="points_per_day", ascending=False)

            chart_col_1, chart_col_2, chart_col_3 = st.columns(3, gap="large")

            with chart_col_1:
                st.caption("Points per day")
                st.bar_chart(chart_df.set_index("name")["points_per_day"], use_container_width=True)

            with chart_col_2:
                if spicy_chart_mode == "Total spicy-time points":
                    st.caption("Spicy-time points")
                    spicy_points_df = chart_df.sort_values(by="spicy_time", ascending=False)
                    st.bar_chart(spicy_points_df.set_index("name")["spicy_time"], use_container_width=True)
                else:
                    if spicy_events_all.empty:
                        st.caption("Spicy events")
                        st.info("No spicy events yet.")
                    else:
                        spicy_events_chart = (
                            spicy_events_all.groupby("candidate_id", as_index=False)
                            .agg(
                                spicy_sessions=("id", "count"),
                                avg_session_intensity=("session_intensity", "mean"),
                            )
                            .merge(df[["id", "name"]], left_on="candidate_id", right_on="id", how="left")
                        )
                        spicy_events_chart["name"] = spicy_events_chart["name"].fillna(
                            spicy_events_chart["candidate_id"].map(lambda value: f"#{int(value)}")
                        )
                        spicy_events_chart["avg_session_intensity"] = spicy_events_chart["avg_session_intensity"].round(2)

                        if spicy_chart_mode == "Spicy events count":
                            st.caption("Spicy events count")
                            spicy_events_chart = spicy_events_chart.sort_values(by="spicy_sessions", ascending=False)
                            st.bar_chart(spicy_events_chart.set_index("name")["spicy_sessions"], use_container_width=True)
                        else:
                            st.caption("Average spicy-session intensity")
                            spicy_events_chart = spicy_events_chart.sort_values(by="avg_session_intensity", ascending=False)
                            st.bar_chart(
                                spicy_events_chart.set_index("name")["avg_session_intensity"],
                                use_container_width=True,
                            )

            with chart_col_3:
                st.caption("Total score")
                score_df = chart_df.sort_values(by="score", ascending=False)
                st.bar_chart(score_df.set_index("name")["score"], use_container_width=True)

            st.markdown("### Full ranking table")
            raw_candidates, _, settings_for_table, _ = read_workbook()
            relationship_map_for_table, looking_for_map_for_table = build_point_maps(settings_for_table)
            ranking_table = raw_candidates.copy()
            ranking_table["base_looks_points"] = ranking_table["looks_base"].astype(int)
            ranking_table["base_relationship_points"] = (
                ranking_table["relationship_status"].map(relationship_map_for_table).fillna(0).astype(int)
            )
            ranking_table["base_looking_for_points"] = (
                ranking_table["looking_for"].map(looking_for_map_for_table).fillna(0).astype(int)
            )
            ranking_table["score"] = ranking_table.apply(
                total_score,
                axis=1,
                args=(relationship_map_for_table, looking_for_map_for_table),
            )
            ranking_table = ranking_table[
                [
                    "id",
                    "created_at",
                    "name",
                    "score",
                    "communication",
                    "effort",
                    "respect",
                    "consistency",
                    "future_fit",
                    "fun",
                    "spicy_time",
                    "extra",
                    "relationship_status",
                    "looking_for",
                    "base_looks_points",
                    "base_relationship_points",
                    "base_looking_for_points",
                ]
            ].sort_values(by=["created_at", "id"], ascending=[False, False])
            st.caption("One row = one saved candidate record (kept separately, no merging).")
            st.dataframe(ranking_table, use_container_width=True)

        with st.container(border=True):
            st.markdown(
                """
                <style>
                div[data-testid="stVerticalBlockBorderWrapper"]:has(.control-center-anchor) {
                    background:
                        radial-gradient(120% 180% at 0% 0%, rgba(66, 211, 255, 0.18), rgba(0, 0, 0, 0) 60%),
                        radial-gradient(100% 160% at 100% 100%, rgba(79, 121, 255, 0.16), rgba(0, 0, 0, 0) 55%),
                        linear-gradient(145deg, #0e1522 0%, #121c2d 45%, #0a111d 100%);
                    border: 1px solid rgba(109, 189, 255, 0.55) !important;
                    border-radius: 14px;
                    box-shadow:
                        inset 0 0 0 1px rgba(185, 226, 255, 0.08),
                        0 8px 18px rgba(6, 12, 26, 0.45);
                }

                div[data-testid="stVerticalBlockBorderWrapper"]:has(.control-center-anchor) h1,
                div[data-testid="stVerticalBlockBorderWrapper"]:has(.control-center-anchor) h2,
                div[data-testid="stVerticalBlockBorderWrapper"]:has(.control-center-anchor) h3,
                div[data-testid="stVerticalBlockBorderWrapper"]:has(.control-center-anchor) p,
                div[data-testid="stVerticalBlockBorderWrapper"]:has(.control-center-anchor) label {
                    color: #e7f2ff !important;
                }

                div[data-testid="stVerticalBlockBorderWrapper"]:has(.control-center-anchor) [data-baseweb="select"] > div {
                    background-color: rgba(9, 18, 34, 0.78) !important;
                    border-color: rgba(116, 192, 255, 0.55) !important;
                }

                div[data-testid="stVerticalBlockBorderWrapper"]:has(.control-center-anchor) [data-baseweb="select"] div {
                    color: #e7f2ff !important;
                }

                .control-center-anchor {
                    display: none;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="control-center-anchor"></div>', unsafe_allow_html=True)
            st.markdown("### Control center")
            st.caption("Choose one person here to control statuses, points, spicy events, notes, and base profile in all sections below.")

            selectable_people = df.copy().sort_values(by=["score", "name"], ascending=[False, True])
            selectable_ids = selectable_people["id"].astype(int).tolist()
            if "global_person_id" not in st.session_state or int(st.session_state["global_person_id"]) not in selectable_ids:
                st.session_state["global_person_id"] = selectable_ids[0]

            st.markdown("**Choose person (global):**")
            card_columns = st.columns(3, gap="small")
            for idx, (_, person_row) in enumerate(selectable_people.iterrows()):
                person_id = int(person_row["id"])
                is_selected = person_id == int(st.session_state["global_person_id"])
                person_hearts_left = max(0, min(3, (int(person_row.get("sins_life_remaining", 300)) + 99) // 100))
                person_hearts_cap = max(0, min(3, int(person_row.get("sins_life_cap", 300)) // 100))
                person_hearts_ui = "❤" * person_hearts_left + "♡" * (3 - person_hearts_left)
                person_status = (
                    f"D {'✅' if bool(person_row['dating_zone_unlocked']) else '⬜'} | "
                    f"S {'✅' if bool(person_row['sleeping_together_unlocked']) else '⬜'} | "
                    f"R {'✅' if bool(person_row['relationship_zone_unlocked']) else '⬜'}"
                )

                with card_columns[idx % 3]:
                    card_border = "2px solid rgba(255, 125, 176, 0.75)" if is_selected else "1px solid rgba(140, 202, 255, 0.35)"
                    card_bg = (
                        "linear-gradient(135deg, rgba(120, 12, 64, 0.96), rgba(165, 22, 88, 0.96))"
                        if is_selected
                        else "rgba(7, 18, 34, 0.82)"
                    )
                    st.markdown(
                        f"""
                        <div style="border:{card_border}; border-radius:12px; padding:10px; margin-bottom:6px; background:{card_bg}; color:#eaf5ff; min-height:128px;">
                            <div style="font-weight:700; font-size:15px;">#{person_id} - {person_row['name']} {'⭐' if is_selected else ''}</div>
                            <div style="font-size:13px; margin-top:4px;">Hearts: {person_hearts_ui} ({person_hearts_left}/{person_hearts_cap})</div>
                            <div style="font-size:13px; margin-top:2px;">Points: {int(person_row['score'])}</div>
                            <div style="font-size:13px; margin-top:2px;">Status: {person_status}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Selected" if is_selected else "Select",
                        key=f"select_global_person_{person_id}",
                        use_container_width=True,
                        disabled=is_selected,
                    ):
                        st.session_state["global_person_id"] = person_id
                        st.rerun()

            selected_candidate_id = int(st.session_state["global_person_id"])
            selected_row = df[df["id"] == selected_candidate_id].iloc[0]
            selected_name = str(selected_row["name"])
            dating_unlocked = bool(selected_row["dating_zone_unlocked"])
            sleeping_unlocked = bool(selected_row["sleeping_together_unlocked"])
            relationship_unlocked = bool(selected_row["relationship_zone_unlocked"])

        controls_col = st.container()

        with controls_col:
            st.markdown("### Person controls")
            st.caption(
                "Current: "
                f"Dating {'✅' if dating_unlocked else '⬜'} | "
                f"Sleeping {'✅' if sleeping_unlocked else '⬜'} | "
                f"Relationship {'✅' if relationship_unlocked else '⬜'}"
            )

            st.markdown("#### Unlock statuses")
            level_cols = st.columns(3)
            with level_cols[0]:
                if st.button("Unlock Dating", key="unlock_dating", use_container_width=True, disabled=dating_unlocked):
                    success, msg = set_level_state(selected_candidate_id, "dating", True)
                    if success:
                        st.success(msg)
                    else:
                        st.warning(msg)
                    st.rerun()
                if st.button("Lock Dating", key="lock_dating", use_container_width=True, disabled=not dating_unlocked):
                    success, msg = set_level_state(selected_candidate_id, "dating", False)
                    if success:
                        st.success(msg)
                    else:
                        st.warning(msg)
                    st.rerun()

            with level_cols[1]:
                if st.button(
                    "Unlock Sleeping",
                    key="unlock_sleeping",
                    use_container_width=True,
                    disabled=sleeping_unlocked,
                ):
                    success, msg = set_level_state(selected_candidate_id, "sleeping", True)
                    if success:
                        st.success(msg)
                    else:
                        st.warning(msg)
                    st.rerun()
                if st.button(
                    "Lock Sleeping",
                    key="lock_sleeping",
                    use_container_width=True,
                    disabled=not sleeping_unlocked,
                ):
                    success, msg = set_level_state(selected_candidate_id, "sleeping", False)
                    if success:
                        st.success(msg)
                    else:
                        st.warning(msg)
                    st.rerun()

            with level_cols[2]:
                if st.button(
                    "Unlock Relationship",
                    key="unlock_relationship",
                    use_container_width=True,
                    disabled=relationship_unlocked,
                ):
                    success, msg = set_level_state(selected_candidate_id, "relationship", True)
                    if success:
                        st.success(msg)
                    else:
                        st.warning(msg)
                    st.rerun()
                if st.button(
                    "Lock Relationship",
                    key="lock_relationship",
                    use_container_width=True,
                    disabled=not relationship_unlocked,
                ):
                    success, msg = set_level_state(selected_candidate_id, "relationship", False)
                    if success:
                        st.success(msg)
                    else:
                        st.warning(msg)
                    st.rerun()

            st.markdown("#### Add points by status")
            if not dating_unlocked:
                st.info("Dating level is required to add standard points.")
            else:
                st.markdown("##### Add points via tiles")
                if actions_df.empty:
                    st.info("Add at least one tile in Point Rules.")
                else:
                    tile_columns = st.columns(3)
                    for idx, row in actions_df.iterrows():
                        with tile_columns[idx % 3]:
                            label = (
                                f"{row['label']}\n"
                                f"{row['points']} pts | {POINT_CATEGORIES[str(row['category'])]}"
                            )
                            if st.button(label, key=f"tile_{int(row['id'])}", use_container_width=True):
                                apply_action(selected_candidate_id, int(row["id"]))
                                st.success(f"Added {int(row['points'])} points to {selected_name}.")
                                st.rerun()

                st.markdown("##### Add extra points")
                with st.form("add_extra_points"):
                    extra_points = st.number_input("Extra points", min_value=-50, max_value=100, value=5, step=1)
                    extra_reason = st.text_input("Reason (optional)", placeholder="e.g. amazing support during hard day")
                    extra_submit = st.form_submit_button("Add extra")
                    if extra_submit:
                        success, msg = add_extra_points(selected_candidate_id, int(extra_points), extra_reason)
                        if success:
                            st.success(msg)
                        else:
                            st.warning(msg)
                        st.rerun()

            st.markdown("#### Spicy time")
            if not (sleeping_unlocked or relationship_unlocked):
                st.info("Unlock Sleeping or Relationship to add spicy-time ratings.")
            else:
                with st.form("add_spicy_time"):
                    happened_date = st.date_input("When happened", value=datetime.utcnow().date(), key="spicy_happened_date")
                    happened_time = st.time_input("Time", value=datetime.utcnow().time(), key="spicy_happened_time")
                    foreplay = st.slider("Foreplay", min_value=0, max_value=10, value=6, step=1)
                    connection_strength = st.slider("Connection strength", min_value=0, max_value=10, value=7, step=1)
                    orgasm_count = st.slider("Number of orgasms", min_value=0, max_value=6, value=1, step=1)
                    orgasm_intensity = st.slider("Orgasm intensity", min_value=0, max_value=10, value=6, step=1)
                    session_intensity = st.slider("Overall session intensity", min_value=0, max_value=10, value=7, step=1)
                    spicy_extra_points = st.number_input("Extra points for this spicy time", min_value=-50, max_value=100, value=0, step=1)
                    spicy_extra_reason = st.text_input(
                        "Extra reason (optional)",
                        placeholder="e.g. unforgettable chemistry",
                    )

                    spicy_submit = st.form_submit_button("Add spicy-time rating")
                    if spicy_submit:
                        happened_at = datetime.combine(happened_date, happened_time).isoformat(timespec="minutes")
                        added_points = add_spicy_rating(
                            selected_candidate_id,
                            happened_at,
                            foreplay,
                            connection_strength,
                            orgasm_count,
                            orgasm_intensity,
                            session_intensity,
                            int(spicy_extra_points),
                            spicy_extra_reason,
                        )
                        if added_points == 0:
                            st.warning("Could not add spicy-time rating.")
                        else:
                            st.success(f"Added {added_points} total points from spicy-time event.")
                        st.rerun()

                spicy_events_df = load_spicy_events_for_candidate(selected_candidate_id)
                if spicy_events_df.empty:
                    st.caption("No spicy-time events yet.")
                else:
                    st.caption("Spicy-time events history")
                    st.dataframe(
                        spicy_events_df[
                            [
                                "happened_at",
                                "created_at",
                                "foreplay",
                                "connection_strength",
                                "orgasm_count",
                                "orgasm_intensity",
                                "session_intensity",
                                "extra_points",
                                "extra_reason",
                                "points",
                            ]
                        ],
                        use_container_width=True,
                    )

            st.markdown("#### Board of sins")
            if not relationship_unlocked:
                st.info("Unlock Relationship to access Board of sins.")
            else:
                life_remaining = int(selected_row.get("sins_life_remaining", 300))
                life_cap = int(selected_row.get("sins_life_cap", 300))
                hearts_left = max(0, min(3, (life_remaining + 99) // 100))
                hearts_cap = max(0, min(3, life_cap // 100))
                hearts_ui = "❤" * hearts_left + "♡" * (3 - hearts_left)
                st.caption(f"Lives: {hearts_ui} ({life_remaining}% / {life_cap}%)")
                st.caption(f"Max hearts available now: {hearts_cap}/3")
                st.progress(life_remaining / max(1, life_cap))

                if life_remaining <= 0:
                    with st.container(border=True):
                        st.error("He lost all hearts. Choose: Necromancer or delete record.")
                        with st.form("necromancer_restore_critical"):
                            critical_deed = st.text_input(
                                "Super deed required for Necromancer",
                                placeholder="e.g. did something truly extraordinary",
                            )
                            critical_restore_submit = st.form_submit_button("Necromancer: Restore 1 heart")
                            if critical_restore_submit:
                                ok, msg = necromancer_restore_heart(selected_candidate_id, critical_deed)
                                if ok:
                                    st.success(msg)
                                else:
                                    st.info(msg)
                                st.rerun()

                        if st.button("Delete this candidate record", type="secondary", key="delete_candidate_after_hearts"):
                            delete_candidate(selected_candidate_id)
                            st.warning("Candidate deleted after all hearts were lost.")
                            st.rerun()

                sins_df = load_sins()

                with st.form("add_sin_rule"):
                    sin_label = st.text_input("Add sin label", placeholder="e.g. broke a promise")
                    sin_life_percent = st.slider("Life taken (%)", min_value=1, max_value=100, value=15, step=1)
                    add_sin_submit = st.form_submit_button("Add sin rule")
                    if add_sin_submit:
                        ok, msg = insert_sin_rule(sin_label, int(sin_life_percent))
                        if ok:
                            st.success(msg)
                        else:
                            st.warning(msg)
                        st.rerun()

                sins_df = load_sins()
                if sins_df.empty:
                    st.info("Add at least one sin rule.")
                else:
                    sin_options = {
                        f"{row['label']} (-{int(row['life_percent'])}% life)": int(row["id"])
                        for _, row in sins_df.iterrows()
                    }

                    with st.form("apply_sin"):
                        selected_sin_label = st.selectbox("Choose sin", list(sin_options.keys()), key="apply_sin_choice")
                        sin_notes = st.text_input("Notes (optional)", placeholder="context")
                        apply_sin_submit = st.form_submit_button("Apply sin")
                        if apply_sin_submit:
                            ok, msg = apply_sin(selected_candidate_id, sin_options[selected_sin_label], sin_notes)
                            if ok:
                                st.success(msg)
                            else:
                                st.warning(msg)
                            st.rerun()

                    delete_sin_label = st.selectbox("Delete sin rule", list(sin_options.keys()), key="delete_sin_choice")
                    if st.button("Delete selected sin rule", type="secondary"):
                        ok, msg = delete_sin_rule(sin_options[delete_sin_label])
                        if ok:
                            st.warning(msg)
                        else:
                            st.info(msg)
                        st.rerun()

                candidate_sin_events = load_sin_events_for_candidate(selected_candidate_id)
                if candidate_sin_events.empty:
                    st.caption("No sins events yet.")
                else:
                    st.caption("Board of sins history")
                    forgive_df = candidate_sin_events[
                        ["id", "created_at", "sin_label", "life_percent", "notes"]
                    ].rename(columns={"id": "event_id"})
                    forgive_df["forgive"] = False
                    edited_forgive_df = st.data_editor(
                        forgive_df,
                        hide_index=True,
                        use_container_width=True,
                        key="forgive_sins_editor",
                        column_config={
                            "event_id": st.column_config.NumberColumn("Event ID", disabled=True),
                            "created_at": st.column_config.TextColumn("When", disabled=True),
                            "sin_label": st.column_config.TextColumn("Sin", disabled=True),
                            "life_percent": st.column_config.NumberColumn("Life taken (%)", disabled=True),
                            "notes": st.column_config.TextColumn("Notes", disabled=True),
                            "forgive": st.column_config.CheckboxColumn("Forgive"),
                        },
                        disabled=["event_id", "created_at", "sin_label", "life_percent", "notes"],
                    )

                    if st.button("Forgive selected sins", type="secondary"):
                        selected_event_ids = edited_forgive_df.loc[
                            edited_forgive_df["forgive"], "event_id"
                        ].tolist()
                        if not selected_event_ids:
                            st.info("Select at least one sin event to forgive.")
                        else:
                            restored_count = 0
                            failed_ids: list[int] = []
                            for raw_event_id in selected_event_ids:
                                ok, _ = delete_sin_event(int(raw_event_id))
                                if ok:
                                    restored_count += 1
                                else:
                                    failed_ids.append(int(raw_event_id))

                            if failed_ids:
                                st.warning(
                                    f"Forgiven {restored_count} event(s). Failed IDs: {', '.join(str(v) for v in failed_ids)}"
                                )
                            else:
                                st.success(f"Forgiven {restored_count} event(s).")
                            st.rerun()

                if life_remaining > 0:
                    st.markdown("##### Necromancer")
                    st.caption("Forgive cannot restore lost hearts. Necromancer can restore one heart only for a super deed.")
                    with st.form("necromancer_restore"):
                        super_deed = st.text_input("What super thing did he do?", placeholder="e.g. helped in a crisis")
                        restore_submit = st.form_submit_button("Restore 1 heart")
                        if restore_submit:
                            ok, msg = necromancer_restore_heart(selected_candidate_id, super_deed)
                            if ok:
                                st.success(msg)
                            else:
                                st.info(msg)
                            st.rerun()

        st.markdown("### Update notes")
        note_row = df[df["id"] == selected_candidate_id].iloc[0]
        st.caption(f"Editing notes for: {selected_name}")

        with st.form("update_notes"):
            note_red_flags = st.text_area("Red Flags", value=str(note_row["red_flags"]) if pd.notna(note_row["red_flags"]) else "")
            note_text = st.text_area("Notes", value=str(note_row["notes"]) if pd.notna(note_row["notes"]) else "")
            update_notes_submit = st.form_submit_button("Save notes")
            if update_notes_submit:
                update_candidate_notes(selected_candidate_id, note_red_flags.strip(), note_text.strip())
                st.success("Notes updated.")
                st.rerun()

        st.markdown("### Base profile points")
        with st.form("update_base_points"):
            current_looks = int(note_row.get("looks_base", 0)) if pd.notna(note_row.get("looks_base", 0)) else 0
            looks_update = st.slider("Looks", min_value=-2, max_value=10, value=current_looks, step=1)

            current_rel_status = str(note_row.get("relationship_status", "Unknown"))
            current_looking_for = str(note_row.get("looking_for", "Not sure"))

            rel_default = (
                current_rel_status
                if current_rel_status in RELATIONSHIP_STATUS_OPTIONS
                else "It's complicated"
            )
            look_default = current_looking_for if current_looking_for in LOOKING_FOR_OPTIONS else "Not sure"

            rel_update_label = st.selectbox(
                "Relationship status",
                options=RELATIONSHIP_STATUS_OPTIONS,
                index=RELATIONSHIP_STATUS_OPTIONS.index(rel_default),
                format_func=lambda opt: f"{opt} ({relationship_point_map.get(opt, 0):+d})",
            )
            look_update_label = st.selectbox(
                "Looking for",
                options=LOOKING_FOR_OPTIONS,
                index=LOOKING_FOR_OPTIONS.index(look_default),
                format_func=lambda opt: f"{opt} ({looking_for_point_map.get(opt, 0):+d})",
            )

            base_submit = st.form_submit_button("Save base points")
            if base_submit:
                update_candidate_base_points(
                    selected_candidate_id,
                    looks_update,
                    rel_update_label,
                    look_update_label,
                )
                st.success("Base profile points updated.")
                st.rerun()

        st.markdown("### Remove Entry")
        removable = filtered[["id", "name", "score"]].copy()
        options = {
            f"{row['name']} (score {row['score']})": int(row["id"]) for _, row in removable.iterrows()
        }
        selected = st.selectbox("Select a person to delete", list(options.keys()))

        if st.button("Delete selected", type="secondary"):
            delete_candidate(options[selected])
            st.warning("Entry deleted.")
            st.rerun()

if __name__ == "__main__":
    main()
