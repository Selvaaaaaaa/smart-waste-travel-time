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
}

export const api = new ApiService();
export default api;

