# Observability (POST-06)

## Request IDs

Every response includes `X-Request-Id` (generated or forwarded from client).

## Logging

Access logs use logger `sourcepath.access` with:

- `request_id`, `method`, `path`, `status`, `latency_ms`

**Never logged:** request bodies, query parameters with user questions, JWT secrets, DSNs.

## Production

- Ship logs to your aggregator with retention per `docs/privacy-data-retention-policy.md`
- Add metrics (Prometheus) in a follow-up if needed
