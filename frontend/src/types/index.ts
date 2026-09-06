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

// ==========================================
// Phase 7 Multi-Vehicle Fleet Coordination
// ==========================================

export interface VehicleFleetItem {
  vehicle_id: string;
  vehicle_code: string;
  vehicle_type: string;
  capacity_kg: number;
  current_payload_kg: number;
  current_location: string;
  driver_id?: string | null;
  driver_name?: string | null;
  driver_shift_remaining_min: number;
  current_route: string[];
  current_task_id?: string | null;
  status: 'AVAILABLE' | 'ASSIGNED' | 'EN_ROUTE' | 'AT_STOP' | 'LOADING' | 'RETURNING' | 'OVERLOADED' | 'BREAKDOWN' | 'OFF_DUTY' | string;
  overload_status: 'NORMAL' | 'WARNING' | 'CRITICAL' | 'OVERLOADED' | string;
  utilization_pct: number;
  safety_status: string;
  estimated_available_time_min: number;
  assigned_tasks_count?: number;
  completed_tasks_count?: number;
  pending_tasks_count?: number;
  estimated_workload_minutes?: number;
  route_distance_km?: number;
  workload_deviation_minutes?: number;
}


export interface FleetSummary {
  total_vehicles: number;
  available: number;
  assigned: number;
  en_route: number;
  overloaded: number;
  breakdown: number;
  off_duty: number;
  mean_utilization_pct: number;
  utilization_variance: number;
  load_balance_score: number;
}

export interface FleetStateResponse {
  summary: FleetSummary;
  vehicles: VehicleFleetItem[];
  active_tasks_count: number;
  pending_tasks_count: number;
  timestamp: string;
  disclaimer: string;
}

export interface CollectionTask {
  id: string;
  location_node: string;
  estimated_waste_kg: number;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT' | string;
  request_type: 'SCHEDULED_COLLECTION' | 'EMERGENCY_REQUEST' | string;
  status: 'PENDING' | 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'DEFERRED' | string;
  assigned_vehicle_id?: string | null;
  assigned_driver_id?: string | null;
  deadline_minutes?: number | null;
  predicted_eta_minutes?: number | null;
  notes?: string | null;
  created_at: string;
  assigned_at?: string | null;
  completed_at?: string | null;
}

export interface CollectionTaskCreate {
  location_node: string;
  estimated_waste_kg: number;
  priority?: string;
  request_type?: string;
  deadline_minutes?: number;
  notes?: string;
}

export interface CandidateVehicleEvaluation {
  vehicle_id: string;
  vehicle_code: string;
  is_safe: boolean;
  rejection_reason?: string | null;
  allocation_score?: number | null;
  predicted_eta_min?: number | null;
  additional_distance_km?: number | null;
  projected_payload_kg: number;
  projected_shift_minutes: number;
  selected_eta_model: string;
  prediction_spread_min: number;
}

export interface TaskAssignResponse {
  task_id: string;
  status: string;
  selected_vehicle_id?: string | null;
  selected_driver_id?: string | null;
  selected_route: string[];
  predicted_eta_minutes?: number | null;
  allocation_score?: number | null;
  selection_reason: string;
  candidate_evaluations: CandidateVehicleEvaluation[];
  safety_result: string;
  disclaimer: string;
}

export interface FleetAuditEvent {
  id: string;
  event_type: string;
  task_id?: string | null;
  previous_vehicle_id?: string | null;
  new_vehicle_id?: string | null;
  previous_route: string[];
  new_route: string[];
  predicted_eta_before?: number | null;
  predicted_eta_after?: number | null;
  distance_difference_km: number;
  safety_result: string;
  selected_eta_model: string;
  reason: string;
  timestamp: string;
}

export interface FleetRebalanceResponse {
  rebalance_triggered: boolean;
  trigger_reason: string;
  affected_tasks_count: number;
  reassigned_tasks_count: number;
  deferred_tasks_count: number;
  details: Array<{
    task_id: string;
    status: string;
    previous_vehicle_id?: string | null;
    new_vehicle_id?: string | null;
    eta_minutes?: number | null;
    notes?: string;
  }>;
  audit_events: FleetAuditEvent[];
  disclaimer: string;
}

export interface VehicleBreakdownResponse {
  vehicle_id: string;
  previous_status: string;
  new_status: string;
  affected_tasks: string[];
  rebalance_result?: FleetRebalanceResponse | null;
  message: string;
}

