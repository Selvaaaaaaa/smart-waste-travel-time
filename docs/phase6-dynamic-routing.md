# Phase 6 — Dynamic Real-Time Route Rerouting & Optimization Engine

> [!NOTE]
> **Simulation Disclaimer**: This is a deterministic simulation and research prototype. It does not represent live municipal routing or live GPS data.

## Architecture Overview

The Phase 6 routing intelligence layer consists of five modular components:

```
+-------------------------------------------------------------------------+
|                      DETERMINISTIC MUNICIPAL GRAPH                      |
|          (14 Nodes, Directed Edges, Speed Limits, Dynamic Congestion)    |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                        CANDIDATE ROUTE GENERATOR                        |
|  [SHORTEST_PATH, AVOID_TRAFFIC, AVOID_CLOSURE, AVOID_WEATHER, BALANCED] |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                     ADAPTIVE HYBRID ETA PREDICTION                      |
|           (Phase 5 Hybrid Model: Baseline + Random Forest Ensemble)     |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                   SAFETY-FIRST MULTI-OBJECTIVE SCORING                  |
|   Hard Gates: Max Payload, Driver Shift Hours, Impassable Closures      |
|   Formula: Score = 0.50*(ETA/Max) + 0.30*(Dist/Max) + 0.20*(Penalty)   |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                         REROUTING EVENT AUDITING                        |
|          (Full Decision Rationale, Time Saved, Distance Impact)         |
+-------------------------------------------------------------------------+
```

## Mathematical Scoring Formulation

For every candidate path $p_k \in \mathcal{P}$:

$$\text{Score}(p_k) = w_1 \cdot \frac{\text{ETA}(p_k)}{\max_{j} \text{ETA}(p_j)} + w_2 \cdot \frac{\text{Dist}(p_k)}{\max_{j} \text{Dist}(p_j)} + w_3 \cdot \text{Penalty}_{\text{env}}(p_k)$$

Subject to:
1. $W_{\text{current}} + W_{\text{remaining}} \le C_{\text{vehicle}}$
2. $T_{\text{elapsed}} + \text{ETA}(p_k) \le T_{\text{max\_shift}}$
3. $e \notin \mathcal{E}_{\text{blocked}} \quad \forall e \in p_k$
