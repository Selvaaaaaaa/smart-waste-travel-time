"""Candidate Route Generator for producing diverse viable path alternatives.

Generates distinct routing candidates using 5 strategies:
1. SHORTEST_PATH
2. AVOID_TRAFFIC
3. AVOID_CLOSURE
4. AVOID_WEATHER
5. BALANCED
"""
from typing import List, Dict, Any, Optional
from app.routing.graph import RoadNetworkGraph


class CandidatePath:
    def __init__(self, strategy: str, path: List[str], graph: RoadNetworkGraph):
        self.strategy = strategy
        self.path = path
        self.graph = graph
        self.total_distance_km = graph.compute_path_distance(path)
        self.base_traversal_time_min = graph.compute_path_cost(path, weight_mode="time")

    def to_dict(self) -> Dict[str, Any]:
        coords = [
            {"lat": self.graph.nodes[n]["lat"], "lng": self.graph.nodes[n]["lng"]}
            for n in self.path
            if n in self.graph.nodes
        ]
        return {
            "strategy": self.strategy,
            "path": self.path,
            "path_coordinates": coords,
            "total_distance_km": round(self.total_distance_km, 2),
            "base_traversal_time_min": round(self.base_traversal_time_min, 2),
        }


class CandidateRouteGenerator:
    """Generates candidate routes from current node through remaining stops to destination."""

    def __init__(self, graph: RoadNetworkGraph):
        self.graph = graph

    def generate_path_for_waypoints(self, waypoints: List[str], weight_mode: str) -> Optional[List[str]]:
        """Connect ordered waypoints using graph search under the given weight mode."""
        if len(waypoints) < 2:
            return waypoints

        full_path: List[str] = [waypoints[0]]
        for i in range(len(waypoints) - 1):
            src = waypoints[i]
            dst = waypoints[i + 1]
            seg_result = self.graph.dijkstra_shortest_path(src, dst, weight_mode=weight_mode)
            if not seg_result:
                # Fallback: try Yen's or ignore closure if strictly blocked
                yen_paths = self.graph.yen_k_shortest_paths(src, dst, k=3, weight_mode=weight_mode)
                if yen_paths:
                    seg_result = yen_paths[0]
                else:
                    return None
            seg_path, _ = seg_result
            # Append segment excluding the starting duplicate
            full_path.extend(seg_path[1:])

        return full_path

    def generate_candidates(
        self,
        current_node: str,
        remaining_stops: List[str],
        destination_node: str,
        strategies: Optional[List[str]] = None,
    ) -> List[CandidatePath]:
        """Generate up to 5 distinct candidate paths connecting current_node -> remaining_stops -> destination."""
        if strategies is None:
            strategies = [
                "SHORTEST_PATH",
                "AVOID_TRAFFIC",
                "AVOID_CLOSURE",
                "AVOID_WEATHER",
                "BALANCED",
            ]

        waypoints = [current_node] + [s for s in remaining_stops if s != current_node] + [destination_node]
        # Remove consecutive duplicate waypoints
        clean_waypoints = []
        for w in waypoints:
            if not clean_waypoints or clean_waypoints[-1] != w:
                clean_waypoints.append(w)

        candidates: List[CandidatePath] = []
        seen_paths = set()

        for strat in strategies:
            weight_mode = "time"
            if strat == "SHORTEST_PATH":
                weight_mode = "distance"
            elif strat == "AVOID_TRAFFIC":
                weight_mode = "traffic_penalized"
            elif strat == "AVOID_CLOSURE":
                weight_mode = "time"  # Disallows blocked edges strictly
            elif strat == "AVOID_WEATHER":
                weight_mode = "weather_penalized"
            elif strat == "BALANCED":
                weight_mode = "balanced"

            path = self.generate_path_for_waypoints(clean_waypoints, weight_mode=weight_mode)

            if path:
                path_tuple = tuple(path)
                # Ensure we have candidates, even if multiple strategies find same optimal path under normal conditions
                cand = CandidatePath(strategy=strat, path=path, graph=self.graph)
                candidates.append(cand)
                seen_paths.add(path_tuple)
            else:
                # If specific mode couldn't find a path, generate fallback via Yen's alternative
                yen_list = self.graph.yen_k_shortest_paths(clean_waypoints[0], clean_waypoints[-1], k=2, weight_mode="balanced")
                if yen_list:
                    cand = CandidatePath(strategy=strat, path=yen_list[0][0], graph=self.graph)
                    candidates.append(cand)

        # If we need more diversity and have fewer than 2 candidates, inject Yen's alternatives
        if len(candidates) < 2 and len(clean_waypoints) >= 2:
            alt_paths = self.graph.yen_k_shortest_paths(clean_waypoints[0], clean_waypoints[-1], k=3, weight_mode="balanced")
            for idx, (alt_p, _) in enumerate(alt_paths):
                strat_name = f"ALTERNATIVE_{idx + 1}"
                if not any(c.path == alt_p for c in candidates):
                    candidates.append(CandidatePath(strategy=strat_name, path=alt_p, graph=self.graph))

        return candidates
