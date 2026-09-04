"""Deterministic Municipal Road Graph representation and graph traversal algorithms.

Research & Simulation Disclaimer:
This is a deterministic simulation and research prototype.
It does not represent live municipal routing or live GPS data.
"""
import heapq
import math
from typing import Dict, List, Tuple, Optional, Any, Set


class RoadNetworkGraph:
    """Directed, weighted municipal graph with dynamic edge attributes."""

    def __init__(self):
        # node_id -> { 'name': str, 'lat': float, 'lng': float, 'node_type': str }
        self.nodes: Dict[str, Dict[str, Any]] = {}
        # (u, v) -> { 'distance_km': float, 'speed_limit_kmh': float, 'road_type': str,
        #             'is_blocked': bool, 'congestion_factor': float, 'weather_penalty_factor': float }
        self.edges: Dict[Tuple[str, str], Dict[str, Any]] = {}
        # u -> list of target node ids v
        self.adjacency: Dict[str, List[str]] = {}

    def add_node(self, node_id: str, name: str, lat: float, lng: float, node_type: str = "intersection"):
        self.nodes[node_id] = {
            "name": name,
            "lat": lat,
            "lng": lng,
            "node_type": node_type,
        }
        if node_id not in self.adjacency:
            self.adjacency[node_id] = []

    def add_edge(
        self,
        source: str,
        target: str,
        distance_km: float,
        speed_limit_kmh: float = 40.0,
        road_type: str = "arterial",
        bidirectional: bool = True,
    ):
        if source not in self.nodes or target not in self.nodes:
            raise ValueError(f"Nodes {source} and {target} must exist before adding edge.")

        edge_data = {
            "distance_km": distance_km,
            "speed_limit_kmh": speed_limit_kmh,
            "road_type": road_type,
            "is_blocked": False,
            "congestion_factor": 1.0,
            "weather_penalty_factor": 1.0,
        }

        self.edges[(source, target)] = dict(edge_data)
        if target not in self.adjacency[source]:
            self.adjacency[source].append(target)

        if bidirectional:
            self.edges[(target, source)] = dict(edge_data)
            if source not in self.adjacency[target]:
                self.adjacency[target].append(source)

    def get_edge(self, source: str, target: str) -> Optional[Dict[str, Any]]:
        return self.edges.get((source, target))

    def set_edge_blocked(self, source: str, target: str, is_blocked: bool = True, bidirectional: bool = True):
        if (source, target) in self.edges:
            self.edges[(source, target)]["is_blocked"] = is_blocked
        if bidirectional and (target, source) in self.edges:
            self.edges[(target, source)]["is_blocked"] = is_blocked

    def set_edge_congestion(self, source: str, target: str, factor: float, bidirectional: bool = True):
        if (source, target) in self.edges:
            self.edges[(source, target)]["congestion_factor"] = max(0.2, factor)
        if bidirectional and (target, source) in self.edges:
            self.edges[(target, source)]["congestion_factor"] = max(0.2, factor)

    def set_edge_weather_penalty(self, source: str, target: str, factor: float, bidirectional: bool = True):
        if (source, target) in self.edges:
            self.edges[(source, target)]["weather_penalty_factor"] = max(0.5, factor)
        if bidirectional and (target, source) in self.edges:
            self.edges[(target, source)]["weather_penalty_factor"] = max(0.5, factor)

    def reset_dynamic_conditions(self):
        """Reset all edge congestions, closures, and weather penalties."""
        for edge_key in self.edges:
            self.edges[edge_key]["is_blocked"] = False
            self.edges[edge_key]["congestion_factor"] = 1.0
            self.edges[edge_key]["weather_penalty_factor"] = 1.0

    def compute_edge_cost(
        self,
        source: str,
        target: str,
        weight_mode: str = "time",
        ignore_closures: bool = False,
    ) -> float:
        """Compute traversal cost for an edge.

        weight_mode: 'time' (traversal minutes), 'distance' (km), 'traffic_penalized', 'weather_penalized', 'balanced'
        """
        edge = self.edges.get((source, target))
        if not edge:
            return float("inf")

        if edge["is_blocked"] and not ignore_closures:
            return float("inf")

        distance_km = edge["distance_km"]
        base_speed = edge["speed_limit_kmh"]
        congestion = edge["congestion_factor"]
        weather = edge["weather_penalty_factor"]

        # Base traversal time in minutes
        effective_speed = max(5.0, base_speed / (congestion * weather))
        base_time_min = (distance_km / effective_speed) * 60.0

        if weight_mode == "distance":
            return distance_km
        elif weight_mode == "time":
            return base_time_min
        elif weight_mode == "traffic_penalized":
            # Heavier weight on congestion
            return base_time_min * (congestion**1.5)
        elif weight_mode == "weather_penalized":
            # Extra penalty for weather sensitive roads
            weather_mult = 2.0 if edge["road_type"] in ["highway", "arterial"] and weather > 1.2 else 1.0
            return base_time_min * weather * weather_mult
        elif weight_mode == "balanced":
            # Composite cost: 60% dynamic time + 40% distance
            return 0.6 * base_time_min + 0.4 * distance_km
        else:
            return base_time_min

    def dijkstra_shortest_path(
        self,
        source: str,
        target: str,
        weight_mode: str = "time",
        excluded_edges: Optional[Set[Tuple[str, str]]] = None,
        excluded_nodes: Optional[Set[str]] = None,
    ) -> Optional[Tuple[List[str], float]]:
        """Dijkstra algorithm for finding the lowest cost path between source and target."""
        if source not in self.nodes or target not in self.nodes:
            return None

        if source == target:
            return ([source], 0.0)

        excluded_edges = excluded_edges or set()
        excluded_nodes = excluded_nodes or set()

        # Priority queue stores (cost, current_node, path)
        pq = [(0.0, source, [source])]
        visited: Dict[str, float] = {source: 0.0}

        while pq:
            cost, u, path = heapq.heappop(pq)

            if u == target:
                return (path, cost)

            if cost > visited.get(u, float("inf")):
                continue

            for v in self.adjacency.get(u, []):
                if v in excluded_nodes and v != target:
                    continue
                if (u, v) in excluded_edges:
                    continue

                edge_cost = self.compute_edge_cost(u, v, weight_mode=weight_mode)
                if math.isinf(edge_cost):
                    continue

                new_cost = cost + edge_cost
                if new_cost < visited.get(v, float("inf")):
                    visited[v] = new_cost
                    heapq.heappush(pq, (new_cost, v, path + [v]))

        return None

    def yen_k_shortest_paths(
        self,
        source: str,
        target: str,
        k: int = 3,
        weight_mode: str = "time",
    ) -> List[Tuple[List[str], float]]:
        """Yen's algorithm for finding up to k loopless shortest paths."""
        first_path = self.dijkstra_shortest_path(source, target, weight_mode=weight_mode)
        if not first_path:
            return []

        a_paths: List[Tuple[List[str], float]] = [first_path]
        b_candidates: List[Tuple[float, List[str]]] = []

        for i in range(1, k):
            prev_path, _ = a_paths[i - 1]

            for j in range(len(prev_path) - 1):
                spur_node = prev_path[j]
                root_path = prev_path[: j + 1]

                excluded_edges: Set[Tuple[str, str]] = set()
                for p, _ in a_paths:
                    if len(p) > j and p[: j + 1] == root_path:
                        excluded_edges.add((p[j], p[j + 1]))

                excluded_nodes: Set[str] = set(root_path[:-1])

                spur_result = self.dijkstra_shortest_path(
                    spur_node,
                    target,
                    weight_mode=weight_mode,
                    excluded_edges=excluded_edges,
                    excluded_nodes=excluded_nodes,
                )

                if spur_result:
                    spur_path, _ = spur_result
                    total_path = root_path[:-1] + spur_path
                    # Calculate total path cost
                    total_cost = self.compute_path_cost(total_path, weight_mode=weight_mode)
                    if not math.isinf(total_cost):
                        candidate_entry = (total_cost, total_path)
                        if candidate_entry not in b_candidates:
                            heapq.heappush(b_candidates, candidate_entry)

            if not b_candidates:
                break

            # Pick the lowest cost candidate that is not already in a_paths
            while b_candidates:
                cost, path = heapq.heappop(b_candidates)
                if not any(p == path for p, _ in a_paths):
                    a_paths.append((path, cost))
                    break

        return a_paths

    def compute_path_cost(self, path: List[str], weight_mode: str = "time") -> float:
        """Compute the aggregate cost of a node path."""
        if not path or len(path) < 2:
            return 0.0
        total_cost = 0.0
        for i in range(len(path) - 1):
            c = self.compute_edge_cost(path[i], path[i + 1], weight_mode=weight_mode)
            if math.isinf(c):
                return float("inf")
            total_cost += c
        return total_cost

    def compute_path_distance(self, path: List[str]) -> float:
        """Compute total real distance in km for a path."""
        if not path or len(path) < 2:
            return 0.0
        dist = 0.0
        for i in range(len(path) - 1):
            edge = self.edges.get((path[i], path[i + 1]))
            if edge:
                dist += edge["distance_km"]
            else:
                dist += 2.0  # Fallback default
        return dist


