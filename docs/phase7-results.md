# PHASE 7 — FLEET COORDINATION BENCHMARK RESULTS

> **SIMULATION & RESEARCH DISCLAIMER**:
> This is a deterministic simulation and research prototype. It does not represent live municipal dispatch or real-time GPS tracking. All metrics below are computed from actual execution outputs of the 35 benchmark simulation runs.

---

## 1. Executive Summary

- **Research Question**: Can a fleet-level coordination system dynamically assign waste collection tasks to the safest and most efficient available vehicle while responding to vehicle overload, disruption, delay, breakdown, and emergency waste requests?
- **Fleet Size**: 6 Operational Municipal Vehicles (Capacities: 6,000 kg – 12,000 kg)
- **Road Network Topology**: 14 Municipal Nodes (Depot, Transfer Hubs, Collection Zones, Intersections, Regional Landfill)
- **Scenarios Evaluated**: 7 Stress Scenarios
- **Deterministic Seeds**: 5 Repetitions (`[42, 43, 44, 45, 46]`)
- **Total Experiment Runs**: **35 Simulation Runs**

---

## 2. Key Aggregate Metrics

| Metric | Measured Value | Standard / Target | Status |
| :--- | :--- | :--- | :--- |
| **Task Assignment Success Rate** | **100.0%** | $\ge 90.0\%$ | Optimal |
| **Safe Assignment Rate** | **100.0%** | $100.0\%$ | Flawless |
| **Unsafe Assignments Prevented** | **255** | $> 0$ | Verified |
| **Average Assignment ETA** | **43.45 min** | $< 60.0$ min | Feasible |
| **Average Fleet Travel Time** | **277.81 min** | Nom. Shift Limit | Sustainable |
| **Average Fleet Distance** | **78.09 km** | Municipal Area | Efficient |
| **Emergency Request Fulfillment Rate** | **100.0%** | $\ge 95.0\%$ | Optimal |
| **Vehicle Breakdown Recovery Rate** | **100.0%** | $100.0\%$ | Flawless |
| **Average Fleet Vehicle Utilization** | **43.40%** | Balanced Load | Optimal |
| **Fleet Utilization Variance** | **480.55** | Stable Distribution | Controlled |
| **Fleet Load Balance Score** | **0.7827** | $> 0.70$ (1.0 = Perfect) | High Balance |
| **Total Reassignments Executed** | **10** | Event-Driven | Minimal Detour |
| **Average Rebalancing Improvement** | **5.20 min** | $> 0$ | Positive Gain |
| **Unassigned Task Rate** | **0.0%** | $0.0\%$ | Complete Fulfillment |

---

## 3. Scenario-Level Breakdown

All 7 scenarios were evaluated across the 5 deterministic seeds (seeds 42, 43, 44, 45, 46):

| Scenario Name | Success Rate (%) | Safe Rate (%) | Avg ETA (min) | Mean Utilization (%) | Load Balance Score | Unsafe Prevented | Reassignments |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **NORMAL_FLEET** | 100.0% | 100.0% | 28.72 | 36.55% | 0.7728 | 15 | 0 |
| **HIGH_WASTE_FLEET** | 100.0% | 100.0% | 31.02 | 72.14% | 0.8508 | 70 | 0 |
| **VEHICLE_BREAKDOWN** | 100.0% | 100.0% | 28.72 | 39.05% | 0.7810 | 15 | 5 |
| **EMERGENCY_REQUEST** | 100.0% | 100.0% | 27.94 | 39.05% | 0.7810 | 20 | 0 |
| **ROAD_CLOSURE_FLEET** | 100.0% | 100.0% | 64.98 | 36.55% | 0.7728 | 15 | 0 |
| **DRIVER_SHIFT_WARNING**| 100.0% | 100.0% | 31.00 | 36.25% | 0.7640 | 90 | 0 |
| **COMBINED_FLEET_STRESS**| 100.0% | 100.0% | 91.79 | 44.19% | 0.7565 | 30 | 5 |

---

## 4. Safety Gate & Failure Analysis

Throughout the 35 benchmark evaluations:
- **255 unsafe vehicle-task assignments** were detected and filtered out prior to scoring.
- **Breakdown Scenarios**: In `VEHICLE_BREAKDOWN` and `COMBINED_FLEET_STRESS`, 100% of affected tasks were successfully transferred to alternative safe vehicles with sufficient payload headroom and shift availability.
- **Overload Prevention**: In `HIGH_WASTE_FLEET`, 70 capacity-exceeding allocations were blocked, successfully preventing any truck from exceeding its rated capacity.
- **Labor Fatigue Gate**: In `DRIVER_SHIFT_WARNING`, 90 assignments that would have breached the 8-hour consecutive shift limit were rejected, routing tasks exclusively to fresh drivers.
- **Zero Unsafe Leaks**: Zero unsafe vehicle-task combinations entered the final selection stage across all 35 runs.

---

## 5. Research Conclusions & Limitations

1. **Answer to Core Research Question**: Yes. A centralized, multi-criteria coordination engine that couples strict physical safety gates with Adaptive Hybrid ETA can dynamically coordinate multiple collection vehicles with 100% safety adherence, recovering smoothly from sudden breakdowns, heavy rain, closures, and emergency demand surges.
2. **Deterministic Simulation Boundary**: This benchmark is evaluated on a synthetic 14-node directed graph and deterministic simulation framework. Real-world municipal deployments involve unpredictable driver dwell times, bin contamination, and dynamic traffic signals not captured in this prototype.
