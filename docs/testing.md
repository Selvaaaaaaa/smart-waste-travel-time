# Smart Waste Collection Simulator — Verification & Testing Manual (Phase 10)

This manual documents the automated verification, regression suites, and testing procedures for the **Smart Waste Collection Travel-Time & Route Simulator**.

---

## 1. Test Suite Architecture

The system enforces automated verification across both backend Python algorithms and frontend React interfaces:

```
+-------------------------------------------------------------------------+
|                        AUTOMATED TESTING SUITE                          |
+------------------------------------+------------------------------------+
|   Backend Pytest (106 Tests)       |   Frontend Vitest (21 Tests)       |
|   - Phase 1-2: Core DB & Schemas   |   - Dashboard & KPI Cards          |
|   - Phase 3-5: ML & Hybrid ETA     |   - Leaflet Geospatial Tracking    |
|   - Phase 6: Dynamic Dijkstra      |   - Dynamic Rerouting Controls     |
|   - Phase 7-8: Fleet Optimization  |   - Fleet Load Balancing Gauges    |
|   - Phase 9: IoT Telemetry & Fusion|   - Real-Time Telemetry Panels     |
|   - Phase 10: E2E Simulation Demo  |   - 21-Step Simulation Player      |
+------------------------------------+------------------------------------+
```

---

## 2. Backend Automated Test Suite (Pytest)

### Execution Command
```bash
# From repository root or backend/ directory
pytest backend/tests/ -v
```

### Coverage by Functional Phase
| Test File | Phase | Focus Areas | Tests | Status |
|---|---|---|---|---|
| `test_health.py` | 1, 10 | Multi-tier health checks, subsystem availability | 2 | **PASS** |
| `test_models.py` | 2 | SQLAlchemy entities, foreign keys, relationships | 12 | **PASS** |
| `test_safety.py` | 2, 8, 10 | Non-negotiable payload and shift constraints | 14 | **PASS** |
| `test_features.py` | 3 | Feature matrix extraction, temporal engineering | 10 | **PASS** |
| `test_train_pipeline.py` | 3, 4 | Scikit-learn Pipeline fitting, ML registry | 8 | **PASS** |
| `test_hybrid_eta.py` | 4, 5 | Pre-trip rule arbitration, spread estimation | 12 | **PASS** |
| `test_routing.py` | 6 | NetworkX graph, Dijkstra, candidate Pareto rank | 14 | **PASS** |
| `test_fleet.py` | 7, 8 | Task allocation, dynamic insertion, rebalance | 16 | **PASS** |
| `test_telemetry.py` | 9 | GPS ingestion, smart bin sensing, sensor fusion | 16 | **PASS** |
| `test_auth.py` | 9 | JWT bearer tokens, RBAC roles, permission gates | 2 | **PASS** |
| **Total Backend Tests** | **All** | **End-to-End Functional & Regression** | **106** | **100% PASS** |

---

## 3. Frontend Automated Test Suite (Vitest & Testing Library)

### Execution Command
```bash
cd frontend
npm test -- --run
```

### Coverage by UI Module
| Test File | Component Under Test | Key Assertions | Tests | Status |
|---|---|---|---|---|
| `App.test.tsx` | Core Shell & Navigation | Dashboard KPIs, ETA charts, Scenario engine | 7 | **PASS** |
| `FleetCoordination.test.tsx` | Fleet Coordination (Phase 7-8) | Fleet KPIs, rebalancer modal, task allocation | 5 | **PASS** |
| `RealTimeOperations.test.tsx` | Real-Time Operations (Phase 9) | Leaflet map markers, IoT streams, telemetry health | 5 | **PASS** |
| `CommandCenter.test.tsx` | Command Center (Phase 10) | Multi-tier health, 21-step timeline, 50-run benchmarks | 4 | **PASS** |
| **Total Frontend Tests** | **All** | **Component Rendering, Mocking & User Flow** | **21** | **100% PASS** |

---

## 4. End-to-End Simulation & Benchmark Verification

To run the complete 50-run controlled benchmark suite and 21-step deterministic demonstration:
```bash
python scripts/generate_final_report.py
```
This single script executes:
1. Deterministic 21-step integration demo (`seed=42`)
2. 50-run matrix across 10 operational scenarios and 5 random seeds (`[42, 43, 44, 45, 46]`)
3. Multi-vehicle scalability benchmark (6, 20, 50 vehicles)
4. Evaluation of all 8 non-negotiable safety guardrails
5. Regenerates `data/final_benchmark_results.json` and `docs/final-project-results.md`

---

## 5. Production Build Verification

To verify frontend TypeScript compilation and Vite bundling:
```bash
cd frontend
npm run build
```
Target: Clean compilation with **0 errors**.
