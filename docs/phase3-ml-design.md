# Phase 3 Research Design: Context-Aware Travel-Time Machine Learning & Scenario Intelligence

## 1. Problem Formulation & Research Objective
Urban solid waste collection operations operate under continuous dynamic environmental and physical stressors. Standard dispatch planners rely on static, distance-proportional kinematic heuristics (e.g., assuming an invariant nominal speed across municipal road networks). In real-world urban logistics, these assumptions fail due to:
- Severe meteorological events (rainfall reducing visibility and wheel-traction).
- Dynamic traffic congestion and rush-hour bottlenecks.
- Localized disruptions (public gatherings, parades, marathons).
- Infrastructure blockages (lane closures, utility repairs).
- Stochastic collection stop dwell delays proportional to bin load tonnage.

**Core Research Question:**
> *"Can contextual information such as weather, traffic, public events, road restrictions, and changing waste volumes significantly improve travel-time (ETA) prediction accuracy compared with a simple deterministic baseline?"*

---

## 2. Dataset Pipeline & Validation
The primary dataset is extracted directly from the PostgreSQL `travel_time_observations` relational database and contextual entity tables (`weather_conditions`, `traffic_conditions`, `events`, `road_restrictions`).

### Target Variable
- `actual_travel_minutes` (Continuous float > 0): Verified total route traversal and stop service duration.

### Dataset Integrity & Pre-Training Validation
Records are programmatically validated before entering the feature pipeline:
1. `distance_km > 0`
2. `actual_travel_minutes > 0` and `baseline_travel_minutes > 0`
3. `waste_volume_tons >= 0`
4. `congestion_index` bounded in `[0, 100]`
5. `hour_of_day` bounded in `[0, 23]`
6. `day_of_week` bounded in `[0, 6]`
7. Missing categorical associations are assigned explicit defaults (`NONE`, `CLEAR`, `LOW`).

> **Disclaimer:** The dataset is synthetic and serves as an academic research prototype for systematic benchmarking prior to full production GPS sensor ingestion.

---

## 3. Feature Engineering Pipeline

The tabular feature pipeline processes numerical continuous and categorical discrete variables:

### Continuous Numerical Features
- `distance_km`: Spatial route length.
- `waste_volume_tons`: Total accumulated waste tonnage.
- `rainfall_mm`: Precipitation rate.
- `visibility_km`: Atmospheric sight distance.
- `congestion_index`: Road segment saturation index (0–100%).
- `average_speed_kmh`: Observed road corridor flow velocity.
- `event_radius`: Geographic extent of nearby public gatherings.
- `hour_of_day` & `day_of_week`: Diurnal and weekly temporal factors.
- `is_peak_hour`: Engineered binary indicator (1 for morning peak 07:00–09:00, evening peak 16:00–18:00 on weekdays, and midday Saturday 11:00–14:00).

### Categorical Environmental Features
- `weather_condition`: `CLEAR`, `CLOUDY`, `LIGHT_RAIN`, `HEAVY_RAIN`, `STORM`.
- `traffic_level`: `LOW`, `MEDIUM`, `HIGH`, `SEVERE`.
- `event_level`: `NONE`, `LOW`, `MEDIUM`, `HIGH`.
- `road_restriction_type`: `NONE`, `LANE_RESTRICTION`, `CONSTRUCTION`, `PARTIAL_CLOSURE`, `ROAD_CLOSURE`.
- `road_restriction_severity`: `NONE`, `LOW`, `MEDIUM`, `HIGH`.

Categorical features are transformed using `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` within a scikit-learn `ColumnTransformer`.

---

## 4. Model Architectures & Methodological Separation

### Model 1 — Deterministic Baseline
The baseline represents standard municipal dispatch calculation:
$$\text{ETA}_{\text{baseline}} = \left( \frac{\text{distance\_km}}{\bar{v}_{\text{baseline}}} \right) \times 60$$
where nominal vehicle speed $\bar{v}_{\text{baseline}} = 25.0\text{ km/h}$.
- **Strict Constraint:** The baseline model receives *only* `distance_km` and is isolated from all contextual variables.

### Model 2 — Context-Aware Machine Learning (Random Forest Regressor)
A multi-tree ensemble regressor (`RandomForestRegressor(n_estimators=100, random_state=42)`) trained on the engineered multidimensional feature space.
- Captures nonlinear cross-feature interactions between weather severity, congestion spikes, and stop dwell times.
- Persisted to `backend/models/context_aware_eta_model.joblib` with serialized metadata in `context_aware_eta_metadata.json`.

