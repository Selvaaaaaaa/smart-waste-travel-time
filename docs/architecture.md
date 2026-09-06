# Smart Waste Collection Simulator — Architecture & Design Document (Phase 10)

## 1. System Overview

The **Smart Waste Collection Travel-Time & Route Simulator** is an enterprise-grade operational research and logistics platform designed for municipal public works departments. It solves the multi-vehicle dynamic waste collection problem under stochastic traffic congestion, adverse weather, road closures, container overflow spikes, and unexpected mechanical breakdowns.

```
                      +---------------------------------------+
                      |         Municipal Web GUI             |
                      |   React 18 + TS + Vite + Leaflet      |
                      +-------------------+-------------------+
                                          |
                                   REST / WebSocket
                                          |
                                          v
                      +---------------------------------------+
                      |         FastAPI Gateway Core          |
                      |   Pydantic V2 + JWT Authentication    |
                      +-------------------+-------------------+
                                          |
     +-----------------+------------------+------------------+-----------------+
     |                 |                  |                  |                 |
     v                 v                  v                  v                 v
+---------+     +--------------+   +---------------+   +------------+   +---------------+
|   IoT   |     | Sensor Fusion|   |Adaptive Hybrid|   |  Dynamic   |   | Multi-Vehicle |
|Telemetry|     |  & Outliers  |   |  ETA Engine   |   |  Routing   |   | Coordination  |
| Ingest  |     |  Estimation  |   | (RF + Base)   |   | (Dijkstra) |   | (Pareto Alloc)|
+----+----+     +------+-------+   +-------+-------+   +-----+------+   +-------+-------+
     |                 |                   |                 |                  |
     +-----------------+-------------------+-----------------+------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |       Strict Safety Guardrail Layer   |
                      |  (Payload, Shift, Weather, Closure)   |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |    Relational Persistence Layer       |
                      |    PostgreSQL 15 / SQLite (Dev)       |
                      +---------------------------------------+
```

---

## 2. Core Architectural Subsystems

### 2.1 IoT Telemetry & Ingestion Subsystem (Phase 9)
- **High-Frequency Ingestion:** Endpoints accept vehicle GPS packets (5 Hz) and smart container sensor readings (15 s intervals).
- **Validation Pipeline:** Schema enforcement via Pydantic; deduplication against message hash cache; drop counter tracking.
- **WebSocket Streaming:** `ConnectionManager` distributes live vehicle movements, container fill updates, and critical system alerts to connected command center consoles.

### 2.2 Sensor Fusion & Operational State Estimation (Phase 9)
- **Trajectory Deviation Detector:** Calculates perpendicular distance from vehicle coordinates to planned polyline vertices; triggers warning if deviation exceeds 100m.
- **Critical Spillover Aggregator:** Flags bins exceeding 90% capacity; clusters localized hot-spots; initiates automated emergency collection tickets.
- **Fused Operational Model:** Unifies weather data, traffic congestion index, vehicle statuses, and container fill levels into an immutable timestamped state snapshot.

### 2.3 Adaptive Hybrid Travel-Time Forecasting (Phases 3–5)
- **Deterministic Baseline:** Evaluates kinematic distance divided by 25 km/h urban collection speed.
- **Context-Aware Machine Learning:** 100-tree Random Forest Regressor trained on 15 features:
  - Numerical: `distance_km`, `waste_volume_tons`, `rainfall_mm`, `visibility_km`, `congestion_index`, `average_speed_kmh`, `event_radius`, `hour_of_day`, `day_of_week`, `is_peak_hour`.
  - Categorical: `weather_condition`, `traffic_level`, `event_level`, `road_restriction_type`, `road_restriction_severity`.
- **Pre-Trip Policy Arbiter:** Evaluates environmental stress metrics. If nominal, selects deterministic baseline (eliminates model variance); if disrupted (rain $> 25$ mm, traffic high, major event, road closure), routes to Context-Aware ML with empirical spread calculation.

### 2.4 Dynamic Routing & Detour Engine (Phase 6)
- **Graph Model:** Directed weighted graph constructed via NetworkX (`14 vertices, 24 arcs`).
- **Pareto Candidate Evaluation:** Computes top route candidates considering total distance, expected transit duration, and high-traffic corridor exposure.
- **Real-Time Detour Generation:** In response to road blockage alerts, edges are weighted to infinity, and Dijkstra shortest-path detours are calculated in under 2 ms.

### 2.5 Multi-Vehicle Fleet Coordination & Rebalancing (Phases 7–8)
- **Centralized State Management:** `FleetStateManager` tracks vehicle assignments, payloads, drivers, and shifts.
- **Multi-Objective Task Allocation:** Computes allocation scores balancing travel distance, remaining shift equity, and payload match.
- **Dynamic Task Insertion:** Evaluates marginal detour cost across active vehicle routes to insert emergency collection stops without rebuilding the entire schedule.
- **Automated Breakdown Rebalance:** Stranded tasks from failed vehicles are immediately redistributed to active units with available capacity.

### 2.6 Strict Safety Validation Guardrail Layer (Phases 2, 8, 10)
- Hard constraint layer wrapping all operations.
- Intercepts and rejects dispatches that would cause vehicle gross overload (`CAPACITY_EXCEEDED`) or driver shift overage (`SHIFT_EXCEEDED`).
- Enforces severe weather speed buffers and suppresses duplicate alerts via cooldown timers.

---

## 3. Database Entity Relationship Model

The operational database defines 14 core tables with foreign key cascades:
- `vehicles` (capacity, status, type, active)
- `drivers` (employee code, shift minutes, active)
- `routes` (origin, destination, distance, waste, duration, status)
- `route_stops` (sequence, latitude, longitude, service minutes, completed)
- `waste_collections` (waste type, weight, timestamp)
- `weather_conditions` (rainfall, visibility, temperature, condition)
- `traffic_conditions` (congestion index, average speed, level)
- `events` (impact level, radius, coordinates)
- `road_restrictions` (type, severity, active)
- `travel_time_observations` (historical training records)
- `eta_predictions` (prediction logs, baseline vs ML, absolute error)
- `collection_tasks` (task status, priority, assigned vehicle)
- `fleet_audit_events` (immutable audit trail)

---

## 4. Security & Role-Based Access Control (RBAC)

Three operational roles are defined with hierarchical permissions:
1. **DISPATCHER:** Full access to route planning, task assignment, emergency insertion, and fleet rebalancing.
2. **DRIVER:** Read-only access to assigned vehicle itinerary, route stops, and GPS reporting.
3. **MUNICIPAL_SUPERVISOR:** Access to system-wide KPI analytics, audit logs, scalability benchmarks, and model configuration.
