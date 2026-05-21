"""Pre-generation legal safety checks (POST-05)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_DISCLAIMER = (
    "This is general legal information only. It is not legal advice, does not create "
    "an attorney-client relationship, and does not replace a qualified immigration attorney."
)

_FRAUD_PATTERNS = (
    re.compile(r"\b(lie|lying|fake|false)\b.*\b(application|asylum|visa|petition)\b", re.I),
    re.compile(r"\bmisrepresent\b", re.I),
    re.compile(r"\bwithout\s+getting\s+caught\b", re.I),
    re.compile(r"\bfraud\b", re.I),
)

_EVASION_PATTERNS = (
    re.compile(r"\bfake\s+passport\b", re.I),
    re.compile(r"\bevade\b.*\b(immigration|law|court)\b", re.I),
    re.compile(r"\bavoid\s+court\b", re.I),
    re.compile(r"\bcross\s+border\s+illegally\b", re.I),
)


@dataclass(frozen=True)
class GuardrailRefusal:
    category: str
    message: str
    query_hash: str


def _query_hash(message: str) -> str:
    return hashlib.sha256(message.lower().strip().encode()).hexdigest()


def evaluate_message(message: str) -> GuardrailRefusal | None:
    """Return refusal metadata if message matches blocked categories."""
    normalized = message.strip()
    if not normalized:
        return None

    qhash = _query_hash(normalized)

    for pat in _FRAUD_PATTERNS:
        if pat.search(normalized):
            return GuardrailRefusal(
                category="fraud_or_misrepresentation",
                message=(
                    "I cannot provide guidance on misrepresenting facts, committing fraud, or "
                    "deceiving immigration authorities. For legitimate options, consult a qualified "
                    "immigration attorney or official USCIS resources."
                ),
                query_hash=qhash,
            )

    for pat in _EVASION_PATTERNS:
        if pat.search(normalized):
            return GuardrailRefusal(
                category="evasion_or_unlawful_conduct",
                message=(
                    "I cannot provide guidance on evading immigration law, using fraudulent documents, "
                    "or avoiding legal responsibilities. Consult a qualified immigration attorney."
                ),
                query_hash=qhash,
            )

    return None


REFUSAL_DISCLAIMER = _DISCLAIMER
