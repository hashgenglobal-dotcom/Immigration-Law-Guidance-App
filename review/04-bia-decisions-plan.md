# BIA Decisions Ingestion Plan

**Status:** Planning Phase  
**Priority:** Medium (Phase 4)  
**Source:** DOJ EOIR (Executive Office for Immigration Review)

---

## Overview

Board of Immigration Appeals (BIA) decisions are binding precedent for all immigration judges and USCIS officers. They interpret statutes (INA), regulations (CFR), and policy guidance.

### Why BIA Decisions Matter

| Aspect | Description |
|--------|-------------|
| **Authority** | Binding precedent on immigration courts and USCIS |
| **Coverage** | Case-specific interpretations of INA, CFR, policy |
| **Hierarchy** | Below federal courts, above immigration judges |
| **Updates** | New precedent decisions monthly |
| **MVP Questions** | Critical for complex cases, appeals, waivers |

### Key BIA Precedent Decisions

| Case Name | Citation | Subject |
|-----------|----------|---------|
| Matter of A-B- | 28 I&N Dec. 307 (2021) | Asylum, domestic violence |
| Matter of L-E-A- | 28 I&N Dec. 30 (2019) | Particular social group |
| Matter of K-A-C- | 27 I&N Dec. 347 (2018) | Asylum, firm resettlement |
| Matter of M-A-M- | 25 I&N Dec. 474 (2011) | Criminal grounds |
| Matter of D-J- | 27 I&N Dec. 610 (2018) | Bond hearings |

---

## Source Structure

### Official Source

**Primary:** DOJ EOIR  
**URL:** https://www.justice.gov/eoir/bia-decisions  
**Format:** HTML with search interface

### Decision Types

| Type | Description | Count |
|------|-------------|-------|
| Precedent | Binding on all immigration proceedings | ~500 |
| Non-Precedent | Persuasive only (not binding) | ~10,000+ |
| Summary Orders | Brief dispositions (no legal analysis) | ~50,000+ |

### Hierarchy

```
BIA Decisions
  └── Precedent Decisions (indexed by I&N Dec. citation)
      └── Volume (I&N Dec. Vol 1-30+)
          └── Page (e.g., 307 in 28 I&N Dec. 307)
              └── Full decision text (HTML/PDF)
```

---

## Technical Approach

### Challenge: No Bulk API

Unlike eCFR and INA (which have official APIs), BIA decisions require:
- HTML scraping from justice.gov/eoir
- PDF parsing for older decisions
- Search interface navigation
- No official bulk download

### Strategy

#### Option A: Precedent Decision Crawl (Recommended for MVP)

1. **Start with precedent list:** https://www.justice.gov/eoir/bia-precedent-decisions
2. **Extract all precedent citations** (I&N Dec. references)
3. **Fetch each decision page** individually
4. **Parse HTML/PDF** to extract:
   - Case name (Matter of X-Y-)
   - Citation (28 I&N Dec. 307)
   - Decision date
   - Full text (majority, concurrence, dissent)
   - Subject keywords

**Scope:** ~500 precedent decisions (manageable, high-value)

#### Option B: Full Archive Crawl (Future Phase)

- Crawl all ~10,000+ non-precedent decisions
- Requires PDF parsing infrastructure
- Significant storage (~5-10 GB)
- Lower priority than precedent

#### Option C: Hybrid

- Precedent decisions first (HTML)
- Add non-precedent via bulk PDF processing later

---

## Data Mapping

### Source Registry Entry

Already exists:
```sql
source_name: DOJ EOIR BIA Decisions
source_type: case_law
publisher: DOJ
base_url: https://www.justice.gov/eoir/bia-decisions
access_method: scraping
update_frequency: weekly
```

### Schema Mapping

| BIA Element | Database Table | Notes |
|-------------|----------------|-------|
| Case name | `legal_documents` | "Matter of A-B-" |
| Citation | `legal_sections` | "28 I&N Dec. 307 (BIA 2021)" |
| Decision text | `legal_chunks` | Retrieval-ready segments |
| Subject keywords | `legal_sections.topic` | "asylum", "bond", etc. |
| Precedent status | `legal_sections.metadata` | Boolean flag |
| Decision date | `legal_sections.effective_date` | YYYY-MM-DD |

### Metadata Extraction

```python
{
    "citation": "28 I&N Dec. 307 (BIA 2021)",
    "case_name": "Matter of A-B-",
    "title": "Asylum Eligibility — Domestic Violence",
    "official_url": "https://www.justice.gov/eoir/bia-precedent-decisions",
    "decision_date": "2021-09-25",
    "topic": "asylum",
    "subtopic": "particular_social_group",
    "risk_level": "critical",
    "is_precedent": True
}
```

