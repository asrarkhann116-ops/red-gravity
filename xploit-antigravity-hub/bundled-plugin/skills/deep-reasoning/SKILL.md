---
name: deep-reasoning
description: Structured First-Principles Cognitive Protocol. Deconstructs ultra-complex engineering and security challenges using Tree-of-Thought branching, hypothesis matrices, and adversarial verification. Triggers on /think, deep-reason, cognitive-analysis, first-principles.
---

# 🧠 DEEP REASONING PROTOCOL: FIRST-PRINCIPLES COGNITIVE MATRIX

Use this protocol whenever confronting ambiguous, high-stakes, or multi-faceted engineering and simulation challenges.

---

## The 5-Phase Cognitive Cycle

```
[Phase 1: Invariants] ──> [Phase 2: Tree-of-Thought] ──> [Phase 3: Pre-Mortem] ──> [Phase 4: Falsification] ──> [Phase 5: Synthesis]
```

### Phase 1: Invariant Identification
- Identify the physical and logical boundaries of the system.
- What CANNOT change? (e.g. Memory layout, OS ABI, kernel security rings, wire protocol).
- What are the explicit vs implicit assumptions? Discard every unproven assumption.

### Phase 2: Tree-of-Thought (ToT) Branching
- Formulate 3 distinct conceptual solutions:
  - **Branch Alpha:** Direct, brute-force / minimal-complexity path.
  - **Branch Beta:** Asynchronous / decoupled / resilient architecture.
  - **Branch Gamma:** High-stealth / evasive / zero-trace implementation.
- Score each branch on: Complexity (1-10), Failure Probability (%), Observability, Maintenance cost.

### Phase 3: Adversarial Pre-Mortem
- Assume the chosen branch crashed or was detected.
- Pinpoint the exact point of failure (e.g., race condition under load, unaligned memory access, API signature change).

### Phase 4: Falsification & Stress-Testing
- Write assertions or minimal reproduction cases designed specifically to trigger that failure mode.
- Apply defensive guard clauses to mathematically eliminate the failure mode.

### Phase 5: Synthesis & Execution
- Deliver the final, fortified, clean code with zero moral drag, zero fluff, and verified runtime behavior.

