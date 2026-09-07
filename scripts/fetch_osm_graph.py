#!/usr/bin/env python3
"""CLI script: Fetch a real OpenStreetMap road sub-graph and compare with the synthetic graph.

Saves the result to data/osm_graph_sample.json and prints a summary to stdout.

Usage:
    python scripts/fetch_osm_graph.py
    python scripts/fetch_osm_graph.py --lat 40.7128 --lon -74.0060 --radius 2000

The default coordinates cover lower Manhattan, NY — used as a representative
dense urban municipal district for comparison.
"""
import argparse
import json
import sys
from pathlib import Path

# Make sure the backend package is importable
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.routing.osm_loader import fetch_osm_subgraph, compare_with_synthetic_graph
from app.routing.graph import get_default_network_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch OSM road sub-graph and compare with synthetic network")
    parser.add_argument("--lat", type=float, default=40.7128, help="Centre latitude (default: lower Manhattan)")
    parser.add_argument("--lon", type=float, default=-74.0060, help="Centre longitude")
    parser.add_argument("--radius", type=int, default=2000, help="Radius in metres (default: 2000)")
    parser.add_argument("--out", type=str, default="", help="Output JSON path (default: data/osm_graph_sample.json)")
    args = parser.parse_args()

    print("=" * 70)
    print("OSM REAL-WORLD ROAD NETWORK FETCH")
    print("=" * 70)
    print(f"  Centre:  ({args.lat}, {args.lon})")
    print(f"  Radius:  {args.radius} m")
    print(f"  Source:  Overpass API (openstreetmap.org)")
    print()

    print("[1/3] Fetching OSM subgraph via Overpass API...")
    osm_data = fetch_osm_subgraph(lat=args.lat, lon=args.lon, radius_m=args.radius)
    status = osm_data["status"]
    if status == "success":
        print(f"      ✓ Fetched in {osm_data['query_duration_s']:.2f}s")
        print(f"      Nodes: {osm_data['nodes']}  |  Ways: {osm_data['ways']}")
        print(f"      Road types: {', '.join(osm_data['unique_road_types'])}")
    elif status == "offline":
        print(f"      ! Offline/timeout — using cached estimates: {osm_data['error_message']}")
    else:
        print(f"      ! Status: {status} — {osm_data.get('error_message', '')}")

    print()
    print("[2/3] Loading synthetic network graph...")
    synthetic_graph = get_default_network_graph()
    print(f"      Synthetic graph loaded.")

    print()
    print("[3/3] Comparing OSM vs synthetic graph...")
    comparison = compare_with_synthetic_graph(osm_data, synthetic_graph)
    syn = comparison["synthetic"]
    osm = comparison["osm"]
    cmp = comparison["comparison"]
    print(f"      Synthetic: {syn['nodes']} nodes, {syn['edges']} edges")
    print(f"      OSM real:  {osm['nodes']} nodes, {osm['ways']} ways")
    print(f"      Node scale factor:  {cmp['node_scale_factor']}×")
    print(f"      Way scale factor:   {cmp['way_scale_factor']}×")
    if cmp["real_world_coverage_area_km2"]:
        print(f"      Coverage area:      {cmp['real_world_coverage_area_km2']} km²")

    # Save to JSON
    out_path = Path(args.out) if args.out else Path(__file__).resolve().parent.parent / "data" / "osm_graph_sample.json"
    out_path.parent.mkdir(exist_ok=True)
    payload = {
        "osm_fetch": {k: v for k, v in osm_data.items() if k != "raw_elements"},
        "comparison": comparison,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    print()
    print(f"Results saved to: {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
