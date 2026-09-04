export interface HealthResponse {
  status: string;
  service: string;
  phase: number;
}

export interface OperatingConditions {
  weather: string;
  traffic: string;
  event_impact: string;
  road_restrictions: string;
  waste_volume: string;
}

export interface WasteVolumeTrend {
  day: string;
  volume_tons: number;
}

export interface ETAComparisonItem {
  route_id: string;
  baseline_eta_min: number;
  context_eta_min: number;
  actual_eta_min: number;
}

export interface ETAErrorItem {
  route_id: string;
  baseline_error_min: number;
  context_error_min: number;
}

export interface VehicleUtilizationItem {
  vehicle_id: string;
  utilization_pct: number;
  capacity_tons: number;
  current_load_tons: number;
}

export interface DashboardSummary {
  waste_volume: number;
  waste_volume_unit: string;
  active_routes: number;
  average_eta_min: number;
  eta_accuracy_pct: number;
  available_vehicles: string;
  workload_status: string;
  operating_conditions: OperatingConditions;
  waste_volume_trends: WasteVolumeTrend[];
  eta_comparisons: ETAComparisonItem[];
  eta_errors: ETAErrorItem[];
  vehicle_utilization: VehicleUtilizationItem[];
  is_demo: boolean;
  phase: number;
}

export interface RouteStop {
  stop_id: string;
  name: string;
  lat: number;
  lng: number;
  waste_volume_kg: number;
  sequence: number;
}

export interface RouteItem {
  route_id: string;
  vehicle_id: string;
  driver_name: string;
  waste_volume_tons: number;
  distance_km: number;
  baseline_eta_min: number;
  context_eta_min: number;
  status: 'On Schedule' | 'Delayed' | 'At Risk' | string;
  collection_stops_count: number;
  stops?: RouteStop[];
}

export interface RouteListResponse {
  routes: RouteItem[];
  total: number;
  is_demo: boolean;
}

export interface ScenarioOptionsResponse {
  weather_options: string[];
  traffic_options: string[];
  event_options: string[];
  road_restriction_options: string[];
  waste_volume_options: string[];
  time_of_day_options: string[];
  is_demo: boolean;
}

export interface ScenarioFormState {
  weather: string;
  traffic: string;
  event_impact: string;
  road_restrictions: string;
  waste_volume: string;
  time_of_day: string;
}

export interface ExperimentResult {
  id: string;
  experiment_name: string;
  scenario: string;
  baseline_model: string;
  context_model: string;
  baseline_mae: number;
  context_mae: number;
  baseline_rmse: number;
  context_rmse: number;
  improvement_pct: number;
  status: 'Completed (Demo)' | 'Pending ML Phase';
}

// Phase 2 Database Entities Interfaces
export interface VehicleItem {
  id: number;
  vehicle_code: string;
  vehicle_type: string;
  capacity_tons: number;
  status: string;
  active: boolean;
  created_at: string;
}

export interface DriverItem {
  id: number;
  employee_code: string;
  name: string;
  max_work_minutes_per_shift: number;
  current_work_minutes: number;
  status: string;
  active: boolean;
  created_at: string;
}

export interface WeatherItem {
  id: number;
  observation_time: string;
  condition: string;
  temperature_c: number;
  rainfall_mm: number;
  visibility_km: number;
  severity: string;
  created_at: string;
}

export interface TrafficItem {
  id: number;
  observation_time: string;
  traffic_level: string;
  congestion_index: number;
  average_speed_kmh: number;
  created_at: string;
}

export interface EventItem {
  id: number;
  event_name: string;
  event_type: string;
  start_time: string;
  end_time: string;
  latitude: number;
  longitude: number;
  impact_radius_km: number;
  impact_level: string;
  created_at: string;
}

export interface RoadRestrictionItem {
  id: number;
  restriction_type: string;
  description: string;
  start_time: string;
  end_time: string;
  latitude: number;
  longitude: number;
  affected_radius_km: number;
  severity: string;
  active: boolean;
  created_at: string;
}

export interface ObservationItem {
  id: number;
  route_id: number;
  observation_date: string;
  distance_km: number;
  baseline_travel_minutes: number;
  actual_travel_minutes: number;
  weather_id?: number;
  traffic_id?: number;
  event_id?: number;
  road_restriction_id?: number;
  waste_volume_tons: number;
  hour_of_day: number;
  day_of_week: number;
  created_at: string;
}

