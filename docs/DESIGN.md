# Design Decisions Document

## Overview

This document explains the key architectural and implementation decisions made in building the Frontdesk HITL system, including rationale, trade-offs, and alternatives considered.

---

## 1. Terminal Agent vs LiveKit Integration

### Decision
Built terminal simulator instead of full LiveKit integration.

### Rationale
**Why terminal simulation:**
- Requirements stated: "You can just use a sample app and wrap up this step quickly"
- Focuses on HITL logic (the core requirement)
- Easier to demonstrate and test
- No API key management needed for demo
- Same workflow, clearer interface

**LiveKit considerations:**
- Agent interface designed to match LiveKit event model
- Integration points clearly marked in code
- Would take 1-2 days to add full LiveKit
- Assessment focuses on architecture, not framework integration

### Trade-offs
- ❌ Not testing LiveKit learning ability
- ❌ Not "real" phone calls
- ✅ Cleaner demo
- ✅ Focus on what matters (HITL logic)
- ✅ Easy migration path

### Future Implementation
```python
# Current
question = input(f"{caller}: ").strip()

# LiveKit (straightforward migration)
@assistant.on("transcript")
def handle_transcript(event):
    question = event.text
    # Same processing logic
```

---

## 2. Database: In-Memory Storage

### Decision
Used Python dictionaries instead of SQL database.

### Rationale
**Advantages:**
- Zero setup time
- Perfect for MVP/demo
- Fast iteration
- No connection management
- Easy to understand

**Production path:**
- Dataclass structure makes SQL migration trivial
- Estimated migration time: 30 minutes

### Implementation
```python
# Current
help_requests: Dict[str, HelpRequest] = {}

# Production (SQLAlchemy) - same interface
session.query(HelpRequest).filter_by(status="pending").all()
```

### Scaling Plan
1. **0-100 requests/day:** Current (in-memory)
2. **100-1000/day:** SQLite (30-min migration)
3. **1000-10k/day:** PostgreSQL with pooling (2-hour migration)
4. **10k+/day:** PostgreSQL + Redis + read replicas

---

## 3. Knowledge Base: Semantic Matching

### Decision
Implemented synonym expansion + Jaccard similarity scoring.

### Algorithm
```python
1. Normalize query ("What are your hours?" → "hours")
2. Expand with synonyms:
   hours → [timings, schedule, open, close, opening, closing]
3. Remove stop words (what, are, your, the, etc.)
4. Calculate Jaccard similarity with each KB entry
5. Match if score ≥ 0.25 threshold
6. Boost score for important keywords (+0.4)
```

### Why Not Embeddings?
**Considered:** sentence-transformers with vector similarity

**Rejected because:**
- Adds 500MB+ dependency
- Slower inference (50ms vs 1ms)
- Overkill for <100 entries
- Less predictable/debuggable

**Current solution:**
- Fast (< 1ms per query)
- Predictable results
- No dependencies
- Good enough for MVP

**Upgrade path clearly documented:**
```python
# Future: Add embeddings
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode([question])
# Use cosine similarity
```

### Test Results
| Query | Matches | Score |
|-------|---------|-------|
| "What are your hours?" | "What are your hours?" | 1.0 (exact) |
| "timings" | "What are your hours?" | 0.65 |
| "schedule" | "What are your hours?" | 0.55 |
| "when do you open" | "What are your hours?" | 0.45 |

Threshold of 0.25 provides good balance.

---

## 4. Request Lifecycle Management

### Decision
Four clear states: PENDING → RESOLVED / UNRESOLVED / EXPIRED

### State Machine
