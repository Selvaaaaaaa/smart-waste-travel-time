# Phase 4 Empirical Research Results: Model Evaluation, Failure-Case Analysis & Safety Benchmarks

*Generated automatically on 2026-09-04T11:25:25.154821 from 30 controlled deterministic experiment runs.*

---

## 1. Executive Summary & Core Research Question

> **Research Question:** *"Does incorporating weather, traffic, events, road restrictions, waste volume, and temporal context improve travel-time prediction compared with a simple baseline?"*

Across **30 total experiment runs** evaluating the 6 standard operational stress scenarios:
- **Baseline Global MAE:** **51.51 minutes**
- **Context-Aware Global MAE:** **34.85 minutes**
- **Overall MAE Improvement:** **32.34% reduction in mean absolute error**
- **Baseline Global RMSE:** **71.08 minutes**
- **Context-Aware Global RMSE:** **41.69 minutes**
- **Overall RMSE Improvement:** **41.35% reduction in variance**
- **Predictions within $\pm 10$ minutes:** Baseline **16.67%** vs Context-Aware **13.33%**

---

## 2. Data Science & Dataset Integrity Validation

Before benchmark execution, the observation dataset underwent rigorous data science validation:
- **Total Database Records:** 60
- **Duplicate Observations:** 0
- **Missing Target Values:** 0
- **Negative Travel Durations:** 0
- **Negative Distances:** 0
- **Data Quality Status:** PASS (100% valid physical measurements)

> **Research Disclaimer:** *Performance is evaluated on the available synthetic dataset and serves as an academic research prototype. Predictions should not be interpreted as live production GPS telematics.*

---

## 3. Scenario-Level Empirical Comparison

| Operational Scenario | Baseline MAE | Context MAE | Baseline RMSE | Context RMSE | MAE Improvement | Winner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Normal Conditions** | 14.91 min | 30.18 min | 15.08 min | 30.25 min | -102.41% | `BASELINE` |
| **Heavy Rain** | 23.87 min | 36.24 min | 24.54 min | 36.51 min | -51.82% | `BASELINE` |
| **Major Event** | 71.98 min | 31.06 min | 72.82 min | 33.19 min | 56.85% | `CONTEXT_AWARE` |
| **Road Closure** | 44.3 min | 7.13 min | 44.83 min | 7.99 min | 83.91% | `CONTEXT_AWARE` |
| **High Waste Volume** | 7.25 min | 28.87 min | 7.34 min | 28.94 min | -298.21% | `BASELINE` |
| **Combined Stress** | 146.73 min | 75.62 min | 148.72 min | 78.58 min | 48.46% | `CONTEXT_AWARE` |

### Key Scenario Insights:
- **Best Performing Context-Aware Scenario:** **Road Closure** (83.91% MAE reduction)
- **Worst Performing / Failure-Prone Scenario:** **High Waste Volume** (-298.21% MAE reduction)
- **Scientific Observation:** The deterministic baseline outperforms the context-aware model during nominal/normal conditions where standard speed heuristics hold true without environmental noise. Context-aware models demonstrate clear superiority under extreme disruptions (e.g. Major Events and Road Closures).

---

## 4. Operational Safety & Constraint Enforcement

Safety is evaluated separately from prediction accuracy. Unsafe assignments are strictly rejected and never credited with efficiency scores:
- **Total Assignments Evaluated:** 30
- **Safe Assignments:** 30
- **Unsafe Assignments Blocked:** 0
- **Safety Principle:** *Efficiency is not gained through unsafe assignments.* In the `COMBINED_STRESS` scenario, gross payload limits trigger `UNSAFE_ASSIGNMENT` (`PAYLOAD_CAPACITY_EXCEEDED`).

---

## 5. Failure-Case Analysis & Classification

A run is classified as a failure case when context-aware error exceeds baseline error, exceeds the +/- 10 min operational tolerance, or violates safety bounds.

- **Total Failure Cases Detected:** **26** / 30 (86.67%)

### Failure Reason Breakdown
| Failure Category | Frequency |
| :--- | :--- |
| `CONTEXT_MISMATCH` | 10 |
| `RARE_CONDITION` | 5 |
| `ROAD_RESTRICTION_MISMATCH` | 6 |
| `WEATHER_IMPACT_MISMATCH` | 5 |

### Top Largest Context-Aware ETA Errors
| Rank | Scenario | Route | Predicted ETA | Actual ETA | Absolute Error | Failure Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| #1 | Combined Stress | R-103 | 126.79 min | 230.97 min | **104.18 min** | `RARE_CONDITION` |
| #2 | Combined Stress | R-105 | 126.3 min | 212.13 min | **85.83 min** | `RARE_CONDITION` |
| #3 | Combined Stress | R-101 | 114.61 min | 198.87 min | **84.26 min** | `RARE_CONDITION` |
| #4 | Combined Stress | R-102 | 97.77 min | 158.8 min | **61.03 min** | `RARE_CONDITION` |
| #5 | Major Event | R-103 | 93.22 min | 140.0 min | **46.78 min** | `ROAD_RESTRICTION_MISMATCH` |
| #6 | Heavy Rain | R-104 | 86.13 min | 43.2 min | **42.93 min** | `WEATHER_IMPACT_MISMATCH` |
| #7 | Combined Stress | R-104 | 96.26 min | 139.06 min | **42.8 min** | `RARE_CONDITION` |
| #8 | Heavy Rain | R-105 | 114.48 min | 75.71 min | **38.77 min** | `WEATHER_IMPACT_MISMATCH` |
| #9 | Major Event | R-105 | 90.72 min | 128.08 min | **37.36 min** | `ROAD_RESTRICTION_MISMATCH` |
| #10 | Heavy Rain | R-102 | 88.31 min | 52.04 min | **36.27 min** | `WEATHER_IMPACT_MISMATCH` |

---

## 6. Research Limitations & Future Work
1. **Synthetic Environment:** Synthetic distributions make some extreme disruptions easier to predict than real-world chaotic telemetry.
2. **Dynamic Detours:** Road closure rerouting delays are currently modeled through parameterized physical delay distributions rather than live road graph pathfinding.
3. **Multi-Model Ensembles:** Future phases should explore blending simple baseline predictions for nominal conditions with ML for heavy disruption states.