export interface FleetSimulationStepResponse {
  step_duration_minutes: number;
  events_detected: string[];
  vehicles_updated: number;
  tasks_completed: string[];
  rebalance_performed: boolean;
  rebalance_details?: FleetRebalanceResponse | null;
  fleet_summary: FleetSummary;
  disclaimer: string;
}

export interface FleetBenchmarkRunResult {
  scenario_name: string;
  seed: number;
  tasks_assigned: number;
  tasks_total: number;
  assignment_success_rate: number;
  safe_assignment_rate: number;
  avg_assignment_eta_min: number;
  total_fleet_travel_time_min: number;
  total_fleet_distance_km: number;
  emergency_fulfilled: number;
  emergency_total: number;
  breakdown_recovered: number;
  breakdown_total: number;
  mean_vehicle_utilization_pct: number;
  utilization_variance: number;
  load_balance_score: number;
  unsafe_assignments_prevented: number;
  reassignments_count: number;
  avg_rebalancing_improvement_min: number;
  unassigned_task_count: number;
  primary_failure_mode?: string | null;
}

export interface FleetExperimentSummaryResponse {
  total_runs: number;
  scenarios_evaluated: string[];
  task_assignment_success_rate_pct: number;
  safe_assignment_rate_pct: number;
  avg_assignment_eta_min: number;
  avg_fleet_travel_time_min: number;
  avg_fleet_distance_km: number;
  emergency_fulfillment_rate_pct: number;
  breakdown_recovery_rate_pct: number;
  avg_vehicle_utilization_pct: number;
  utilization_variance: number;
  fleet_load_balance_score: number;
  unsafe_assignments_prevented: number;
  reassignments_count: number;
  avg_rebalancing_improvement_min: number;
  unassigned_task_rate_pct: number;
  scenario_breakdown: Record<string, {
    success_rate_pct: number;
    safe_rate_pct: number;
    avg_eta_min: number;
    mean_utilization_pct: number;
    load_balance_score: number;
    unsafe_prevented: number;
    reassignments: number;
  }>;
  failure_analysis: Record<string, number>;
  detailed_runs: FleetBenchmarkRunResult[];
  disclaimer: string;
}

// ============================================================================
// PHASE 8 TYPES — ADVANCED FLEET OPTIMIZATION & REALISTIC VALIDATION
// ============================================================================

export interface FleetOptimizationSummary {
  total_vehicles: number;
  active_vehicles: number;
  available_vehicles: number;
  assigned_vehicles: number;
  overloaded_vehicles: number;
  breakdown_vehicles: number;
  workload_balance_score: number;
  fleet_mean_workload_min: number;
  fleet_workload_std_min: number;
  mean_utilization_pct: number;
  emergency_requests_count: number;
  unsafe_assignments_prevented: number;
  disclaimer: string;
}

export interface MetricComparisonItem {
  baseline_value: number;
  optimized_value: number;
  absolute_difference: number;
  percentage_improvement: number;
  unit: string;
}

export interface AllocationComparison {
  strategy_evaluated: string;
  task_count: number;
  eta_comparison: MetricComparisonItem;
  distance_comparison: MetricComparisonItem;
  utilization_comparison: MetricComparisonItem;
  workload_balance_comparison: MetricComparisonItem;
  safety_violations_prevented_comparison: MetricComparisonItem;
  reassignment_count_comparison: MetricComparisonItem;
  summary_verdict: string;
  disclaimer: string;
}

export interface FailureDiagnostic {
  scenario: string;
  seed: number;
  task_id?: string | null;
  vehicle_id?: string | null;
  failure_category: string;
  failure_reason: string;
  recovery_action: string;
  final_status: string;
}

export interface Phase8BenchmarkRun {
  scenario_name: string;
  seed: number;
  tasks_assigned: number;
  tasks_total: number;
  assignment_success_rate: number;
  safe_assignment_rate: number;
  unassigned_task_rate: number;
  emergency_fulfillment_rate: number;
  vehicle_utilization_mean_pct: number;
  workload_balance_metric: number;
  avg_tasks_per_vehicle: number;
  reassignment_count: number;
  avg_eta_min: number;
  total_travel_time_min: number;
  avg_distance_km: number;
  additional_distance_km: number;
  rerouting_success_rate: number;
  unsafe_candidates_rejected: number;
  unsafe_assignments_prevented: number;
  payload_violations_prevented: number;
  shift_violations_prevented: number;
  blocked_road_violations_prevented: number;
  breakdown_recovery_rate: number;
  avg_recovery_time_min: number;
  affected_task_count: number;
  baseline_allocation_score: number;
  optimized_allocation_score: number;
  optimization_improvement_pct: number;
  execution_time_ms: number;
  primary_failure_category?: string | null;
}