export interface SafetyCheckResponse {
  is_valid: boolean;
  message: string;
  violation_type?: string;
}

export interface PaginatedList<T> {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  items: T[];
  is_demo: boolean;
}

// Phase 3 Machine Learning and Scenario Types
export interface EvaluationMetrics {
  mae: number;
  rmse: number;
  mean_error: number;
  median_absolute_error: number;
  within_tolerance_pct: number;
  tolerance_minutes: number;
  sample_count: number;
}

export interface ModelMetricsComparison {
  baseline: EvaluationMetrics;
  context_aware: EvaluationMetrics;
  mae_improvement_pct: number;
  rmse_improvement_pct: number;
  is_improved: boolean;
}

export interface FeatureImportanceItem {
  feature: string;
  importance: number;
}

export interface MLStatusResponse {
  is_trained: boolean;
  model_name?: string;
  model_type?: string;
  model_version?: string;
  training_date?: string;
  training_row_count?: number;
  testing_row_count?: number;
  total_dataset_rows?: number;
  metrics?: ModelMetricsComparison;
  feature_importances?: FeatureImportanceItem[];
  split_method?: string;
  synthetic_disclaimer: string;
}

export interface MLTrainResponse {
  status: string;
  message: string;
  metadata: MLStatusResponse;
}

export interface ETAPredictRequest {
  distance_km: number;
  waste_volume_tons?: number;
  weather_condition?: string;
  rainfall_mm?: number;
  visibility_km?: number;
  traffic_level?: string;
  congestion_index?: number;
  average_speed_kmh?: number;
  event_level?: string;
  event_radius?: number;
  road_restriction_type?: string;
  road_restriction_severity?: string;
  hour_of_day?: number;
  day_of_week?: number;
  route_id?: number;
  persist?: boolean;
}

export interface ETAPredictResponse {
  distance_km: number;
  baseline_eta_minutes: number;
  context_aware_eta_minutes: number;
  difference_minutes: number;
  baseline_speed_kmh: number;
  context_applied: Record<string, any>;
}

export interface ScenarioRunRequest {
  scenario_key?: string;
  route_id?: number;
  vehicle_id?: number;
  driver_id?: number;
  distance_km?: number;
  waste_volume_tons?: number;
  weather_condition?: string;
  rainfall_mm?: number;
  visibility_km?: number;
  traffic_level?: string;
  congestion_index?: number;
  average_speed_kmh?: number;
  event_level?: string;
  event_radius?: number;
  road_restriction_type?: string;
  road_restriction_severity?: string;
  hour_of_day?: number;
  day_of_week?: number;
}

export interface ConstraintViolationInfo {
  type?: string;
  message: string;
}

export interface ScenarioRunResponse {
  scenario_name: string;
  scenario_key: string;
  status: 'COMPLETED' | 'UNSAFE_ASSIGNMENT' | string;
  is_safe: boolean;
  constraint_violation?: ConstraintViolationInfo;
  parameters: Record<string, any>;
  baseline_eta_minutes?: number;
  context_aware_eta_minutes?: number;
  simulated_actual_minutes?: number;
  baseline_error_minutes?: number;
  context_aware_error_minutes?: number;
  improvement_pct?: number;
  safety_status?: string;
  safety_message?: string;
}

export interface PresetScenario {
  key: string;
  name: string;
  description: string;
  weather_condition: string;
  rainfall_mm: number;
  visibility_km: number;
  traffic_level: string;
  congestion_index: number;
  average_speed_kmh: number;
  event_level: string;
  event_radius: number;
  road_restriction_type: string;
  road_restriction_severity: string;
  waste_volume_tons: number;
  hour_of_day: number;
  day_of_week: number;
}

// Phase 5 Adaptive Hybrid & Advanced Error Analysis Types
export interface HybridPredictRequest {
  distance_km: number;
  waste_volume_tons?: number;
  weather_condition?: string;
  rainfall_mm?: number;
  visibility_km?: number;
  traffic_level?: string;
  congestion_index?: number;
  average_speed_kmh?: number;
  event_level?: string;
  event_radius?: number;
  road_restriction_type?: string;
  road_restriction_severity?: string;
  hour_of_day?: number;
  day_of_week?: number;
  route_id?: number;
  vehicle_id?: number;
  driver_id?: number;
  persist?: boolean;
}

