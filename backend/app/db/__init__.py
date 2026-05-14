"""Database access layer (psycopg-based, no ORM yet).

Contains DSN handling and small async helpers for talking to PostgreSQL.
SQLAlchemy models are intentionally NOT introduced here yet — this layer
is just enough plumbing to support the schema health probe and future
read paths against the official legal-source tables.

Privacy rule: nothing in this package may read, log, or transmit full
user question text or full generated answer text. Only privacy-safe
metadata may ever be persisted (see `privacy_safe_answer_logs`).
"""
