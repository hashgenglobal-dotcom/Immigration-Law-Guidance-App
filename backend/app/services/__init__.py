"""Service-layer modules (no HTTP, no DB models).

Services contain small, focused integrations with external systems
(PostgreSQL, Redis, Ollama, etc.). They must obey the project's
privacy rules: no full user question or answer text is persisted,
and no public AI API is ever called.
"""
