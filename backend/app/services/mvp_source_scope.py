"""MVP legal source scope helpers for retrieval and chat reporting.

The MVP corpus is three co-active dataset versions (no combined dataset row):
  - ecfr-title8-full-*  → eCFR Title 8 (regulations)
  - ina-*               → INA / U.S. Code Title 8 (statutes)
  - uscis-pm-*          → USCIS Policy Manual (policy)

BIA decisions are post-MVP and not ingested. Sample eCFR preview datasets
(ecfr-title8-sample-*) use status ``ready`` and must not be searched.
"""

from __future__ import annotations

# Dataset version name prefixes for MVP-active corpora (status='active' in DB).
_MVP_ECFR_PREFIX = "ecfr-title8-full"
_MVP_INA_PREFIX = "ina-"
_MVP_USCIS_PREFIX = "uscis-pm-"


def source_family_from_version(version_name: str | None) -> str | None:
    """Map a dataset ``version_name`` to a human-readable MVP source family."""
    if not version_name:
        return None
    # Keep sample datasets explicitly outside the MVP source family.
    if version_name.startswith("ecfr-title8-sample"):
        return "eCFR Title 8 (sample — non-MVP)"
    if version_name.startswith(_MVP_ECFR_PREFIX):
        return "eCFR Title 8"
    if version_name.startswith(_MVP_INA_PREFIX):
        return "INA / U.S. Code Title 8"
    if version_name.startswith(_MVP_USCIS_PREFIX):
        return "USCIS Policy Manual"
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
