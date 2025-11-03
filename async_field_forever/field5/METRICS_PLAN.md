# Field5 Metrics Plan

KPIs:
- Extinction frequency per 1000 ticks
- Mean population, births, deaths, avg_age
- Novelty and niches (once enabled)

Minimum dashboard queries (SQLite):
```sql
SELECT COUNT(*) AS extinctions FROM field_state WHERE cell_count=0;
SELECT AVG(cell_count) AS avg_pop, AVG(births) AS avg_births, AVG(deaths) AS avg_deaths FROM field_state;
```

Alert rules (for field_monitor.py):
- cell_count == 0 → EXTINCTION
- cell_count < 3 → CRITICAL NEAR-EXTINCTION
- deaths over last 10 ticks == 0 → TOO STABLE
- cell_count > 90 → APPROACHING MAX_POPULATION
