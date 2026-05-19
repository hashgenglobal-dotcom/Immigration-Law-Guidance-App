# 🗄️ Database Backup Instructions

**Generated:** May 19, 2026  
**Database:** `immigration_law_dev`  
**PostgreSQL Version:** 18.3 (Homebrew)

---

## Why SQL Dumps Are Not in Git

The database data dump (`data-inserts.sql`) is **161 MB** — too large for practical Git version control. Instead, this folder contains:

- ✅ `schema-only.sql` — Database schema (27K, included in git)
- ✅ `table-row-counts.txt` — Row counts per table (included in git)
- ❌ `data-inserts.sql` — Full data dump (161M, generated on-demand)

---

## How to Regenerate Database Dumps

### Prerequisites

```bash
# Ensure PostgreSQL 18 is installed (Homebrew)
brew install postgresql@18

# Add to PATH (or use full path below)
export PATH="/opt/homebrew/opt/postgresql@18/bin:$PATH"
```

### Regenerate Schema Dump

```bash
cd ~/projects/immigration-law-app-official

/opt/homebrew/opt/postgresql@18/bin/pg_dump \
  -h localhost -p 54329 -U hash \
  -d immigration_law_dev \
  --schema-only \
  > review/database/schema-only.sql
```

### Regenerate Data Dump

```bash
cd ~/projects/immigration-law-app-official

/opt/homebrew/opt/postgresql@18/bin/pg_dump \
  -h localhost -p 54329 -U hash \
  -d immigration_law_dev \
  --data-only --inserts \
  --table=source_registry \
  --table=raw_documents \
  --table=legal_documents \
  --table=legal_sections \
  --table=legal_chunks \
  --table=dataset_versions \
  > review/database/data-inserts.sql
```

### Regenerate Row Counts

```bash
psql -h localhost -p 54329 -U hash -d immigration_law_dev -c \
  "SELECT 'source_registry' as table_name, COUNT(*) as row_count FROM source_registry \
   UNION ALL SELECT 'raw_documents', COUNT(*) FROM raw_documents \
   UNION ALL SELECT 'legal_documents', COUNT(*) FROM legal_documents \
   UNION ALL SELECT 'legal_sections', COUNT(*) FROM legal_sections \
   UNION ALL SELECT 'legal_chunks', COUNT(*) FROM legal_chunks \
   UNION ALL SELECT 'dataset_versions', COUNT(*) FROM dataset_versions;" \
  > review/database/table-row-counts.txt
```

---

## Restore Instructions

### From Schema + Data Dumps

```bash
# Create fresh database
createdb -h localhost -p 54329 -U hash immigration_law_restore

# Restore schema
/opt/homebrew/opt/postgresql@18/bin/psql \
  -h localhost -p 54329 -U hash \
  -d immigration_law_restore \
  -f review/database/schema-only.sql

# Restore data
/opt/homebrew/opt/postgresql@18/bin/psql \
  -h localhost -p 54329 -U hash \
  -d immigration_law_restore \
  -f review/database/data-inserts.sql

# Verify
psql -h localhost -p 54329 -U hash -d immigration_law_restore -c \
  "SELECT COUNT(*) FROM legal_chunks;"
```

**Expected:** 11,583 chunks

### From Migration Scripts (Alternative)

If you prefer to rebuild from source:

```bash
cd ~/projects/immigration-law-app-official

# 1. Run migrations
uv run --project backend python scripts/activate_dataset.py

# 2. Verify
psql -h localhost -p 54329 -U hash -d immigration_law_dev -c \
  "SELECT COUNT(*) FROM legal_chunks WHERE is_active = TRUE;"
```

---

## Database Statistics (Current State)

| Table | Rows | Description |
|-------|------|-------------|
| `source_registry` | 7 | Data sources |
| `raw_documents` | 728 | Raw fetched documents |
| `legal_documents` | 728 | Processed legal documents |
| `legal_sections` | 2,578 | Legal sections (chapters, parts) |
| `legal_chunks` | 11,583 | Embeddable chunks with vectors |
| `dataset_versions` | 4 | Versioned snapshots |

**Total Chunks Embedded:** 11,583  
**Embedding Model:** nomic-embed-text (768 dimensions)  
**Vector Storage:** ~35 MB

---

## Notes

- **PostgreSQL Version Mismatch:** Use `/opt/homebrew/opt/postgresql@18/bin/pg_dump` (not system pg_dump)
- **Database Password:** `hash` (development only)
- **Port:** `54329` (non-standard for dev)
- **Host:** `localhost`

---

**Generated:** May 19, 2026, 12:35 PM EST