export interface HybridPredictResponse {
  selected_model: 'BASELINE' | 'CONTEXT_AWARE' | string;
  predicted_eta_minutes?: number;
  selection_reason: string;
  prediction_spread_minutes?: number | null;
  safety_status: string;
  is_safe: boolean;
  baseline_eta_minutes?: number;
  context_aware_eta_minutes?: number;
  constraint_violation?: ConstraintViolationInfo | null;
  policy_version?: string;
}

export interface HybridSelectionRate {
  baseline_pct: number;
  context_aware_pct: number;
}

// Phase 4 & Phase 5 Experimentation & Failure Analysis Types
export interface ScenarioExperimentSummary {
  experiment_id?: number;
  scenario_key: string;
  scenario_name: string;
  repetitions: number;
  total_runs: number;
  safe_runs: number;
  unsafe_runs: number;
  winner: 'BASELINE' | 'CONTEXT_AWARE' | 'HYBRID' | 'HYBRID (BASELINE)' | 'HYBRID (CONTEXT)' | 'TIE' | 'UNSAFE' | string;
  selection_rates?: {
    baseline_selected_pct: number;
    context_aware_selected_pct: number;
  };
  metrics: {
    baseline: EvaluationMetrics;
    context_aware: EvaluationMetrics;
    hybrid?: EvaluationMetrics;
    mae_improvement_pct: number;
    rmse_improvement_pct: number;
    context_mae_improvement_pct?: number;
    hybrid_vs_context_mae_impr_pct?: number;
  };
  safety_summary: {
    total_assignments: number;
    safe_assignments: number;
    unsafe_assignments: number;
    capacity_violations: number;
    driver_workload_violations: number;
    blocked_assignments: number;
  };
}

export interface FailureCaseItem {
  scenario_key: string;
  scenario_name: string;
  route_id: string;
  seed: number;
  baseline_eta_minutes?: number;
  context_aware_eta_minutes?: number;
  hybrid_eta_minutes?: number;
  selected_model?: string;
  selection_reason?: string;
  prediction_spread_minutes?: number | null;
  actual_travel_minutes?: number;
  baseline_error_minutes?: number;
  context_aware_error_minutes?: number;
  hybrid_error_minutes?: number;
  error_delta_minutes?: number;
  failure_reason: string;
  is_safe: boolean;
  safety_message?: string;
}

export interface WorstErrorItem {
  rank: number;
  route: string;
  scenario: string;
  seed: number;
  predicted_eta: number;
  actual_eta: number;
  absolute_error: number;
  signed_error: number;
  reason: string;
  selected_model?: string;
}

export interface TopWorstErrorsResponse {
  baseline_worst: WorstErrorItem[];
  context_aware_worst: WorstErrorItem[];
  hybrid_worst?: WorstErrorItem[];
}

export interface ExperimentBenchmarkResponse {
  total_scenarios: number;
  total_experiment_runs: number;
  safe_runs_count: number;
  unsafe_runs_count: number;
  global_winner?: string;
  global_metrics: {
    baseline: EvaluationMetrics;
    context_aware: EvaluationMetrics;
    hybrid?: EvaluationMetrics;
    mae_improvement_pct?: number;
    rmse_improvement_pct?: number;
    hybrid_vs_baseline_mae_impr_pct?: number;
    hybrid_vs_baseline_rmse_impr_pct?: number;
    hybrid_vs_context_mae_impr_pct?: number;
    context_vs_baseline_mae_impr_pct?: number;
  };
  scenario_breakdown: ScenarioExperimentSummary[];
  failure_analysis: {
    total_runs: number;
    total_failures: number;
    failure_rate_pct: number;
    category_breakdown: Record<string, number>;
    failure_cases: FailureCaseItem[];
  };
  top_worst_errors: TopWorstErrorsResponse;
  synthetic_disclaimer: string;
}

// ==========================================
// PHASE 6: DYNAMIC ROUTING & REROUTING ENGINE
// ==========================================

export interface LatLng {
  lat: number;
  lng: number;
}

export interface GraphNode {
  id: string;
  name: string;
  lat: number;
  lng: number;
  node_type: 'depot' | 'collection' | 'transfer_station' | 'landfill' | 'intersection' | string;
}

export interface GraphEdge {
  source: string;
  target: string;
  distance_km: number;
  speed_limit_kmh: number;
  base_traversal_time_min: number;
  current_traversal_time_min: number;
  is_blocked: boolean;
  congestion_factor: number;
  weather_penalty_factor: number;
  road_type: string;
}

export interface NetworkGraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  disclaimer: string;
}

