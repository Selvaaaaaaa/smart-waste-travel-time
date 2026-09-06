import {
  HealthResponse,
  DashboardSummary,
  RouteListResponse,
  ScenarioOptionsResponse,
  VehicleItem,
  DriverItem,
  WeatherItem,
  TrafficItem,
  EventItem,
  RoadRestrictionItem,
  ObservationItem,
  PaginatedList,
  SafetyCheckResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL.replace(/\/+$/, '');
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        ...options,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
      }

      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error(
          `Unable to connect to backend server at ${this.baseUrl}. Please ensure the FastAPI service is running.`
        );
      }
      throw error;
    }
  }

  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  async getDashboardSummary(): Promise<DashboardSummary> {
    return this.request<DashboardSummary>('/dashboard/summary');
  }

  async getRoutes(params?: {
    status?: string;
    vehicle_id?: string;
    search?: string;
  }): Promise<RouteListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.status && params.status !== 'all') {
      searchParams.append('status', params.status);
    }
    if (params?.vehicle_id && params.vehicle_id !== 'all') {
      searchParams.append('vehicle_id', params.vehicle_id);
    }
    if (params?.search) {
      searchParams.append('search', params.search);
    }

    const qs = searchParams.toString();
    const endpoint = `/routes${qs ? `?${qs}` : ''}`;
    return this.request<RouteListResponse>(endpoint);
  }

  async getScenarioOptions(): Promise<ScenarioOptionsResponse> {
    return this.request<ScenarioOptionsResponse>('/scenarios/options');
  }

  // Phase 2 Endpoints
  async getVehicles(page = 1, pageSize = 20, status?: string): Promise<PaginatedList<VehicleItem>> {
    const qs = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (status && status !== 'all') qs.append('status', status);
    return this.request<PaginatedList<VehicleItem>>(`/vehicles?${qs}`);
  }

  async getDrivers(page = 1, pageSize = 20, status?: string): Promise<PaginatedList<DriverItem>> {
    const qs = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (status && status !== 'all') qs.append('status', status);
    return this.request<PaginatedList<DriverItem>>(`/drivers?${qs}`);
  }

  async getWeather(page = 1, pageSize = 20): Promise<PaginatedList<WeatherItem>> {
    return this.request<PaginatedList<WeatherItem>>(`/weather?page=${page}&page_size=${pageSize}`);
  }

  async getTraffic(page = 1, pageSize = 20): Promise<PaginatedList<TrafficItem>> {
    return this.request<PaginatedList<TrafficItem>>(`/traffic?page=${page}&page_size=${pageSize}`);
  }

  async getEvents(page = 1, pageSize = 20): Promise<PaginatedList<EventItem>> {
    return this.request<PaginatedList<EventItem>>(`/events?page=${page}&page_size=${pageSize}`);
  }

  async getRoadRestrictions(page = 1, pageSize = 20): Promise<PaginatedList<RoadRestrictionItem>> {
    return this.request<PaginatedList<RoadRestrictionItem>>(`/road-restrictions?page=${page}&page_size=${pageSize}`);
  }

  async getObservations(page = 1, pageSize = 20): Promise<PaginatedList<ObservationItem>> {
    return this.request<PaginatedList<ObservationItem>>(`/observations?page=${page}&page_size=${pageSize}`);
  }

  // Safety Validation API calls
  async validateVehicleCapacity(vehicleId: number, wasteTons: number): Promise<SafetyCheckResponse> {
    return this.request<SafetyCheckResponse>('/safety/validate-capacity', {
      method: 'POST',
      body: JSON.stringify({ vehicle_id: vehicleId, assigned_waste_tons: wasteTons }),
    });
  }

  async validateDriverWorkload(driverId: number, additionalMinutes: number): Promise<SafetyCheckResponse> {
    return this.request<SafetyCheckResponse>('/safety/validate-workload', {
      method: 'POST',
      body: JSON.stringify({ driver_id: driverId, additional_minutes: additionalMinutes }),
    });
  }

  async validateRouteAssignment(vehicleId: number, driverId: number, routeId?: number): Promise<SafetyCheckResponse> {
    return this.request<SafetyCheckResponse>('/safety/validate-assignment', {
      method: 'POST',
      body: JSON.stringify({ vehicle_id: vehicleId, driver_id: driverId, route_id: routeId }),
    });
  }

  // Phase 3 Machine Learning and Scenario APIs
  async getMLStatus(): Promise<import('../types').MLStatusResponse> {
    return this.request<import('../types').MLStatusResponse>('/ml/status');
  }

  async trainMLModel(modelType = 'random_forest', nEstimators = 100): Promise<import('../types').MLTrainResponse> {
    return this.request<import('../types').MLTrainResponse>('/ml/train', {
      method: 'POST',
      body: JSON.stringify({ model_type: modelType, n_estimators: nEstimators }),
    });
  }

  async predictETA(params: import('../types').ETAPredictRequest): Promise<import('../types').ETAPredictResponse> {
    return this.request<import('../types').ETAPredictResponse>('/eta/predict', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async predictHybridETA(params: import('../types').HybridPredictRequest): Promise<import('../types').HybridPredictResponse> {
    return this.request<import('../types').HybridPredictResponse>('/eta/hybrid', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async runScenario(params: import('../types').ScenarioRunRequest): Promise<import('../types').ScenarioRunResponse> {
    return this.request<import('../types').ScenarioRunResponse>('/scenarios/run', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async getScenarioPresets(): Promise<import('../types').PresetScenario[]> {
    return this.request<import('../types').PresetScenario[]>('/scenarios/presets');
  }

  // Phase 4 Experimentation & Failure Analysis APIs
  async runExperiment(scenarioKey = 'ALL', repetitions = 5): Promise<import('../types').ExperimentBenchmarkResponse> {
    return this.request<import('../types').ExperimentBenchmarkResponse>('/experiments/run', {
      method: 'POST',
      body: JSON.stringify({ scenario_key: scenarioKey, repetitions }),
    });
  }

  async getBenchmarkResults(repetitions = 5): Promise<import('../types').ExperimentBenchmarkResponse> {
    return this.request<import('../types').ExperimentBenchmarkResponse>(`/experiments/results?repetitions=${repetitions}`);
  }

  async getFailureCases(repetitions = 5): Promise<import('../types').ExperimentBenchmarkResponse['failure_analysis']> {
    return this.request<import('../types').ExperimentBenchmarkResponse['failure_analysis']>(`/experiments/failures?repetitions=${repetitions}`);
  }

  async getModelComparison(repetitions = 5): Promise<any> {
    return this.request<any>(`/experiments/comparison?repetitions=${repetitions}`);
  }

  // Phase 6 Dynamic Routing & Simulation Engine APIs
  async getNetworkGraph(): Promise<import('../types').NetworkGraphResponse> {
    return this.request<import('../types').NetworkGraphResponse>('/routing/graph');
  }

  async createActiveTrip(params: import('../types').ActiveTripCreate): Promise<import('../types').ActiveTrip> {
    return this.request<import('../types').ActiveTrip>('/routing/trips', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async listActiveTrips(limit = 50): Promise<import('../types').ActiveTrip[]> {
    return this.request<import('../types').ActiveTrip[]>(`/routing/trips?limit=${limit}`);
  }

  async getActiveTrip(tripId: string): Promise<import('../types').ActiveTrip> {
    return this.request<import('../types').ActiveTrip>(`/routing/trips/${tripId}`);
  }

  async injectDisruption(tripId: string, params: import('../types').DisruptionInjectRequest): Promise<any> {
    return this.request<any>(`/routing/trips/${tripId}/inject-disruption`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async executeReroute(
    tripId: string,
    params: { candidate_strategies?: string[]; force_reroute?: boolean; notes?: string } = {}
  ): Promise<import('../types').RerouteResponse> {
    return this.request<import('../types').RerouteResponse>(`/routing/trips/${tripId}/reroute`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async simulateStep(
    tripId: string,
    params: { step_duration_minutes?: number; auto_reroute_on_disruption?: boolean } = {}
  ): Promise<import('../types').SimulationStepResponse> {
    return this.request<import('../types').SimulationStepResponse>(`/routing/trips/${tripId}/step`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async runRoutingBenchmark(): Promise<import('../types').RoutingExperimentSummary> {
    return this.request<import('../types').RoutingExperimentSummary>('/routing/experiments/run', {
      method: 'POST',
    });
  }

  // Phase 7 Multi-Vehicle Fleet Coordination APIs
  async getFleetState(): Promise<import('../types').FleetStateResponse> {
    return this.request<import('../types').FleetStateResponse>('/fleet/state');
  }

  async getFleetVehicles(): Promise<import('../types').VehicleFleetItem[]> {
    return this.request<import('../types').VehicleFleetItem[]>('/fleet/vehicles');
  }

  async getFleetTasks(status?: string): Promise<import('../types').CollectionTask[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return this.request<import('../types').CollectionTask[]>(`/fleet/tasks${query}`);
  }

  async createCollectionTask(params: import('../types').CollectionTaskCreate): Promise<import('../types').CollectionTask> {
    return this.request<import('../types').CollectionTask>('/fleet/tasks', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async assignTask(taskId: string): Promise<import('../types').TaskAssignResponse> {
    return this.request<import('../types').TaskAssignResponse>(`/fleet/tasks/${taskId}/assign`, {
      method: 'POST',
    });
  }

  async triggerEmergencyTask(taskId: string): Promise<import('../types').TaskAssignResponse> {
    return this.request<import('../types').TaskAssignResponse>(`/fleet/tasks/${taskId}/emergency`, {
      method: 'POST',
    });
  }

  async simulateBreakdown(vehicleId: string, reason = 'MECHANICAL_FAILURE'): Promise<import('../types').VehicleBreakdownResponse> {
    return this.request<import('../types').VehicleBreakdownResponse>(`/fleet/vehicles/${vehicleId}/breakdown`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async recoverVehicle(vehicleId: string): Promise<{ vehicle_id: string; status: string; message: string }> {
    return this.request<{ vehicle_id: string; status: string; message: string }>(`/fleet/vehicles/${vehicleId}/recover`, {
      method: 'POST',
    });
  }

  async rebalanceFleet(triggerReason = 'MANUAL_REBALANCE'): Promise<import('../types').FleetRebalanceResponse> {
    return this.request<import('../types').FleetRebalanceResponse>('/fleet/rebalance', {
      method: 'POST',
      body: JSON.stringify({ trigger_reason: triggerReason }),
    });
  }

  async getFleetEvents(limit = 50): Promise<import('../types').FleetAuditEvent[]> {
    return this.request<import('../types').FleetAuditEvent[]>(`/fleet/events?limit=${limit}`);
  }

  async simulateFleetStep(params: { step_duration_minutes?: number; auto_rebalance_on_disruption?: boolean } = {}): Promise<import('../types').FleetSimulationStepResponse> {
    return this.request<import('../types').FleetSimulationStepResponse>('/fleet/simulate-step', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async runFleetBenchmark(): Promise<import('../types').FleetExperimentSummaryResponse> {
    return this.request<import('../types').FleetExperimentSummaryResponse>('/fleet/experiments/run', {
      method: 'POST',
    });
  }

  // Phase 8 Advanced Optimization Methods
  async getOptimizationSummary(): Promise<import('../types').FleetOptimizationSummary> {
    return this.request<import('../types').FleetOptimizationSummary>('/fleet/optimization/summary');
  }

  async getOptimizationComparison(): Promise<import('../types').AllocationComparison> {
    return this.request<import('../types').AllocationComparison>('/fleet/optimization/comparison');
  }

  async getFailureDiagnostics(): Promise<import('../types').FailureDiagnostic[]> {
    return this.request<import('../types').FailureDiagnostic[]>('/fleet/optimization/failures');
  }

  async runPhase8BenchmarkSuite(forceFresh = true): Promise<import('../types').Phase8ExperimentSummary> {
    return this.request<import('../types').Phase8ExperimentSummary>(`/fleet/optimization/experiments/run?force_fresh=${forceFresh}`, {
      method: 'POST',
    });
  }

  async getPhase8BenchmarkExperiments(): Promise<import('../types').Phase8ExperimentSummary> {
    return this.request<import('../types').Phase8ExperimentSummary>('/fleet/optimization/experiments');
  }

  async triggerPhase8Emergency(locationNode: string, estimatedWasteKg: number): Promise<any> {
    return this.request('/fleet/optimization/emergency', {
      method: 'POST',
      body: JSON.stringify({
        location_node: locationNode,
        estimated_waste_kg: estimatedWasteKg,
        priority: 'URGENT',
      }),
    });
  }

  async triggerPhase8Breakdown(vehicleId: string): Promise<any> {
    return this.request(`/fleet/optimization/breakdown?vehicle_id=${vehicleId}`, {
      method: 'POST',
    });
  }

  async triggerPhase8Rebalance(triggerReason: string, forceRebalance = false): Promise<any> {
    return this.request('/fleet/optimization/rebalance', {
      method: 'POST',
      body: JSON.stringify({
        trigger_reason: triggerReason,
        force_rebalance: forceRebalance,
      }),
    });
  }

  // ---------------------------------------------------------
  // Phase 9: Real-Time IoT Telemetry & Sensor Fusion Methods
  // ---------------------------------------------------------

  async getVehicleTelemetry(): Promise<import('../types').VehicleGPSTelemetry[]> {
    return this.request<import('../types').VehicleGPSTelemetry[]>('/telemetry/vehicles');
  }

  async ingestVehicleTelemetry(telemetry: Record<string, any>): Promise<any> {
    return this.request('/telemetry/vehicle', {
      method: 'POST',
      body: JSON.stringify(telemetry),
    });
  }

  async getBinTelemetry(): Promise<import('../types').BinSensorTelemetry[]> {
    return this.request<import('../types').BinSensorTelemetry[]>('/telemetry/bins');
  }

  async ingestBinTelemetry(telemetry: Record<string, any>): Promise<any> {
    return this.request('/telemetry/bin', {
      method: 'POST',
      body: JSON.stringify(telemetry),
    });
  }

  async getTelemetryHealth(): Promise<import('../types').TelemetryHealthSummary> {
    return this.request<import('../types').TelemetryHealthSummary>('/telemetry/health');
  }

  async getTelemetryAlerts(limit = 50): Promise<import('../types').TelemetryAlert[]> {
    return this.request<import('../types').TelemetryAlert[]>(`/telemetry/alerts?limit=${limit}`);
  }

  async stepTelemetrySimulation(elapsedSeconds = 5.0): Promise<import('../types').RealtimeOperationalState> {
    return this.request<import('../types').RealtimeOperationalState>(`/telemetry/simulate/step?elapsed_seconds=${elapsedSeconds}`, {
      method: 'POST',
    });
  }

  async getFusedFleetState(weather = 'CLEAR', traffic = 'NORMAL'): Promise<import('../types').RealtimeOperationalState> {
    return this.request<import('../types').RealtimeOperationalState>(`/realtime/fleet?weather=${weather}&traffic=${traffic}`);
  }

  async getDepots(): Promise<import('../types').DepotInfo[]> {
    return this.request<import('../types').DepotInfo[]>('/realtime/depots');
  }

  async getAuditLog(limit = 50, action?: string, entityType?: string): Promise<import('../types').AuditEvent[]> {
    let url = `/realtime/audit?limit=${limit}`;
    if (action) url += `&action=${action}`;
    if (entityType) url += `&entity_type=${entityType}`;
    return this.request<import('../types').AuditEvent[]>(url);
  }

  async login(username: string, password: string): Promise<import('../types').TokenResponse> {
    return this.request<import('../types').TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async getCurrentUser(): Promise<import('../types').AuthUser> {
    return this.request<import('../types').AuthUser>('/auth/me');
  }

  async getDemoUsers(): Promise<import('../types').AuthUser[]> {
    return this.request<import('../types').AuthUser[]>('/auth/demo-users');
  }

  async runPhase9BenchmarkSuite(): Promise<import('../types').Phase9BenchmarkSummary> {
    return this.request<import('../types').Phase9BenchmarkSummary>('/telemetry/experiments/run', {
      method: 'POST',
    });
  }

  async getPhase9BenchmarkExperiments(): Promise<import('../types').Phase9BenchmarkSummary> {
    return this.request<import('../types').Phase9BenchmarkSummary>('/telemetry/experiments');
  }

  async runScalabilityBenchmark(): Promise<import('../types').ScalabilityBenchmarkResult> {
    return this.request<import('../types').ScalabilityBenchmarkResult>('/telemetry/scalability/run', {
      method: 'POST',
    });
  }

  async getScalabilityBenchmark(): Promise<import('../types').ScalabilityBenchmarkResult> {
    return this.request<import('../types').ScalabilityBenchmarkResult>('/telemetry/scalability');
  }

  // Phase 10 Final Command Center & Full System Integration
  async getExtendedHealth(): Promise<import('../types').ExtendedHealthResponse> {
    return this.request<import('../types').ExtendedHealthResponse>('/health');
  }

  async runFullSystemDemo(seed: number = 42): Promise<import('../types').SimulationDemoState> {
    return this.request<import('../types').SimulationDemoState>('/simulation/full-system-demo', {
      method: 'POST',
      body: JSON.stringify({ seed }),
    });
  }

  async getDemoState(): Promise<import('../types').SimulationDemoState> {
    return this.request<import('../types').SimulationDemoState>('/simulation/demo-state');
  }

  async getFinalBenchmarks(): Promise<import('../types').FinalBenchmarkComparison> {
    return this.request<import('../types').FinalBenchmarkComparison>('/simulation/benchmarks');
  }
}

export const api = new ApiService();
export default api;




