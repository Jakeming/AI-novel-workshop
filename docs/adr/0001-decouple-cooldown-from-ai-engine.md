# ADR-0001: Decouple cooldown logic from AI engine

**Status**: Accepted
**Date**: 2026-05-28
**Context**: 拆文工坊

## Problem

`check_similarity` output originally included `cooldown_required` field, putting rule decisions inside AI engine. Changing cooldown rules (hours threshold, failure count) would require modifying AI engine code.

## Decision

AI engine outputs validation result only (similarity values + verdict). Rule engine (`coolant.py`) is sole owner of cooldown timing, consecutive count, daily limits.

```
Before:  AI engine -> {similarity, verdict, cooldown_required}
After:   AI engine -> {similarity, verdict}
         Rule engine reads verdict -> decides cooldown
```

## Consequences

Positive:
- Rule changes (24h -> 48h, 2 failures -> 3) affect only rule-engine/
- AI engine stays stateless and testable in isolation
- One source of truth for user state

Negative:
- Frontend must call user_status API (not read from validation response)
