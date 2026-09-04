# Smart Waste Collection Travel-Time & Route Simulator

> **Academic & Research Prototype Platform — Phase 6: Dynamic Real-Time Route Rerouting & Optimization Engine**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688.svg)](https://fastapi.tiangolo.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E.svg)](https://scikit-learn.org/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0.52-red.svg)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-1.19+-orange.svg)](https://alembic.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16--Alpine-336791.svg)](https://www.postgresql.org/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg)](https://tailwindcss.com)

---

## 1. Project Overview

The **Smart Waste Collection Travel-Time & Route Simulator** is an academic research platform designed to model, simulate, and predict municipal solid waste collection transit durations under dynamic environmental, logistical, and infrastructure conditions.

**Phase 6** introduces the **Dynamic Real-Time Route Rerouting & Optimization Engine**:
1. **Deterministic Simulated Road Graph**: 14 municipal nodes and directed edges with speed limits, distance metrics, and dynamic edge blockage/penalties.
2. **Candidate Route Generator**: Produces viable alternative paths using 5 distinct strategies (`SHORTEST_PATH`, `AVOID_TRAFFIC`, `AVOID_CLOSURE`, `AVOID_WEATHER`, `BALANCED`).
3. **Adaptive Hybrid ETA Integration**: Each candidate's travel time is predicted in real time via the Phase 5 Adaptive Hybrid ETA model.
4. **Safety-First Route Scoring**: Hard constraints strictly gate payload capacity, driver shift limits, and impassable closures. Optimization formula: $\text{Score} = 0.50 \cdot (\text{ETA} / \max) + 0.30 \cdot (\text{Dist} / \max) + 0.20 \cdot \text{Penalty}$.
5. **Interactive Frontend Live Simulation**: Dedicated Dynamic Routing page featuring live Leaflet maps, disruption injection, step progression, and 35-run empirical benchmark suite.
6. **Empirical Benchmarks**: Across 7 scenarios and 5 random seeds (35 total runs), Dynamic Rerouting achieves **5.93 minutes mean travel time savings (10.41% reduction)** and lifts safety compliance from 71.4% to **85.7%**.

> [!NOTE]
> **Simulation Disclaimer:** This is a deterministic simulation and research prototype. It does not represent live municipal routing or live GPS data.


---

## 2. Empirical Benchmark Evaluation Summary (Three-Model Matrix)

| Operational Scenario | Baseline MAE | Context MAE | Hybrid MAE | Baseline RMSE | Context RMSE | Hybrid RMSE | Empirical Winner | Hybrid Selection Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Normal Conditions** | 14.91 min | 29.81 min | **14.91 min** | 15.08 min | 29.87 min | **15.08 min** | `HYBRID (BASELINE)` | 100% Base / 0% Ctx |
| **Heavy Rain** | 23.87 min | 29.68 min | **29.68 min** | 24.54 min | 30.28 min | **30.28 min** | `BASELINE` | 0% Base / 100% Ctx |
| **Major Event** | 71.98 min | 16.03 min | **16.03 min** | 72.82 min | 18.94 min | **18.94 min** | `HYBRID (CONTEXT)` | 0% Base / 100% Ctx |
| **Road Closure** | 44.30 min | 7.06 min | **7.06 min** | 44.83 min | 8.36 min | **8.36 min** | `HYBRID (CONTEXT)` | 0% Base / 100% Ctx |
| **High Waste Volume** | 7.25 min | 30.35 min | **7.25 min** | 7.34 min | 30.48 min | **7.34 min** | `HYBRID (BASELINE)` | 100% Base / 0% Ctx |
| **Combined Stress** | 146.73 min | 74.62 min | **74.62 min** | 148.72 min | 77.93 min | **77.93 min** | `HYBRID (CONTEXT)` | 0% Base / 100% Ctx |

*Global Overall: Baseline MAE 51.51 min vs Context MAE 31.26 min vs **Hybrid MAE 24.92 min** (+51.62% improvement over Baseline, +20.28% improvement over Context-Aware alone).*

---

## 3. CLI Commands & Report Generation

### 1. Generate Automated Phase 5 Research Markdown Report
```bash
cd backend
python -m app.experiments.generate_phase5_report
# Generated at docs/phase5-hybrid-results.md
```

### 2. Train Context-Aware Model via CLI
```bash
cd backend
python -m app.ml.train --model-type random_forest --n-estimators 100 --random-state 42
```

### 3. Run FastAPI Backend
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
# OpenAPI Docs: http://127.0.0.1:8000/api/docs
```

### 4. Run React + Vite Frontend
```bash
cd frontend
npm run dev
# Dashboard, Experiments & Simulator: http://127.0.0.1:5173/
```

---

## 4. API Catalog (Phase 5 Extensions)

### ETA & Adaptive Hybrid Prediction
- `POST /api/eta/hybrid` — Pre-trip rule evaluation -> Adaptive Hybrid ETA calculation & spread estimation.
- `POST /api/eta/predict` — Return baseline, context-aware, and hybrid ETA predictions.
- `POST /api/experiments/run` — Controlled multi-repetition benchmark with hybrid support.
- `GET /api/experiments/results` — 3-model benchmark aggregation and selection rate breakdown.
- `GET /api/experiments/failures` — Failure case categorization.
- `GET /api/experiments/comparison` — Scenario-level 3-model comparison table.

---

## 5. Verification & Test Suites

### Backend Tests (pytest) — 57 Tests Passed
```bash
pytest backend/tests/ -v
```

### Frontend Tests (Vitest) — 6 Tests Passed
```bash
cd frontend
npm test
```

### Frontend Production Build
```bash
cd frontend
npm run build
```