export interface ScenarioStat {
  scenario_name: string;
  num_runs: number;
  eta_mean: number;
  eta_median: number;
  eta_min: number;
  eta_max: number;
  eta_std: number;
  distance_mean: number;
  distance_median: number;
  distance_min: number;
  distance_max: number;
  distance_std: number;
  score_mean: number;
  score_median: number;
  score_min: number;
  score_max: number;
  score_std: number;
  workload_balance_mean: number;
  workload_balance_median: number;
  workload_balance_min: number;
  workload_balance_max: number;
  workload_balance_std: number;
  recovery_time_mean: number;
  recovery_time_std: number;
  pct_improvement_over_baseline: number;
}

export interface Phase8ExperimentSummary {
  total_runs: number;
  scenarios_evaluated: string[];
  seeds_evaluated: number[];
  overall_assignment_success_rate_pct: number;
  overall_safe_assignment_rate_pct: number;
  overall_emergency_fulfillment_rate_pct: number;
  overall_breakdown_recovery_rate_pct: number;
  overall_mean_workload_balance: number;
  overall_mean_utilization_pct: number;
  total_unsafe_candidates_rejected: number;
  total_unsafe_assignments_prevented: number;
  total_payload_violations_prevented: number;
  total_shift_violations_prevented: number;
  total_blocked_road_violations_prevented: number;
  mean_baseline_score: number;
  mean_optimized_score: number;
  overall_optimization_improvement_pct: number;
  scenario_statistics: Record<string, ScenarioStat>;
  failure_distribution: Record<string, number>;
  failure_diagnostic_log: FailureDiagnostic[];
  detailed_runs: Phase8BenchmarkRun[];
  benchmark_execution_time_seconds: number;
  disclaimer: string;
}

// ---------------------------------------------------------
// Phase 9: Real-Time IoT Telemetry & Sensor Fusion Types
// ---------------------------------------------------------

export interface VehicleGPSTelemetry {
  vehicle_id: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  speed_kmh: number;
  heading: number;
  current_route_id?: string | null;
  current_task_id?: string | null;
  engine_status: string;
  telemetry_sequence: number;
  health_status: string;
  source: string;
}

export interface BinSensorTelemetry {
  bin_id: string;
  location_node: string;
  timestamp: string;
  fill_level_percent: number;
  estimated_waste_kg: number;
  temperature_c: number;
  sensor_battery_percent: number;
  sensor_status: string;
  status_classification: 'NORMAL' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  sequence_number: number;
  health_status: string;
  source: string;
}

export interface TelemetryAlert {
  alert_id: string;
  alert_type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | string;
  entity_id: string;
  message: string;
  timestamp: string;
  recovery_action?: string | null;
  resolved: boolean;
}

export interface RealtimeVehicleState {
  vehicle_id: string;
  vehicle_code: string;
  status: string;
  latitude: number;
  longitude: number;
  speed_kmh: number;
  heading: number;
  current_payload_kg: number;
  capacity_kg: number;
  utilization_pct: number;
  current_task_id?: string | null;
  current_route: string[];
  route_status: 'ON_TRACK' | 'DEVIATED' | 'REROUTED' | string;
  deviation_distance_m: number;
  estimated_eta_min: number;
  telemetry_health: string;
  last_telemetry_timestamp: string;
  depot_id: string;
  safety_status: string;
}

export interface RealtimeOperationalState {
  timestamp: string;
  vehicles: RealtimeVehicleState[];
  bins: BinSensorTelemetry[];
  critical_bins_count: number;
  active_alerts: TelemetryAlert[];
  traffic_condition: string;
  weather_condition: string;
  fleet_workload_balance: number;
  average_eta_minutes: number;
  disclaimer: string;
}

export interface TelemetryHealthSummary {
  total_messages_received: number;
  valid_messages_count: number;
  invalid_messages_count: number;
  duplicate_messages_count: number;
  stale_vehicles_count: number;
  telemetry_health_rate_pct: number;
  vehicle_health: Record<string, string>;
  bin_health: Record<string, string>;
  active_alerts_count: number;
  websocket_clients_connected: number;
  disclaimer: string;
}

export interface DepotInfo {
  depot_id: string;
  name: string;
  latitude: number;
  longitude: number;
  node_id: string;
  active: boolean;
  assigned_vehicles_count: number;
  capacity_vehicles: number;
}

