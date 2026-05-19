# INA (Immigration and Nationality Act) Ingestion Plan

**Status:** Planning Phase  
**Priority:** Critical (Phase 3)  
**Source:** U.S. Code Title 8 via GovInfo API

---

## Overview

The Immigration and Nationality Act (INA) is the foundational federal statute governing U.S. immigration law. All regulations (CFR) and policy guidance (USCIS PM) derive authority from the INA.

### Why INA Matters

| Aspect | Description |
|--------|-------------|
| **Authority** | Federal statute (law passed by Congress) |
| **Hierarchy** | Supreme over CFR and policy guidance |
| **Coverage** | All immigration categories, grounds of inadmissibility, removal, benefits |
| **Stability** | Changes only via Congressional amendment (less frequent than CFR) |
| **MVP Questions** | Statutory basis for 80%+ of immigrant questions |

### Key INA Sections for MVP

| INA Section | Subject | CFR Cross-Reference |
|-------------|---------|---------------------|
| INA § 101(a)(42) | Refugee definition | 8 CFR § 208 |
| INA § 208 | Asylum eligibility | 8 CFR § 208 |
| INA § 212 | Grounds of inadmissibility | 8 CFR § 212 |
| INA § 240 | Removal proceedings | 8 CFR § 1240 |
| INA § 245 | Adjustment of status | 8 CFR § 245 |
| INA § 274A | Employment authorization | 8 CFR § 274a |
| INA § 319 | Naturalization requirements | 8 CFR § 319 |

---

## Source Structure

### Official Source

**Primary:** GovInfo (U.S. Government Publishing Office)  
**URL:** https://www.govinfo.gov/app/collection/uscode  
**API:** https://api.govinfo.gov/uscode  

### Hierarchy

```
Title 8 (Aliens and Nationality)
  └── Chapter I (General Provisions)
      └── Subchapter II (Immigration)
          └── Part III (Nationality and Naturalization)
              └── Section (§ 201, § 202, ... § 349)
```

### GovInfo API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/uscode/titles` | List all titles (get Title 8 ID) |
| `/uscode/titles/{title_id}` | Get title structure |
| `/uscode/titles/{title_id}/sections/{section_id}` | Get section content (XML/JSON) |
| `/uscode/bulk` | Bulk download (optional) |

---

## Technical Approach

### Option A: GovInfo API (Recommended)

**Pros:**
- Official, documented API
- JSON/XML formats available
- Version tracking (date-specific snapshots)
- Stable URLs

**Cons:**
- Rate limiting (check docs)
- Requires pagination for full title

**Implementation:**
```python
import httpx

BASE_URL = "https://api.govinfo.gov/uscode"

async def fetch_ina_section(section_number: str) -> dict:
    """Fetch one INA section (e.g., '208' for INA § 208)."""
    url = f"{BASE_URL}/titles/8/sections/{section_number}"
    params = {"api_key": govinfo_cred}  # GovInfo credential stored outside Git
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
```

### Option B: Bulk Download

**Pros:**
- Single download for entire Title 8
- No rate limiting concerns
- Offline processing

**Cons:**
- Large file (~50-100 MB XML)
- Less frequent updates
- More complex parsing

**URL:** https://www.govinfo.gov/bulkdata/USCODE/title-8/

### Option C: uscode.house.gov (Alternative)

**URL:** https://uscode.house.gov/browse.xhtml  
**Format:** HTML with structured navigation

**Note:** Less reliable than GovInfo API; use as fallback only.

---

## Data Mapping

### Source Registry Entry

Already exists:
```sql
source_name: U.S. Code Title 8 (INA)
source_type: statute
publisher: GPO
base_url: https://uscode.house.gov/browse.xhtml
access_method: api
update_frequency: monthly
```

### Schema Mapping

| INA Element | Database Table | Notes |
|-------------|----------------|-------|
| Title/Chapter/Subchapter | `legal_documents` | Hierarchical metadata |
| Section (§ 208, § 245, etc.) | `legal_sections` | Official statutory text |
| Subsections ((a), (b), (c)...) | `legal_chunks` | Retrieval-ready segments |
| Cross-references | `legal_sections` | Link to CFR, other INA sections |