---

## 5. Train / Test Split Strategy
To avoid temporal data leakage:
- Observations are ordered chronologically by `observation_date` and timestamp.
- The earliest 80% partition is designated as the training set ($N=48$).
- The remaining 20% partition serves as the out-of-sample test set ($N=12$).
- If dates are homogenous or sparse, a deterministic split (`random_state=42`) is utilized with explicit reporting in metadata logs.

---

## 6. Evaluation Metrics & Benchmark Results

### Metric Definitions
- **Mean Absolute Error (MAE):** $\text{MAE} = \frac{1}{N}\sum |y_i - \hat{y}_i|$
- **Root Mean Squared Error (RMSE):** $\text{RMSE} = \sqrt{\frac{1}{N}\sum (y_i - \hat{y}_i)^2}$
- **Mean Error (Bias):** $\frac{1}{N}\sum (\hat{y}_i - y_i)$
- **Median Absolute Error:** $\text{Median}(|y_i - \hat{y}_i|)$
- **Within Tolerance Rate:** Percentage of test predictions within $\pm 10.0\text{ minutes}$ of ground truth.
- **Percentage Improvement:** $\Delta_{\text{MAE}} = \frac{\text{MAE}_{\text{baseline}} - \text{MAE}_{\text{context}}}{\text{MAE}_{\text{baseline}}} \times 100$

### Measured Empirical Test Results
| Metric | Model 1 (Baseline) | Model 2 (Context-Aware RF) | Empirical Improvement |
| :--- | :--- | :--- | :--- |
| **MAE** | 36.76 min | **3.75 min** | **+89.80% reduction** |
| **RMSE** | 43.75 min | **4.74 min** | **+89.17% reduction** |
| **Mean Bias** | -36.76 min | **-1.29 min** | Minimal systemic bias |
| **Median Absolute Error**| 29.10 min | **3.32 min** | Robust non-parametric |
| **Arrivals within $\pm 10$m**| 0.00% | **91.67%** | High operational reliability |

---

## 7. Model Feature Importance
Normalized Gini feature importance extracted from the Random Forest ensemble:
1. **Rainfall rate (`rainfall_mm`):** ~31.3%
2. **Traffic Congestion (`congestion_index`):** ~28.8%
3. **Average Speed (`average_speed_kmh`):** ~12.3%
4. **Visibility (`visibility_km`):** ~8.6%
5. **Waste Volume (`waste_volume_tons`):** ~8.4%
6. **Route Distance (`distance_km`):** ~7.4%

---

## 8. Operational Scenario Engine & Safety Integration

### Predefined Stress Scenarios
1. **Normal Conditions:** Clear weather, light traffic, standard 5.5t payload.
2. **Heavy Rain:** 38mm precipitation, 3km visibility, speed reduction to 22 km/h.
3. **Major Event:** Marathon/festival, 86% congestion index, partial lane closures.
4. **Road Closure:** Arterial detour, 74% congestion, high restriction severity.
5. **High Waste Volume:** Surge collection (11.2t), extended dwell times.
6. **Combined Stress:** Extreme compound storm (55mm rain, 94% congestion, event radius, road closure, 12.5t payload).

### Safety Constraint Enforcement
Prior to simulation execution, the engine validates physical boundaries:
- **Vehicle Capacity:** Overloading a vehicle beyond rated gross tonnage triggers `UNSAFE_ASSIGNMENT` (`PAYLOAD_CAPACITY_EXCEEDED`) and halts prediction.
- **Driver Shift Limits:** Routes extending cumulative driver time past 480 minutes trigger `WORKLOAD_LIMIT_EXCEEDED`.
- **Integrity Guarantee:** Safety violations are never overridden by the simulator.

---

## 9. Research Limitations
1. **Synthetic Generation:** Data generated via stochastic domain parameters; real GPS telematics will be incorporated in subsequent phases.
2. **Spatial Topology:** Detours currently modeled via parametric delay functions rather than dynamic graph recalculation (Dijkstra/A*).
3. **Driver Behavior:** Individual driving styles and fatigue variance modeled via bounded normal noise rather than biometric telemetry.