export interface AuthUser {
  username: string;
  email: string;
  role: 'DISPATCHER' | 'DRIVER' | 'MUNICIPAL_SUPERVISOR' | string;
  assigned_vehicle_id?: string | null;
  permissions: string[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  user: AuthUser;
}

export interface AuditEvent {
  event_id: string;
  timestamp: string;
  actor: string;
  role: string;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  reason?: string | null;
  result: string;
  details: Record<string, any>;
}

export interface ScalabilityBenchmarkItem {
  vehicle_count: number;
  depot_count: number;
  telemetry_messages_processed: number;
  average_processing_latency_ms: number;
  peak_processing_latency_ms: number;
  telemetry_throughput_msg_per_sec: number;
  optimization_execution_time_ms: number;
  memory_rss_mb: number;
  status: string;
}

export interface ScalabilityBenchmarkResult {
  timestamp: string;
  benchmarks: ScalabilityBenchmarkItem[];
  scalability_verdict: string;
  disclaimer: string;
}

export interface Phase9ScenarioStat {
  scenario: string;
  runs_count: number;
  telemetry_health_rate_pct: number;
  route_deviations_detected: number;
  critical_bins_detected: number;
  emergency_requests_generated: number;
  average_eta_recalculation_ms: number;
  mean_eta_minutes: number;
  rerouting_success_rate_pct: number;
  failure_counts: Record<string, number>;
}

export interface Phase9BenchmarkSummary {
  total_runs: number;
  scenarios_evaluated: string[];
  seeds_evaluated: number[];
  overall_telemetry_health_rate_pct: number;
  total_telemetry_messages_generated: number;
  total_route_deviations_detected: number;
  total_critical_bins_detected: number;
  total_emergency_requests_generated: number;
  emergency_fulfillment_rate_pct: number;
  average_eta_recalculation_time_ms: number;
  scenario_stats: Record<string, Phase9ScenarioStat>;
  failure_counts_by_category: Record<string, number>;
  disclaimer: string;
}

// ============================================================================
// PHASE 10: INTEGRATED COMMAND CENTER & FINAL SYSTEM VALIDATION TYPES
// ============================================================================

export interface SimulationStepLog {
  step: number;
  timestamp: string;
  action: string;
  subsystem: string;
  status: string;
  details: Record<string, any>;
}

export interface SimulationDemoState {
  status: 'IDLE' | 'RUNNING' | 'COMPLETED' | 'ERROR';
  current_step: number;
  total_steps: number;
  elapsed_seconds: number;
  active_scenario: string;
  safe_allocation_rate: number;
  safety_violations: number;
  deviations_detected: number;
  breakdown_handled: boolean;
  emergency_inserted: boolean;
  steps_log: SimulationStepLog[];
  final_summary?: Record<string, any>;
}

export interface ExtendedHealthResponse extends HealthResponse {
  database?: { status: string; latency_ms: number };
  telemetry?: { status: string; health_rate_pct: number };
  websocket?: { status: string; connected_clients: number };
  simulation?: { status: string; last_run_timestamp?: string };
  timestamp?: string;
}

export interface FinalBenchmarkScenarioStat {
  runs_count: number;
  baseline_mean_eta_min: number;
  integrated_mean_eta_min: number;
  baseline_mean_dist_km: number;
  integrated_mean_dist_km: number;
  baseline_workload_balance: number;
  integrated_workload_balance: number;
  baseline_eta_mae_min: number;
  integrated_eta_mae_min: number;
  emergency_fulfillment_rate_pct: number;
  safe_assignment_rate_pct: number;
}

export interface FinalBenchmarkComparison {
  total_runs: number;
  scenarios_count: number;
  seeds_evaluated: number[];
  eta_accuracy: {
    baseline_mae_min: number;
    integrated_mae_min: number;
    mae_improvement_pct: number;
    baseline_rmse_min: number;
    integrated_rmse_min: number;
    rmse_improvement_pct: number;
    accuracy_within_10min_baseline_pct: number;
    accuracy_within_10min_integrated_pct: number;
    accuracy_within_15min_baseline_pct: number;
    accuracy_within_15min_integrated_pct: number;
  };
  fleet_performance: {
    baseline_workload_balance: number;
    integrated_workload_balance: number;
    workload_balance_improvement_pct: number;
    safe_assignment_rate_pct: number;
    unsafe_assignments_prevented: number;
    emergency_fulfillment_rate_baseline_pct: number;
    emergency_fulfillment_rate_integrated_pct: number;
  };
  system_latency: {
    average_integrated_decision_ms: number;
    average_baseline_decision_ms: number;
  };
  scenario_summaries: Record<string, FinalBenchmarkScenarioStat>;
}



