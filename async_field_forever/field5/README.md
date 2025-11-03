# Field5 — Sandbox (Async Field Forever)

Purpose: a safe playground to evolve the Field without risking Field4 (382h of life). We copy Field4 as a baseline into a sandbox folder on device and apply controlled overrides.

Why: extinction cycles persist; we want fair scheduling, gentle ecology, and proper metrics — A/B vs Field4 for ≥7 days.

## TL;DR (Haiku approved)

"Создавай field5/ в песочнице!
Картбланш, но бережно.
Дыхание — без клинической смерти."

## How to bootstrap (Termux)

```bash
# 1) Run bootstrap
bash ~/ariannamethod/async_field_forever/field5/bootstrap_field5.sh

# 2) Start Field5 (same way you run Field4)
# Example (adjust to your runner):
cd ~/ariannamethod/async_field_forever/field5
python3 -u field_core.py  # or use your existing launcher
```

Notes:
- This copies the current Field4 tree into ~/.../field5.
- Config overrides are appended to field5/config.py under "# FIELD5 OVERRIDES".
- A field_metrics table is created in resonance.sqlite3 if missing.

## What's different vs Field4 (initial v1)
- UPDATE_ORDER=random (fair async)
- TICK_BARRIER=True (compute-then-commit per tick)
- Minimal viable population NMIN=10 + Hall-of-Fame HOF_SIZE=8
- Soft ecology levers prepared: ENERGY_INFLOW/OUTFLOW (for chemostat)
- Extinction cooldown and kill-switch MAX_DF_DT for catastrophic drops

These are appended as constants; integration points are documented for next iterations.

## Metrics & A/B
Track for ≥7 days:
- Extinction frequency per 1000 ticks
- Mean/variance of population, births, deaths
- Novelty and niche count (when implemented)
- Time-to-collapse

SQL examples:
```sql
-- last 1000
SELECT COUNT(*) FROM field_state WHERE cell_count=0;
SELECT AVG(cell_count), AVG(births), AVG(deaths) FROM field_state;
```

Decision: if Field5 is more stable/interesting, graduate; else, delete sandbox folder (no regrets).