### Metadata Extraction

```python
{
    "citation": "INA § 208",
    "title": "Asylum — Eligibility",
    "official_url": "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title8-section208",
    "section_number": "208",
    "chapter": "12",
    "subchapter": "II",
    "effective_date": "2025-01-01",  # From version metadata
    "topic": "asylum",
    "subtopic": "eligibility",
    "risk_level": "critical"
}
```

---

## Implementation Plan

### Phase 3.1: API Setup & Testing (1 day)

- [ ] Register for GovInfo API key (free: https://api.govinfo.gov/)
- [ ] Test API access for Title 8 sections
- [ ] Parse JSON/XML response structure
- [ ] Build fetch script for 10 sample sections

### Phase 3.2: Full Ingestion (1 day)

- [ ] Fetch all ~300-400 INA sections (Title 8)
- [ ] Save raw JSON/XML to `data/ina/raw/`
- [ ] Generate JSON preview (`data/ina/preview/`)
- [ ] Handle rate limiting (check API docs)

### Phase 3.3: Database Insertion (1 day)

- [ ] Map to `legal_documents` / `legal_sections` / `legal_chunks`
- [ ] Extract cross-references (CFR, other INA)
- [ ] Assign topic/subtopic/risk_level
- [ ] Create dataset version (`ina-title8-2026-05-19`)

### Phase 3.4: Embeddings & Activation (1 day)

- [ ] Generate embeddings (nomic-embed-text)
- [ ] Validate retrieval quality
- [ ] Activate dataset

---

## Privacy & Compliance

✅ **Public legal-source data:**
- U.S. Code is official federal statute
- No copyright restrictions (U.S. government work)
- Safe to ingest and store

✅ **No user data:**
- Purely source ingestion
- All processing local

✅ **API compliance:**
- Use official GovInfo API key
- Respect rate limits
- Proper User-Agent header

---

## Sample Sections

```
INA § 101(a)(42) — Refugee definition
INA § 208 — Asylum
INA § 212(a) — Grounds of inadmissibility
INA § 235 — Inspection by immigration officers
INA § 240 — Removal proceedings
INA § 241 — Detention and removal of aliens
INA § 245 — Adjustment of status
INA § 274A — Unlawful employment of aliens
INA § 319 — Naturalization requirements
```

---

## Developer Notes

### API Key Registration

1. Visit: https://api.govinfo.gov/
2. Click "Get API Key"
3. Fill form (free, instant)
4. Set the GovInfo credential in your local environment (outside Git)

### Sample Fetch Code

```python
import httpx
from pathlib import Path

govinfo_cred = os.environ["GOVINFO_CREDENTIAL"]  # GovInfo credential stored outside Git
BASE_URL = "https://api.govinfo.gov/uscode"

async def fetch_title8_sections() -> list[dict]:
    """Fetch all Title 8 sections."""
    # First, get title structure
    url = f"{BASE_URL}/titles/8"
    params = {"api_key": govinfo_cred}
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        structure = response.json()
    
    # Extract section IDs
    section_ids = extract_section_ids(structure)
    
    # Fetch each section
    results = []
    for section_id in section_ids:
        section_url = f"{BASE_URL}/titles/8/sections/{section_id}"
        section_response = await client.get(section_url, params=params)
        section_response.raise_for_status()
        results.append(section_response.json())
    
    return results
```

---

## Next Steps

1. **Register for API key** (5 minutes)
2. **Build discovery script** (`scripts/fetch_ina_title8.py`)
3. **Test parser** on 10 sample sections
4. **Run full ingestion** (estimated 300-400 sections)
5. **Insert into database** with proper metadata
6. **Generate embeddings** and activate

---

## Contact

**Developer:** Hash  
**Repo:** https://github.com/hashgenglobal-dotcom/Immigration-Law-Guidance-App
