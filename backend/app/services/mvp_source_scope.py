"""MVP legal source scope helpers for retrieval and chat reporting.

The MVP corpus is five co-active dataset versions (no combined dataset row):
  Canonical name                Supabase alias      Source family
  ecfr-title8-full-*            eCFR-v* / ecfr-v*   eCFR Title 8 (regulations)
  ina-*                         ina-v*               INA / U.S. Code Title 8 (statutes)
  uscis-pm-*                    uscis-pm-v*          USCIS Policy Manual (policy)
  uscis-official-pages-*                             USCIS Official Pages (guidance)
  bia-*                                              BIA Precedent Decisions (case law)

Sample eCFR preview datasets (ecfr-title8-sample-*) must have is_active=FALSE.
"""

from __future__ import annotations

# Dataset version name prefixes for MVP-active corpora (status='active' in DB).
_MVP_ECFR_PREFIX = "ecfr-title8-full"
_MVP_INA_PREFIX = "ina-"
_MVP_USCIS_PREFIX = "uscis-pm-"
_MVP_USCIS_PAGES_PREFIX = "uscis-official-pages"


def source_family_from_version(version_name: str | None) -> str | None:
    """Map a dataset ``version_name`` to a human-readable source family.

    Handles both canonical local names and Supabase alias names.
    """
    if not version_name:
        return None
    n = version_name.lower()

    # eCFR sample — explicitly non-MVP; checked before the full-corpus prefix.
    if n.startswith("ecfr-title8-sample"):
        return "eCFR Title 8 (sample — non-MVP)"

    # eCFR Title 8 — canonical and Supabase alias (eCFR-v / ecfr-v).
    if n.startswith(_MVP_ECFR_PREFIX) or n.startswith("ecfr-v"):
        return "eCFR Title 8"

    # INA — canonical (ina-2026-*) and Supabase alias (ina-v2026-*) both
    # match because both start with "ina-".
    if n.startswith(_MVP_INA_PREFIX):
        return "INA / U.S. Code Title 8"

    # USCIS Policy Manual — canonical (uscis-pm-2026-*) and Supabase alias
    # (uscis-pm-v2026-*) both start with "uscis-pm-".
    if n.startswith(_MVP_USCIS_PREFIX):
        return "USCIS Policy Manual"

    # USCIS Official Pages (supplemental guidance).
    if n.startswith(_MVP_USCIS_PAGES_PREFIX):
        return "USCIS Official Pages"

    # BIA Precedent Decisions — case-law corpus for NTA/removal queries.
    if n.startswith("bia-") or n.startswith("bia_"):
        return "BIA Precedent Decisions"

    return "other"


def format_active_dataset_summary(active_datasets: list[str]) -> str | None:
    """Single-string summary for backward-compatible ``active_dataset`` field."""
    if not active_datasets:
        return None
    if len(active_datasets) == 1:
        return active_datasets[0]
    return "mvp-multi-source: " + ", ".join(active_datasets)


def mvp_source_families_from_versions(active_datasets: list[str]) -> list[str]:
    """Deduplicated MVP source families present in the active dataset list."""
    seen: dict[str, None] = {}
    for name in active_datasets:
        family = source_family_from_version(name)
        if family and family not in seen:
            seen[family] = None
    return list(seen.keys())
