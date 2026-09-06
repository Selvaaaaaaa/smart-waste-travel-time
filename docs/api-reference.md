# Smart Waste Collection Simulator — API Reference Manual (Phase 10)

This document provides a comprehensive REST and WebSocket API specification for the **Smart Waste Collection Travel-Time & Route Simulator**.

**Base URL:** `http://localhost:8000/api/v1`  
**Authentication:** Bearer JWT Token (`Authorization: Bearer <token>`) for protected routes; public demo endpoints allow transparent evaluation.

---

## 1. System Health & Simulation Engine

### `GET /health`
- **Summary:** Multi-tier system health check.
- **Response:**
  ```json
  {
    "status": "HEALTHY",
    "service": "Smart Waste Travel Time Simulator",
    "phase": 2,
    "database": { "status": "CONNECTED", "latency_ms": 0.45 },
    "telemetry": { "status": "ACTIVE", "health_rate_pct": 100.0 },
    "websocket": { "status": "CONNECTED", "connected_clients": 1 },
    "simulation": { "status": "READY" },
    "timestamp": "2026-09-06T17:00:00Z"
  }
  ```

### `POST /simulation/full-system-demo`
- **Summary:** Executes the 21-step deterministic end-to-end simulation across all subsystems (Seed 42).
- **Body:** Optional `{ "seed": 42 }`.
- **Response:**
  ```json
  {
    "status": "PASS",
    "metrics": {
      "simulation_id": "FULL_SYSTEM_DEMO_SEED_42",
      "execution_time_seconds": 1.67,
      "steps_completed": 21,
      "safe_allocation_rate_pct": 100.0,
      "fleet_workload_balance": 0.8875,
      "overall_status": "PASS"
    },
    "step_logs": [ ... ]
  }
  ```

### `GET /simulation/demo-state`
- **Summary:** Retrieves latest step logs and execution state for the Command Center timeline.

### `GET /simulation/benchmarks`
- **Summary:** Retrieves the 50-run controlled benchmark comparison matrix (Baseline vs. Integrated).

---

## 2. Real-Time IoT Telemetry & Sensor Fusion (Phase 9)

### `GET /telemetry/fused-state`
- **Summary:** Returns aggregated real-time operational snapshot (fused positions, smart bins, weather, traffic).

### `GET /telemetry/health`
- **Summary:** Telemetry ingestion health summary (message counts, valid rates, drop counts).

### `POST /telemetry/ingest/gps`
- **Summary:** Ingests raw GPS packet from a municipal vehicle.
- **Payload:**
  ```json
  {
    "vehicle_id": "V-01",
    "timestamp": "2026-09-06T17:00:00Z",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "speed_kmh": 32.5,
    "heading": 90.0,
    "battery_pct": 95.0
  }
  ```

### `POST /telemetry/ingest/bin`
- **Summary:** Ingests raw ultrasonic fill-level reading from a smart container.
- **Payload:**
  ```json
  {
    "bin_id": "BIN-ZONE-C-02",
    "timestamp": "2026-09-06T17:00:00Z",
    "fill_level_pct": 94.2,
    "tilt_angle_deg": 1.2,
    "battery_pct": 88.0
  }
  ```

### `WS /telemetry/ws/live`
- **Summary:** High-frequency bi-directional WebSocket streaming live vehicle coordinates, bin status changes, and critical alerts.

---

## 3. Dynamic Routing & Rerouting (Phase 6)

### `POST /routing/candidates`
- **Summary:** Generates Pareto-optimal route candidates between origin and destination.
- **Parameters:** `origin_node`, `destination_node`, `via_stops`, `weather`, `traffic`.

### `POST /routing/reroute`
- **Summary:** Evaluates dynamic reroute around active road blocks or congestion spikes.
- **Payload:**
  ```json
  {
    "current_node": "DEPOT_CENTRAL",
    "remaining_stops": ["COLLECTION_ZONE_A", "COLLECTION_ZONE_B"],
    "destination_node": "LANDFILL_MAIN",
    "current_path": ["DEPOT_CENTRAL", "COLLECTION_ZONE_A", "COLLECTION_ZONE_B", "LANDFILL_MAIN"],
    "trigger_type": "ROAD_CLOSURE"
  }
  ```

### `GET /routing/network-graph`
- **Summary:** Returns full node and edge topology of the municipal network.

---

## 4. Multi-Vehicle Fleet Coordination (Phases 7–8)

### `GET /fleet/state`
- **Summary:** Real-time state of all vehicles, drivers, active tasks, and workload balance score.

### `POST /fleet/allocate`
- **Summary:** Multi-objective task allocation finding optimal vehicle under capacity and shift constraints.

### `POST /fleet/insert-task`
- **Summary:** Evaluates dynamic insertion of an emergency collection stop into active vehicle itineraries.

### `POST /fleet/rebalance`
- **Summary:** Rebalances tasks across healthy fleet units following vehicle breakdown or traffic blockage.

### `POST /fleet/step`
- **Summary:** Advances discrete simulation time step (5–10 min) updating vehicle positions and task completion.

---

## 5. Travel-Time Forecasting & ML Models (Phases 3–5)

### `POST /eta/predict`
- **Summary:** Predicts travel time using Adaptive Hybrid ETA selection.
- **Payload:**
  ```json
  {
    "distance_km": 18.7,
    "weather_condition": "HEAVY_RAIN",
    "rainfall_mm": 35.0,
    "visibility_km": 4.0,
    "traffic_level": "HIGH",
    "congestion_index": 72.0,
    "average_speed_kmh": 18.0,
    "waste_volume_tons": 6.0
  }
  ```
- **Response:**
  ```json
  {
    "selected_model": "CONTEXT_AWARE",
    "predicted_eta_minutes": 82.4,
    "selection_reason": "SEVERE_WEATHER_DISRUPTION",
    "prediction_spread_minutes": 4.2,
    "baseline_eta_minutes": 44.88
  }
  ```

---

## 6. Authentication & RBAC (Phase 9)

### `POST /auth/login`
- **Payload:** `{ "username": "dispatcher", "password": "password123" }`
- **Response:** `{ "access_token": "...", "token_type": "bearer", "user": { "role": "DISPATCHER" } }`

### `GET /auth/me`
- **Summary:** Returns identity and permissions of authenticated user.

### `GET /auth/demo-users`
- **Summary:** Returns available demo credentials for testing (`DISPATCHER`, `DRIVER`, `MUNICIPAL_SUPERVISOR`).
