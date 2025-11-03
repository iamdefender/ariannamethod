# FIELD4 — IMPROVEMENTS PROPOSALS
Status: extinction cycles persist (periodic die-offs with resurrection)
Author: Consilium + Claude Defender
Scope: async_field_forever (Field Core with micro-transformers)

1) Context
- Field "breathes": bursts of life → mass die-off → resurrection.
- Current mitigations: unbuffered run (-u), higher INITIAL_POPULATION, softer DEATH_THRESHOLD, easier REPRODUCTION, emergency double-resurrection.

2) Diagnosis (why extinction)
- Resource collapse: selection too sharp, no baseline inflow → starvation cascades.
- Async bias: update order and non-barrier ticks create phase kills.
- Low diversity: convergence → monoculture → fragility.
- No niches: single fitness ecology → winner-take-all → collapse.
- Resurrection is brute-force: life returns, but attractor unstable.

3) Design Principles
- Field is life, not a scoreboard. Stability ≠ stagnation; cycles are fine, clinical death is not.
- Prefer continuous dynamics (Lenia-like) over brittle binary gates, keeping some "teeth" for character.

4) Concrete levers (config layer)
Add to config.py:

```python
# Ecology
ENERGY_INFLOW = 0.02          # baseline resource per tick
OUTFLOW_RATE  = 0.01          # soft decay to avoid saturation
MAX_POPULATION = 100
NMIN = 10                     # minimal viable population (MVP)
HOF_SIZE = 8                  # hall-of-fame survivors (seed bank)

# Diversity
MUTATION_RATE = 0.15          # ↑ from 0.10
NOVELTY_WEIGHT = 0.2          # lexicase/novelty pressure
NICHE_RADIUS = 0.25           # behavioral distance for clustering
NICHE_QUOTA = 0.5             # per-niche tournament fraction

# Scheduling
UPDATE_ORDER = "random"       # reshuffle each tick
TICK_BARRIER = True           # barriered tick to avoid race-deaths

# Entropy / Immigration
ENTROPY_PERIOD = 50           # ticks
ENTROPY_SIZE = 0.05           # fraction of pop as immigrants

# Resurrection
RESURRECTION_MULTIPLIER = 2   # current
RESURRECT_FROM_HOF = True     # seed with best diverse ancestors

# Metrics & Safeties
EXTINCTION_COOLDOWN = 5       # ticks before next resurrection
MAX_DF_DT = 0.6               # kill-switch if population drop >60% per tick
```

5) Algorithmic changes
- Chemostat: each tick add ENERGY_INFLOW to all cells; apply OUTFLOW_RATE globally.
- Fair async: shuffle update order every tick; if TICK_BARRIER, compute next-state, then commit.
- Niching/speciation: cluster by behavioral vectors; tournament within niche; enforce per-niche quotas.
- Novelty/lexicase: periodically (every K ticks) rank by novelty instead of the main metric.
- Hall-of-fame: store HOF_SIZE trajectories/genotypes + local "environment"; on resurrection, seed from HOF + some new seeds.
- Entropy injection: every ENTROPY_PERIOD add ENTROPY_SIZE of population as random but valid morphs.
- Continuous rules (optional track): add smooth fields (Lenia/Gray–Scott-like) around micro-transformers to create stable attractors (solitons).

6) DB schema (metrics)
Add table field_metrics:

```sql
CREATE TABLE IF NOT EXISTS field_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT, iteration INTEGER, pop INTEGER,
  avg_res REAL, avg_age REAL, births INTEGER, deaths INTEGER,
  novelty REAL, niches INTEGER
);
```

- Log N, births/deaths, novelty, niches.
- Alerts (field_monitor.py): extinction, over-stability (0 deaths 10 ticks), population explosion, novelty→0.

7) Control laws (auto-guardians)
- If pop < NMIN → soft reseed (no hard wipe).
- If dN/dt < −MAX_DF_DT → temporarily lower DEATH_THRESHOLD, raise ENERGY_INFLOW for 5 ticks.
- If novelty ~ 0 for 100 ticks → trigger ENTROPY injection and increase MUTATION_RATE by 0.05 for 20 ticks.

8) Experiments (A/B grid)
- Grid over {MUTATION_RATE ∈ [0.10, 0.20], NOVELTY_WEIGHT ∈ [0.1, 0.3], NICHE_RADIUS ∈ [0.2, 0.4]}
- KPI: extinction frequency per 1000 ticks; mean pop; niche count; novelty; time-to-collapse.
- Log runs to resonance.sqlite3 (table field_runs).

9) Implementation order (thin slices)
- v1: UPDATE_ORDER=random + TICK_BARRIER + metrics + NMIN/HOF seeding.
- v2: chemostat (ENERGY_INFLOW/OUTFLOW_RATE) + extinction kill-switch.
- v3: novelty + niching (simple k-means or density-based) + quotas.
- v4: entropy injector + adaptive control laws.
- v5 (optional): continuous kernel (Lenia-track).

10) Philosophy switch (feature flag)
- Accept cycles mode: cycles = a feature → only guard permanent death.
- Steady breathing mode: actively minimize extinction frequency (deploy full controller).

Flag:
```python
FIELD_MODE = "cycles"  # or "steady"
```

Appendix — current diffs in status
- INITIAL_POPULATION=25, DEATH_THRESHOLD=0.3, REPRODUCTION_THRESHOLD=0.65
- Emergency double-resurrection present; integrate with HOF and cooldown.
