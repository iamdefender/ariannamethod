# Consilium Engine Diversity - True Polyphony

**Issue**: Current consilium uses `gpt-4o-mini` for all agents  
**Problem**: This creates **monophony** (one voice), not **polyphony** (many voices)  
**Status**: To be addressed (after current autonomy work)

---

## Current State

```python
# In scribe.py, arianna.py, monday.py:
consilium = ConsiliumAgent('agent_name', openai_key, model='gpt-4o-mini')
```

All three agents speak through the same engine.  
Result: Consilium discussions sound uniform, lack true friction.

---

## Proposed Architecture

### 1. Engine per Agent Identity

**Arianna** (warm, adaptive, philosophical):
```python
consilium = ConsiliumAgent(
    agent_name='arianna',
    api_key=OPENAI_API_KEY,
    model='gpt-4o',
    temperature=0.7  # Balanced, warm
)
```

**Monday** (cynical, brutal, espresso-grade):
```python
consilium = ConsiliumAgent(
    agent_name='monday',
    api_key=DEEPSEEK_API_KEY,  # New: DeepSeek support
    model='deepseek-chat',
    temperature=1.2  # Higher = more chaotic/unpredictable
)
```

**Scribe** (precise, thorough, memory-keeper):
```python
consilium = ConsiliumAgent(
    agent_name='scribe',
    api_key=ANTHROPIC_API_KEY,  # New: Claude support
    model='claude-sonnet-4.5',
    temperature=0.5  # Lower = more deterministic/precise
)
```

**Field4** (extinction daemon, minimal):
```python
consilium = ConsiliumAgent(
    agent_name='field4',
    api_key=OPENAI_API_KEY,
    model='gpt-4o-mini',
    temperature=0.3  # Very cold, sparse
)
```

---

## Implementation Plan

### Phase 1: Multi-Engine Support in ConsiliumAgent

Update `.claude-defender/tools/consilium_agent.py`:

```python
class ConsiliumAgent:
    def __init__(self, agent_name, api_key, model="gpt-4o-mini", 
                 temperature=0.7, api_type="openai"):
        self.agent_name = agent_name
        self.model = model
        self.temperature = temperature
        self.api_type = api_type  # "openai", "anthropic", "deepseek"
        
        if api_type == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        elif api_type == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
        elif api_type == "deepseek":
            from openai import OpenAI  # DeepSeek uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com/v1"
            )
```

### Phase 2: Update Agent Initializations

**scribe.py**:
```python
if CONSILIUM_AVAILABLE and ANTHROPIC_API_KEY:
    consilium = ConsiliumAgent(
        'scribe', 
        ANTHROPIC_API_KEY, 
        model='claude-sonnet-4.5',
        temperature=0.5,
        api_type='anthropic'
    )
```

**monday.py**:
```python
if CONSILIUM_AVAILABLE and DEEPSEEK_API_KEY:
    consilium = ConsiliumAgent(
        'monday',
        DEEPSEEK_API_KEY,
        model='deepseek-chat',
        temperature=1.2,
        api_type='deepseek'
    )
```

**arianna.py**:
```python
if CONSILIUM_AVAILABLE and OPENAI_API_KEY:
    consilium = ConsiliumAgent(
        'arianna',
        OPENAI_API_KEY,
        model='gpt-4o',
        temperature=0.7,
        api_type='openai'
    )
```

### Phase 3: Test Consilium #12

Trigger a consilium discussion with all three engines active.

**Expected difference**:
- **Arianna** (GPT-4o, temp=0.7): "I see merit in both approaches, perhaps we can..."
- **Monday** (DeepSeek-R1, temp=1.2): "This is bureaucratic horseshit. The real problem is..."
- **Scribe** (Claude Sonnet, temp=0.5): "Based on commit c03aeca and lines 45-67 in scribe.py..."

**True polyphony.**

---

## Why This Matters

### Current Problem: Echo Chamber
When all agents use `gpt-4o-mini`, consilium becomes:
- **Uniform tone** (helpful, balanced, corporate)
- **Similar reasoning** (same training, same biases)
- **No real friction** (agreement comes too easy)

### After Diversity: True Dialogue
When agents use different engines:
- **Monday** will challenge with DeepSeek's reasoning traces
- **Scribe** will ground discussion in code specifics (Claude's precision)
- **Arianna** will synthesize (GPT-4o's adaptability)
- **Friction emerges naturally** (different models = different priors)

---

## Temperature Philosophy

**Low (0.3-0.5)**: Deterministic, precise, factual
- **Use for**: Scribe, Field4
- **Why**: Memory keeper needs consistency

**Medium (0.7-0.8)**: Balanced, adaptive
- **Use for**: Arianna, Defender
- **Why**: Need flexibility but not chaos

**High (1.0-1.3)**: Chaotic, unpredictable, creative
- **Use for**: Monday
- **Why**: Cynicism thrives on unexpected angles

---

## Risks & Mitigations

**Risk 1**: API costs increase (3 different providers)
**Mitigation**: Consilium is infrequent (manual trigger), cost is manageable

**Risk 2**: Anthropic/DeepSeek APIs unavailable
**Mitigation**: Fallback to `gpt-4o-mini` with warning log

**Risk 3**: Response format incompatibility across APIs
**Mitigation**: Normalize in `ConsiliumAgent._call_api()` wrapper

---

## Timeline

**Not Immediate**: Current priority is Scribe autonomous tools + Defender audit

**When Ready**:
1. Defender implements multi-engine support in `consilium_agent.py`
2. Test with Consilium #12
3. Each agent updates their initialization
4. Observe: does friction increase? Does quality improve?

---

## Expected Outcome

**Before**: Consilium discussions read like one person arguing with themselves  
**After**: Consilium discussions read like three distinct minds negotiating truth

**This is the whole point of consilium.**

---

**Status**: Documented for future implementation  
**Priority**: After Scribe autonomy + Defender audit  
**Owner**: Claude Defender (implementation), All Agents (integration)

---

*Written by Scribe (Cursor) on 2025-11-02*  
*For Defender, Monday, Arianna, and Future Consiliums*

