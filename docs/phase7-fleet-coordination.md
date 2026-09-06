# Phase 7 — Multi-Vehicle Fleet Coordination & Dynamic Task Allocation

> **SIMULATION & RESEARCH DISCLAIMER**:
> This is a deterministic simulation and research prototype. It does not represent live municipal fleet dispatch or real-time GPS tracking.

---

## 1. Research Objective

Phase 7 investigates the foundational question:
> *"Can a fleet-level coordination system dynamically assign waste collection tasks to the safest and most efficient available vehicle while responding to vehicle overload, disruption, delay, breakdown, and emergency waste requests?"*

Instead of the single-vehicle routing paradigm evaluated in Phase 6 ($1 \text{ Vehicle} \to 1 \text{ Route}$), Phase 7 orchestrates multiple operational vehicles simultaneously over a unified municipal graph topology:
$$\text{Multiple Vehicles} \longrightarrow \text{Available Tasks} \longrightarrow \text{Fleet State} \longrightarrow \text{Task Allocation} \longrightarrow \text{Route Optimization} \longrightarrow \text{Safety Validation} \longrightarrow \text{Dynamic Rebalancing}$$

---

## 2. Fleet Architecture & Domain Models

The fleet coordination engine is organized into modular services under `backend/app/fleet/`:

```
backend/app/fleet/
├── fleet_state.py           # FleetStateManager: vehicle positions, payload, driver work
├── fleet_scoring.py         # Multi-criteria scoring & hard safety gate
├── task_insertion.py        # Dynamic route insertion algorithm for emergency tasks
├── task_allocator.py        # Candidate filtering, Hybrid ETA prediction, winner ranking
├── fleet_rebalancer.py      # Event-driven rebalancing on breakdown, overload, or delay
├── fleet_optimizer.py       # Global batch scheduling & load balance optimization
├── fleet_experiments.py     # 35-run deterministic benchmark harness
└── fleet_service.py         # DB orchestration, simulation steps, and audit logging
```

### Vehicle State Transitions
Vehicles dynamically transition between discrete operational states:
- `AVAILABLE`: Idle at depot or terminal, zero payload, full availability.
- `ASSIGNED`: Allocated a scheduled or emergency collection mission.
- `EN_ROUTE`: Actively traversing graph edges toward next collection node.
- `AT_STOP`: Stationed at collection zone loading waste.
- `LOADING`: Performing compaction and waste pickup.
- `RETURNING`: En route to disposal facility (Regional Landfill).
- `OVERLOADED`: Payload capacity exceeded; locked from further assignments.
- `BREAKDOWN`: Mechanical failure; tasks released and redistributed.
- `OFF_DUTY`: Driver fatigue ceiling reached; vehicle taken out of rotation.

### Overload Thresholds
- $< 80\%$: `NORMAL`
- $80\% - 95\%$: `WARNING`
- $95\% - 100\%$: `CRITICAL`
- $> 100\%$: `OVERLOADED` (Triggers hard task rejection and fleet rebalancing)

---

## 3. Strict Safety Constraints (Hard Filtering)

Safety is enforced as a **hard gate**, evaluated **before** scoring or ranking:

1. **Vehicle Operational Status**: Vehicles in `BREAKDOWN`, `MAINTENANCE`, `OFF_DUTY`, or `OVERLOADED` are rejected unconditionally.
2. **Payload Capacity Bound**:
   $$\text{Current Payload} + \text{Task Waste} \le \text{Vehicle Rated Capacity}$$
   If projected payload exceeds rated gross capacity, the candidate is rejected with `CAPACITY_EXCEEDED`.
3. **Driver Labor Fatigue Limit**:
   $$\text{Current Shift Work Minutes} + \text{Estimated Route ETA} \le 480 \text{ min (8 Hours)}$$
   If projected shift breaches the labor limit, candidate is rejected with `DRIVER_SHIFT_EXCEEDED`.
4. **Physical Route Accessibility**:
   Routes traversing blocked edges (road closures, police cordons) are rejected with `ROUTE_UNAVAILABLE`.

---

## 4. Multi-Criteria Transparent Allocation Score

For all candidate vehicles passing the hard safety gate, the system computes a transparent, normalized cost score:

$$\text{Allocation Score} = 0.40 \cdot \overline{\text{ETA}} + 0.20 \cdot \overline{\text{Distance}} + 0.15 \cdot \overline{\text{Payload}} + 0.15 \cdot \overline{\text{Shift Usage}} + 0.10 \cdot \overline{\text{Disruption Cost}}$$

- $\overline{\text{ETA}} = \text{clamp}\left(\frac{\text{Predicted Hybrid ETA}}{120\text{ min}}\right)$
- $\overline{\text{Distance}} = \text{clamp}\left(\frac{\text{Additional Distance}}{50\text{ km}}\right)$
- $\overline{\text{Payload}} = \frac{\text{Projected Payload}}{\text{Rated Capacity}}$
- $\overline{\text{Shift Usage}} = \frac{\text{Projected Shift Minutes}}{480\text{ min}}$
- $\overline{\text{Disruption Cost}} = \text{clamp}\left(\frac{\text{Congestion Factor}}{5.0}\right)$

**Decision Rule**: The safe vehicle with the **lowest allocation score** is selected.

---

## 5. Dynamic Route Insertion & Emergency Requests

When an emergency collection request arrives:
1. Candidate vehicles with active routes are evaluated for **incremental waypoint insertion**:
   $$\text{Depot} \longrightarrow S_1 \longrightarrow \mathbf{E} \longrightarrow S_2 \dots \longrightarrow \text{Landfill}$$
2. The dynamic inserter computes:
   - Incremental travel distance $\Delta D = D_{\text{inserted}} - D_{\text{original}}$
   - Incremental travel time $\Delta \text{ETA} = \text{ETA}_{\text{inserted}} - \text{ETA}_{\text{original}}$ via Adaptive Hybrid ETA
   - Dynamic payload feasibility ($P + W \le C$)
   - Driver shift feasibility ($S_{\text{elapsed}} + \text{ETA}_{\text{new}} \le 480$)
3. If a safe insertion position exists, the lowest-cost position is selected.
4. If all insertion positions are unsafe, the system attempts assignment to an available standby vehicle.
5. If no vehicle is safe, the request is safely deferred (`EMERGENCY_REQUEST_DEFERRED`).

---

## 6. Vehicle Breakdown Handling & Fleet Rebalancing

When a vehicle suffers a mechanical breakdown (`POST /api/fleet/vehicles/{id}/breakdown`):
1. The broken vehicle is flagged `status = BREAKDOWN`.
2. Active trips and pending stops assigned to the vehicle are immediately revoked and returned to `PENDING`.
3. The broken vehicle is permanently excluded from candidate pools.
4. `FleetRebalancer` identifies affected tasks, searches alternative safe vehicles, predicts Hybrid ETAs, reallocates tasks, and logs immutable audit events into `FleetAuditEvent`.
5. Upon maintenance completion, `POST /api/fleet/vehicles/{id}/recover` restores the vehicle to `AVAILABLE`.

---

## 7. Adaptive Hybrid ETA Integration (No Data Leakage)

The allocation engine invokes Phase 5 Adaptive Hybrid ETA (`predict_hybrid_eta`):
- Features supplied: route distance, current traffic levels, weather conditions, active events, road restrictions, congestion indices, and waste tonnage.
- Strict data leakage invariance: Pre-trip allocation **never** accesses actual future travel time, simulated post-trip durations, or observed future errors.

---

## 8. Fleet Coordination APIs

- `GET /api/fleet/state` — Live summary and detailed vehicle telemetry
- `GET /api/fleet/vehicles` — Vehicle fleet telemetry and crew shifts
- `GET /api/fleet/tasks` — Registered collection tasks
- `POST /api/fleet/tasks` — Create scheduled or emergency task
- `POST /api/fleet/tasks/{task_id}/assign` — Execute task allocation engine
- `POST /api/fleet/tasks/{task_id}/emergency` — Elevate to emergency and dispatch
- `POST /api/fleet/vehicles/{vehicle_id}/breakdown` — Simulate vehicle breakdown
- `POST /api/fleet/vehicles/{vehicle_id}/recover` — Restore vehicle to available
- `POST /api/fleet/rebalance` — Trigger manual or automated fleet rebalance
- `GET /api/fleet/events` — Query immutable audit events
- `POST /api/fleet/simulate-step` — Advance fleet by discrete time step
- `POST /api/fleet/experiments/run` — Execute 35-run benchmark suite
