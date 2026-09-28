"""
data_fetcher.py
Builds the Illinois road-network graph and saves it to map_data.json.

  1. Geocode every city with the Nominatim (OpenStreetMap) API -> lat/lon
  2. Get the real driving distance for every connection with the OSRM API
  3. Build an adjacency-list graph and check that it is fully connected
  4. Save everything to map_data.json

Run:  python data_fetcher.py
"""

import json
import time
from collections import deque
from datetime import datetime, timezone

import requests

REGION = "Illinois, USA"
STATE = "Illinois"
OUTPUT_FILE = "map_data.json"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"

# Nominatim's usage policy requires a real User-Agent and max 1 request/sec
HEADERS = {"User-Agent": "CS411-Search-Visualizer/1.0 (UIC student project)"}
NOMINATIM_DELAY = 1.1
OSRM_DELAY = 0.3

# 25 Illinois cities
CITIES = [
    "Chicago", "Waukegan", "Elgin", "Aurora", "Naperville",
    "Joliet", "Kankakee", "Rockford", "DeKalb", "Freeport",
    "Galena", "Moline", "Galesburg", "Peoria", "Bloomington",
    "Champaign", "Danville", "Decatur", "Springfield", "Macomb",
    "Quincy", "Effingham", "Mount Vernon", "Carbondale", "Belleville",
]

# Road connections between neighboring cities (mostly along interstates/US routes).
# Each pair is undirected. The distance comes from OSRM, not from here.
CONNECTIONS = [
    ("Chicago", "Waukegan"),        # I-94
    ("Chicago", "Elgin"),           # I-90
    ("Chicago", "Naperville"),      # I-88
    ("Chicago", "Joliet"),          # I-55
    ("Chicago", "Kankakee"),        # I-57
    ("Waukegan", "Rockford"),       # IL-173 / US-20
    ("Elgin", "Rockford"),          # I-90
    ("Elgin", "Aurora"),            # IL-31
    ("Aurora", "Naperville"),       # US-34
    ("Aurora", "DeKalb"),           # I-88
    ("Naperville", "Joliet"),       # IL-59
    ("Joliet", "Kankakee"),         # US-45
    ("Joliet", "Bloomington"),      # I-55
    ("DeKalb", "Rockford"),         # IL-23 / I-39
    ("DeKalb", "Moline"),           # I-88
    ("DeKalb", "Bloomington"),      # I-39
    ("Rockford", "Freeport"),       # US-20
    ("Freeport", "Galena"),         # US-20
    ("Galena", "Moline"),           # IL-84
    ("Moline", "Galesburg"),        # I-74
    ("Galesburg", "Peoria"),        # I-74
    ("Galesburg", "Macomb"),        # US-67
    ("Macomb", "Quincy"),           # US-136 / IL-336
    ("Macomb", "Peoria"),           # IL-9 / US-136
    ("Peoria", "Bloomington"),      # I-74
    ("Peoria", "Springfield"),      # I-155 / I-55
    ("Bloomington", "Champaign"),   # I-74
    ("Bloomington", "Springfield"), # I-55
    ("Kankakee", "Champaign"),      # I-57
    ("Kankakee", "Danville"),       # IL-1
    ("Champaign", "Danville"),      # I-74
    ("Champaign", "Decatur"),       # I-72
    ("Champaign", "Effingham"),     # I-57
    ("Decatur", "Springfield"),     # I-72
    ("Decatur", "Effingham"),       # IL-32 / I-57
    ("Springfield", "Quincy"),      # I-72
    ("Springfield", "Belleville"),  # I-55 / I-64
    ("Effingham", "Belleville"),    # I-70 / I-64
    ("Effingham", "Mount Vernon"),  # I-57
    ("Mount Vernon", "Belleville"), # I-64
    ("Mount Vernon", "Carbondale"), # I-57 / IL-13
    ("Carbondale", "Belleville"),   # IL-13 / IL-4
]


def geocode_city(city):
    """Return (lat, lon, display_name) for a city using Nominatim."""
    params = {"city": city, "state": STATE, "country": "USA", "format": "json", "limit": 1}
    for attempt in range(3):
        try:
            resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            results = resp.json()
            if results:
                r = results[0]
                return float(r["lat"]), float(r["lon"]), r.get("display_name", city)
            raise ValueError(f"No Nominatim result for {city}")
        except (requests.RequestException, ValueError) as e:
            print(f"  geocode attempt {attempt + 1} failed for {city}: {e}")
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Could not geocode {city}")


def road_distance(a, b):
    """Return (distance_km, duration_min) of the driving route between two coords via OSRM."""
    url = OSRM_URL.format(lat1=a["lat"], lon1=a["lon"], lat2=b["lat"], lon2=b["lon"])
    for attempt in range(3):
        try:
            resp = requests.get(url, params={"overview": "false"}, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                return round(route["distance"] / 1000, 2), round(route["duration"] / 60, 1)
            raise ValueError(f"OSRM returned {data.get('code')}")
        except (requests.RequestException, ValueError) as e:
            print(f"  OSRM attempt {attempt + 1} failed: {e}")
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("Could not get OSRM distance")


def is_connected(graph):
    """BFS from any node; the graph is connected if every node gets reached."""
    start = next(iter(graph))
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nbr in graph[node]:
            if nbr not in seen:
                seen.add(nbr)
                queue.append(nbr)
    return len(seen) == len(graph)


def build_graph():
    # 1. geocode
    print(f"Geocoding {len(CITIES)} cities with Nominatim...")
    cities = {}
    for city in CITIES:
        lat, lon, name = geocode_city(city)
        cities[city] = {"lat": lat, "lon": lon, "display_name": name}
        print(f"  {city:<14} {lat:.4f}, {lon:.4f}")
        time.sleep(NOMINATIM_DELAY)

    # 2. road distances
    print(f"\nFetching {len(CONNECTIONS)} road distances with OSRM...")
    edges = []
    graph = {city: {} for city in CITIES}
    for u, v in CONNECTIONS:
        dist_km, dur_min = road_distance(cities[u], cities[v])
        edges.append({"source": u, "target": v, "distance_km": dist_km, "duration_min": dur_min})
        graph[u][v] = dist_km   # undirected graph -> add both directions
        graph[v][u] = dist_km
        print(f"  {u:<13} <-> {v:<13} {dist_km:>7.1f} km  ({dur_min} min)")
        time.sleep(OSRM_DELAY)

    # 3. connectivity check
    connected = is_connected(graph)
    print(f"\nCities: {len(cities)} | Edges: {len(edges)} | Fully connected: {connected}")
    if not connected:
        raise RuntimeError("Graph is not connected. Add more CONNECTIONS.")

    return {
        "region": REGION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {"geocoding": "Nominatim OpenStreetMap", "routing": "OSRM"},
        "num_cities": len(cities),
        "num_edges": len(edges),
        "connected": connected,
        "cities": cities,
        "edges": edges,
        "graph": graph,
    }


if __name__ == "__main__":
    data = build_graph()
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved graph to {OUTPUT_FILE}")