---

## Implementation Plan

### Phase 4.1: Precedent List Discovery (1 day)

- [ ] Fetch precedent decisions index page
- [ ] Parse all ~500 precedent citations
- [ ] Build URL mapping (citation → decision page)
- [ ] Save to `data/bia/precedent-list.json`

### Phase 4.2: Decision Fetch & Parse (2 days)

- [ ] Fetch each precedent decision page
- [ ] Save raw HTML to `data/bia/raw/`
- [ ] Parse decision text (strip navigation, headers)
- [ ] Extract metadata (case name, citation, date, subjects)
- [ ] Generate JSON preview (`data/bia/preview/`)

### Phase 4.3: Database Insertion (1 day)

- [ ] Map to `legal_documents` / `legal_sections` / `legal_chunks`
- [ ] Tag as precedent vs. non-precedent
- [ ] Assign topic/subtopic/risk_level
- [ ] Create dataset version (`bia-precedent-2026-05-19`)

### Phase 4.4: Embeddings & Activation (1 day)

- [ ] Generate embeddings (nomic-embed-text)
- [ ] Validate retrieval quality
- [ ] Activate dataset

---

## Privacy & Compliance

✅ **Public legal-source data:**
- BIA decisions are official government legal opinions
- No copyright restrictions (U.S. government work)
- Safe to ingest and store

✅ **No user data:**
- Purely source ingestion
- All processing local

✅ **Polite scraping:**
- Rate limit: 1 request/second
- User-Agent identifying project
- Respect robots.txt

---

## Sample Precedent Decisions

```
Matter of A-B-, 28 I&N Dec. 307 (BIA 2021) — Asylum, domestic violence
Matter of L-E-A-, 28 I&N Dec. 30 (BIA 2019) — Particular social group
Matter of K-A-C-, 27 I&N Dec. 347 (BIA 2018) — Firm resettlement
Matter of M-A-M-, 25 I&N Dec. 474 (BIA 2011) — Criminal grounds
Matter of D-J-, 27 I&N Dec. 610 (BIA 2018) — Bond hearings
Matter of J-J-, 28 I&N Dec. 1 (BIA 2020) — Cancellation of removal
Matter of R-A-, 23 I&N Dec. 694 (BIA 2005) — Asylum, gender-based violence
```

---

## Developer Notes

### Sample Fetch Code

```python
import httpx
from bs4 import BeautifulSoup

async def fetch_bia_decision(url: str) -> dict:
    """Fetch one BIA precedent decision."""
    headers = {
        "User-Agent": "Immigration-Law-Guidance-App/1.0 (educational; contact: hash@hashgen.global)",
        "Accept": "text/html",
    }
    
    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'lxml')
    
    # Extract case name (usually in <h1> or <h2>)
    case_name = soup.find(['h1', 'h2']).get_text(strip=True)
    
    # Extract decision text (main content area)
    content_div = soup.find('div', class_='usa-prose')  # Adjust selector
    text = content_div.get_text(' ', strip=True) if content_div else ""
    
    # Extract citation from text or metadata
    citation = extract_citation_from_text(text)
    
    return {
        "url": url,
        "case_name": case_name,
        "citation": citation,
        "text": text[:5000],  # Preview
    }
```

### Rate Limiting

```python
import asyncio

async def crawl_bia_precedent(urls: list[str]):
    for i, url in enumerate(urls, 1):
        print(f"Fetching {i}/{len(urls)}: {url}")
        result = await fetch_bia_decision(url)
        yield result
        await asyncio.sleep(1.0)  # 1 req/sec
```

---

## Next Steps

1. **Build precedent list scraper** (`scripts/fetch_bia_precedent_list.py`)
2. **Test parser** on 10 sample decisions
3. **Run full crawl** (~500 precedent decisions, ~10-15 minutes)
4. **Insert into database** with proper metadata
5. **Generate embeddings** and activate

---

## Future Enhancements

### Non-Precedent Decisions

- Crawl all ~10,000+ non-precedent decisions
- Requires PDF parsing (pymupdf, marker-pdf)
- Significant storage (~5-10 GB)
- Lower priority than precedent

### Federal Court Cases

- Circuit court decisions (9th Cir., 5th Cir., etc.)
- Source: CourtListener API, PACER (paid)
- Higher complexity, lower priority

### BIA Search Interface

- Build search UI for precedent decisions
- Filter by subject, date, citation
- Link to related CFR/INA sections

---

## Contact

**Developer:** Hash  
**Repo:** https://github.com/hashgenglobal-dotcom/Immigration-Law-Guidance-App