export interface ActiveTripCreate {
  vehicle_id: string;
  driver_id: string;
  origin_node?: string;
  destination_node?: string;
  initial_stops?: string[];
  vehicle_capacity_kg?: number;
  initial_payload_kg?: number;
  max_shift_hours?: number;
  notes?: string;
}

export interface ActiveDisruptionItem {
  id: string;
  type: string;
  target_edge?: string[];
  target_node?: string;
  severity: number;
  additional_waste_kg: number;
  description: string;
  injected_at: string;
}

export interface ActiveTrip {
  id: string;
  vehicle_id: string;
  driver_id: string;
  origin_node: string;
  destination_node: string;
  current_node: string;
  visited_nodes: string[];
  remaining_stops: string[];
  current_path: string[];
  current_payload_kg: number;
  vehicle_capacity_kg: number;
  elapsed_time_minutes: number;
  max_shift_hours: number;
  distance_traveled_km: number;
  current_eta_minutes: number;
  baseline_eta_minutes: number;
  hybrid_eta_minutes: number;
  eta_uncertainty_minutes: number;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'PAUSED' | string;
  active_disruptions: ActiveDisruptionItem[];
  reroute_count: number;
  created_at: string;
  updated_at: string;
}

export interface RouteCandidate {
  id?: string;
  strategy: string;
  path: string[];
  path_coordinates: LatLng[];
  total_distance_km: number;
  predicted_eta_minutes: number;
  baseline_eta_minutes: number;
  hybrid_eta_minutes: number;
  eta_uncertainty_minutes: number;
  safety_valid: boolean;
  safety_violations: string[];
  optimization_score: number;
  is_selected: boolean;
  rejection_reason?: string | null;
  created_at?: string;
}

export interface ReroutingEvent {
  id: string;
  trip_id: string;
  trigger_type: string;
  trigger_details: Record<string, any>;
  previous_path: string[];
  new_path: string[];
  previous_eta_minutes: number;
  new_eta_minutes: number;
  time_saved_minutes: number;
  distance_difference_km: number;
  selected_candidate_id?: string;
  candidate_count: number;
  decision_rationale: string;
  timestamp: string;
}

export interface RerouteResponse {
  trip_id: string;
  reroute_executed: boolean;
  trigger_type: string;
  decision_rationale: string;
  selected_candidate?: RouteCandidate;
  all_candidates: RouteCandidate[];
  event?: ReroutingEvent;
  trip: ActiveTrip;
  disclaimer: string;
}

export interface DisruptionInjectRequest {
  disruption_type: 'ROAD_CLOSURE' | 'TRAFFIC_SPIKE' | 'HEAVY_RAIN' | 'EVENT_BLOCK' | 'HIGH_WASTE' | string;
  target_edge?: string[];
  target_node?: string;
  severity?: number;
  additional_waste_kg?: number;
  description?: string;
}

export interface SimulationStepResponse {
  trip: ActiveTrip;
  step_taken_from: string;
  step_taken_to: string;
  segment_distance_km: number;
  segment_time_minutes: number;
  waste_collected_kg: number;
  trip_completed: boolean;
  reroute_occurred: boolean;
  reroute_event?: ReroutingEvent | null;
  disclaimer: string;
}

export interface RoutingScenarioResult {
  scenario_name: string;
  seed: number;
  static_baseline_travel_time_min: number;
  static_baseline_distance_km: number;
  static_baseline_success: boolean;
  dynamic_rerouted_travel_time_min: number;
  dynamic_rerouted_distance_km: number;
  dynamic_rerouted_success: boolean;
  time_saved_minutes: number;
  pct_time_saved: number;
  distance_penalty_km: number;
  reroute_count: number;
  safety_violations_prevented: number;
  decision_rationale: string;
}

export interface RoutingExperimentSummary {
  total_runs: number;
  scenarios_evaluated: string[];
  mean_time_saved_min: number;
  mean_pct_time_saved: number;
  overall_safety_rate_static_pct: number;
  overall_safety_rate_dynamic_pct: number;
  disruption_adaptation_effectiveness_pct: number;
  scenario_breakdown: Record<string, {
    mean_static_time_min: number;
    mean_dynamic_time_min: number;
    mean_time_saved_min: number;
    mean_pct_time_saved: number;
    mean_distance_penalty_km: number;
    static_safety_rate_pct: number;
    dynamic_safety_rate_pct: number;
    total_violations_prevented: number;
  }>;
  detailed_runs?: RoutingScenarioResult[];
  disclaimer: string;
}