def get_default_network_graph() -> RoadNetworkGraph:
    """Build the standard 14-node deterministic simulated municipal network."""
    g = RoadNetworkGraph()

    # 1. Add Nodes
    g.add_node("DEPOT_CENTRAL", "Central Fleet Depot", 40.7128, -74.0060, node_type="depot")
    g.add_node("COLLECTION_ZONE_A", "Downtown Commercial Zone A", 40.7250, -74.0020, node_type="collection")
    g.add_node("COLLECTION_ZONE_B", "Midtown Business Zone B", 40.7380, -73.9900, node_type="collection")
    g.add_node("COLLECTION_ZONE_C", "Uptown Mixed-Use Zone C", 40.7500, -73.9800, node_type="collection")
    g.add_node("COLLECTION_ZONE_D", "North Residential Zone D", 40.7620, -73.9700, node_type="collection")
    g.add_node("COLLECTION_ZONE_E", "West Waterfront Zone E", 40.7450, -74.0200, node_type="collection")
    g.add_node("COLLECTION_ZONE_F", "East Industrial Zone F", 40.7280, -73.9600, node_type="collection")
    g.add_node("TRANSFER_STATION_NORTH", "North Transfer Hub", 40.7750, -73.9550, node_type="transfer_station")
    g.add_node("TRANSFER_STATION_SOUTH", "South Recycling Terminal", 40.7000, -74.0150, node_type="transfer_station")
    g.add_node("LANDFILL_MAIN", "Regional Landfill Facility", 40.7900, -73.9400, node_type="landfill")
    g.add_node("INTERSECTION_CENTRAL_1", "Central Junction 1", 40.7300, -74.0100, node_type="intersection")
    g.add_node("INTERSECTION_CENTRAL_2", "Midtown Junction 2", 40.7400, -73.9750, node_type="intersection")
    g.add_node("INTERSECTION_NORTH_1", "North Bypass 1", 40.7600, -73.9900, node_type="intersection")
    g.add_node("INTERSECTION_EAST_1", "East Corridor 1", 40.7150, -73.9800, node_type="intersection")

    # 2. Add Edges with realistic distances & speed limits
    # South / Depot connections
    g.add_edge("DEPOT_CENTRAL", "TRANSFER_STATION_SOUTH", distance_km=2.2, speed_limit_kmh=45.0, road_type="arterial")
    g.add_edge("DEPOT_CENTRAL", "COLLECTION_ZONE_A", distance_km=1.8, speed_limit_kmh=35.0, road_type="residential")
    g.add_edge("DEPOT_CENTRAL", "INTERSECTION_EAST_1", distance_km=2.5, speed_limit_kmh=50.0, road_type="arterial")
    g.add_edge("TRANSFER_STATION_SOUTH", "INTERSECTION_CENTRAL_1", distance_km=3.6, speed_limit_kmh=40.0, road_type="arterial")

    # Lower Midtown / Central connections
    g.add_edge("COLLECTION_ZONE_A", "COLLECTION_ZONE_B", distance_km=2.0, speed_limit_kmh=30.0, road_type="residential")
    g.add_edge("COLLECTION_ZONE_A", "INTERSECTION_CENTRAL_1", distance_km=1.2, speed_limit_kmh=40.0, road_type="arterial")
    g.add_edge("INTERSECTION_EAST_1", "COLLECTION_ZONE_F", distance_km=2.4, speed_limit_kmh=45.0, road_type="arterial")
    g.add_edge("INTERSECTION_CENTRAL_1", "COLLECTION_ZONE_E", distance_km=2.1, speed_limit_kmh=40.0, road_type="arterial")
    g.add_edge("INTERSECTION_CENTRAL_1", "COLLECTION_ZONE_B", distance_km=1.9, speed_limit_kmh=35.0, road_type="residential")

    # Midtown to Uptown
    g.add_edge("COLLECTION_ZONE_B", "COLLECTION_ZONE_C", distance_km=1.9, speed_limit_kmh=30.0, road_type="residential")
    g.add_edge("COLLECTION_ZONE_B", "INTERSECTION_CENTRAL_2", distance_km=1.5, speed_limit_kmh=40.0, road_type="arterial")
    g.add_edge("COLLECTION_ZONE_E", "INTERSECTION_NORTH_1", distance_km=2.8, speed_limit_kmh=50.0, road_type="highway")
    g.add_edge("COLLECTION_ZONE_F", "INTERSECTION_CENTRAL_2", distance_km=2.2, speed_limit_kmh=45.0, road_type="arterial")
    g.add_edge("INTERSECTION_CENTRAL_2", "COLLECTION_ZONE_C", distance_km=1.6, speed_limit_kmh=35.0, road_type="residential")

    # Uptown to North
    g.add_edge("COLLECTION_ZONE_C", "COLLECTION_ZONE_D", distance_km=1.8, speed_limit_kmh=30.0, road_type="residential")
    g.add_edge("COLLECTION_ZONE_C", "INTERSECTION_NORTH_1", distance_km=1.7, speed_limit_kmh=40.0, road_type="arterial")
    g.add_edge("INTERSECTION_CENTRAL_2", "TRANSFER_STATION_NORTH", distance_km=4.5, speed_limit_kmh=55.0, road_type="highway")
    g.add_edge("INTERSECTION_NORTH_1", "COLLECTION_ZONE_D", distance_km=1.9, speed_limit_kmh=40.0, road_type="arterial")
    g.add_edge("COLLECTION_ZONE_D", "TRANSFER_STATION_NORTH", distance_km=2.1, speed_limit_kmh=45.0, road_type="arterial")

    # North to Landfill
    g.add_edge("TRANSFER_STATION_NORTH", "LANDFILL_MAIN", distance_km=3.2, speed_limit_kmh=60.0, road_type="highway")
    g.add_edge("INTERSECTION_NORTH_1", "LANDFILL_MAIN", distance_km=4.8, speed_limit_kmh=55.0, road_type="highway")
    g.add_edge("COLLECTION_ZONE_D", "LANDFILL_MAIN", distance_km=3.9, speed_limit_kmh=50.0, road_type="arterial")

    return g
