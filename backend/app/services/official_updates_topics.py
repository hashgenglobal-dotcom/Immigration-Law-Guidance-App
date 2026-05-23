"""Topic taxonomy and rule-based tagging for Official Updates."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateTopic:
    id: str
    label: str
    description: str


# Fixed enum — do not add free-form tags from LLM in v1.
UPDATE_TOPICS: tuple[UpdateTopic, ...] = (
    UpdateTopic("general", "General", "Broad official immigration announcements"),
    UpdateTopic("f1_j1", "F-1 / J-1 students", "International students and exchange visitors"),
    UpdateTopic("h1b", "H-1B & work visas", "Employment-based visas and PER"),
    UpdateTopic("family", "Family immigration", "Family petitions and relatives"),
    UpdateTopic("asylum", "Asylum & protection", "Asylum, refugee, and humanitarian protection"),
    UpdateTopic("tps", "TPS & humanitarian", "Temporary Protected Status and similar"),
    UpdateTopic("green_card", "Green card", "Permanent residence and adjustment"),
    UpdateTopic("citizenship", "Citizenship", "Naturalization and civics"),
    UpdateTopic("ead_work", "Work permits (EAD)", "Employment authorization documents"),
    UpdateTopic("enforcement", "Enforcement & courts", "ICE, EOIR, removal, border policy"),
    UpdateTopic("fees_forms", "Fees & forms", "Filing fees, form editions, processing"),
    UpdateTopic("visa_bulletin", "Visa bulletin", "Priority dates and visa availability"),
)

TOPIC_BY_ID: dict[str, UpdateTopic] = {t.id: t for t in UPDATE_TOPICS}

# Keyword rules: (topic_id, patterns)
_TOPIC_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("f1_j1", re.compile(r"\b(F-1|J-1|SEVIS|OPT|STEM|international student|exchange visitor)\b", re.I)),
    ("h1b", re.compile(r"\b(H-1B|H1B|L-1|O-1|PER|nonimmigrant worker|specialty occupation)\b", re.I)),
    ("family", re.compile(r"\b(I-130|I-485|spouse|fiancé|fiance|family petition|relative)\b", re.I)),
    ("asylum", re.compile(r"\b(asylum|refugee|credible fear|withholding|CAT protection)\b", re.I)),
    ("tps", re.compile(r"\b(TPS|temporary protected|humanitarian parole|U4U)\b", re.I)),
    ("green_card", re.compile(r"\b(green card|permanent resident|adjustment of status|I-485)\b", re.I)),
    ("citizenship", re.compile(r"\b(naturalization|N-400|citizenship|civics test)\b", re.I)),
    ("ead_work", re.compile(r"\b(EAD|I-765|employment authorization|work permit)\b", re.I)),
    ("enforcement", re.compile(r"\b(ICE|EOIR|removal|deportation|NTA|border|detention)\b", re.I)),
    ("fees_forms", re.compile(r"\b(filing fee|form I-|edition|biometric fee|premium processing)\b", re.I)),
    ("visa_bulletin", re.compile(r"\b(visa bulletin|priority date|visa availability|final action)\b", re.I)),
]


def tag_topics(title: str, excerpt: str | None = None) -> list[str]:
    """Return sorted topic ids matched by keyword rules; always includes 'general' if empty."""
    blob = f"{title}\n{excerpt or ''}"
    matched: set[str] = set()
    for topic_id, pattern in _TOPIC_RULES:
        if pattern.search(blob):
            matched.add(topic_id)
    if not matched:
        matched.add("general")
    return sorted(matched)


def parse_topic_filter(topics_param: str | None) -> list[str]:
    """Parse comma-separated topic ids; ignore unknown."""
    if not topics_param or topics_param.strip().lower() in ("all", ""):
        return []
    ids = [t.strip().lower() for t in topics_param.split(",") if t.strip()]
    return [t for t in ids if t in TOPIC_BY_ID]


def topic_label(topic_id: str) -> str:
    return TOPIC_BY_ID.get(topic_id, UpdateTopic(topic_id, topic_id, "")).label


def primary_topic_for_ask(topic_tags: list[str], user_filter: str | None) -> str:
    """Pick a topic label for Ask bridge button copy."""
    if user_filter and user_filter in TOPIC_BY_ID:
        return TOPIC_BY_ID[user_filter].label
    for tid in topic_tags:
        if tid != "general" and tid in TOPIC_BY_ID:
            return TOPIC_BY_ID[tid].label
    return "this announcement"
