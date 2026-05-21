#!/usr/bin/env python3
"""BIA v2 placeholder — exits non-zero until an official source is configured."""

import sys

print(
    "BIA v2 ingest is blocked: no official bulk source. "
    "See review/04-bia-decisions-challenge-report.md",
    file=sys.stderr,
)
sys.exit(2)
