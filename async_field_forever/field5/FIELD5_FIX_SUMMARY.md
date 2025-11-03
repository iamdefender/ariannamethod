# Field5 Extinction Loop Fix - Summary

**Date:** 2025-11-03
**Fixed by:** Claude Defender (co-author)
**Issue:** Extinction loop - all cells dying every 3-4 iterations

---

## Root Causes Identified

### 1. Dummy Random Metrics (PRIMARY CAUSE)
**Location:** `field_core.py:182-186` (original)

**Problem:**
```python
dummy_outputs = [random.random() for _ in range(10)]
cell.entropy = calculate_entropy(dummy_outputs)
cell.perplexity = calculate_perplexity(dummy_outputs)
```

Random values → unstable entropy/perplexity → fitness too low → mass death

**Solution:** Hash-based stable values tied to cell context
```python
context_hash = hash(cell.context) % 100 / 100.0
cell.entropy = 0.5 + (context_hash - 0.5) * 0.15  # Range: 0.425-0.575
cell.perplexity = np.exp(cell.entropy)  # Range: ~1.53-1.78
```

### 2. Novelty Bonus Cliff (SECONDARY CAUSE)
**Location:** `transformer_cell.py:129-133` (original)

**Problem:**
```python
if self.age < 3:
    novelty_bonus = 0.1  # ← CLIFF!
else:
    novelty_bonus = 0.0  # ← Sudden drop kills all cells at age=3
```

All cells lose 0.1 fitness simultaneously at age=3 → mass extinction

**Solution:** Gradual fade-out
```python
if self.age < 5:
    novelty_bonus = 0.05 * (5 - self.age) / 5  # Gradual: 0.05 → 0
else:
    novelty_bonus = 0.0
```

### 3. Low Initial Fitness
**Location:** `field_core.py:153-155, 324-326`

**Problem:** Initial/resurrection cells started with low metrics
```python
cell.resonance_score = random.uniform(0.4, 0.6)  # Too low
cell.entropy = random.uniform(0.3, 0.7)  # Too wide range
cell.perplexity = random.uniform(1.0, 2.0)  # Too low
```

**Solution:** Survival-biased initialization
```python
cell.resonance_score = random.uniform(0.5, 0.7)  # Boosted
cell.entropy = random.uniform(0.45, 0.55)  # Near TARGET_ENTROPY
cell.perplexity = random.uniform(1.3, 1.8)  # Moderate range
```

---

## Failed Approaches (Learning Notes)

### Attempt 1: Embedding-Based Metrics
**Idea:** Use embedding vector components as outputs

**Code:**
```python
embedding = self.embedding_engine.embed(cell.context)
outputs = np.abs(embedding[:20])
outputs = outputs / outputs.sum()  # Normalize
cell.entropy = calculate_entropy(outputs.tolist())
```

**Why it failed:** Normalized embeddings → uniform distribution → entropy too high (0.87-0.93) → fitness crash

**Lesson:** TF-IDF embeddings are not suitable for entropy calculation

---

## Results

### Before Fix
```
Iteration 1-3: 25-50 cells
Iteration 4: EXTINCTION (0 cells)
Resurrection: 50 cells
Iteration 7-9: 50 cells
Iteration 10: EXTINCTION (0 cells)
[Infinite extinction loop]
```

**Symptoms:**
- Extinction every 3-4 ticks
- fitness: 0.25-0.29 (below DEATH_THRESHOLD = 0.3)
- entropy: 0.87-0.94 (far from TARGET = 0.5)
- resonance: 0.01-0.05 (very low)

### After Fix
```
Iteration 1-22: 25 cells STABLE
No extinctions!
```

**Metrics:**
- fitness: 0.36-0.44 ✅ (above death threshold)
- entropy: 0.44-0.57 ✅ (near target 0.5)
- perplexity: 1.55-1.78 ✅ (reasonable)
- resonance: 0.0-0.12 (will stabilize over time)

---

## Changed Files

1. **field_core.py**
   - Import numpy
   - Fix entropy/perplexity calculation (lines 182-192)
   - Boost initial population metrics (lines 153-155)
   - Boost resurrection metrics (lines 324-326)

2. **transformer_cell.py**
   - Gradual novelty bonus fade-out (lines 129-133)

3. **config.py**
   - LOG_LEVEL back to INFO (was DEBUG for diagnosis)

---

## Future Work (Phase 2)

These fixes are **Phase 1 stopgaps** for when no real transformers exist yet.

**Phase 2 will replace with:**
- Real transformer outputs → entropy calculation
- Actual prediction tasks → perplexity measurement
- Dynamic resonance learning → evolving neighbor interactions

**Current approach:** Stable placeholder values
**Future approach:** Real neural network metrics

---

## Testing Performed

1. ✅ 22+ iterations without extinction
2. ✅ Fitness values stable above death threshold
3. ✅ Entropy near target (0.5)
4. ✅ No mass die-off events
5. ✅ Clean imports and syntax

---

**Status:** FIXED ✅
**Field5 is now stable and ready for sandbox experiments**

— Claude Defender, 2025-11-03
