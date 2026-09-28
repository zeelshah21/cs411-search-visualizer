"""
app.py
Flask backend for the Illinois Intelligent Search Visualizer.

Routes
  GET  /               -> map UI (templates/index.html)
  GET  /api/graph      -> cities, edges, and region from map_data.json
  GET  /api/algorithms -> list of algorithms + their concept notes
  POST /api/search     -> run one algorithm   {source, destination, algorithm}
  POST /api/compare    -> run all algorithms  {source, destination}
"""

import json
import os
import time

from flask import Flask, jsonify, render_template, request

from informed import a_star, greedy_best_first
from uninformed import bfs, dfs, ids, ucs

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "map_data.json")) as f:
    MAP_DATA = json.load(f)

GRAPH = MAP_DATA["graph"]
COORDS = {name: (c["lat"], c["lon"]) for name, c in MAP_DATA["cities"].items()}

ALGORITHMS = {
    "bfs": {
        "name": "Breadth-First Search (BFS)",
        "type": "Uninformed",
        "run": lambda s, g: bfs(GRAPH, s, g),
        "concept": {
            "main_idea": "Explores the map level by level. It visits every city 1 road away from the start, then every city 2 roads away, and so on, until it reaches the destination.",
            "node_selection": "Uses a FIFO queue, so the city that was added to the frontier first is expanded next (the shallowest one).",
            "information_used": "Depth only (number of roads taken). It ignores road distances, so it finds the path with the fewest stops, not the shortest drive.",
            "complete": True,
            "optimal": "Only for fewest edges, not for distance",
        },
    },
    "dfs": {
        "name": "Depth-First Search (DFS)",
        "type": "Uninformed",
        "run": lambda s, g: dfs(GRAPH, s, g),
        "concept": {
            "main_idea": "Goes as deep as possible down one road before backtracking. It keeps following a single route until it hits a dead end or the goal.",
            "node_selection": "Uses a LIFO stack, so the most recently discovered city is expanded next (the deepest one).",
            "information_used": "None beyond the order cities were discovered. No path cost, no heuristic. Paths can be long and roundabout.",
            "complete": "Yes on this finite graph (explored set prevents loops)",
            "optimal": False,
        },
    },
    "ucs": {
        "name": "Uniform-Cost Search (UCS)",
        "type": "Uninformed",
        "run": lambda s, g: ucs(GRAPH, s, g),
        "concept": {
            "main_idea": "Expands outward from the start in order of total distance traveled, like ripples growing by miles instead of by stops.",
            "node_selection": "Uses a priority queue and always expands the city with the lowest path cost g(n) so far.",
            "information_used": "Path cost g(n) (real road distance from OSRM). No heuristic.",
            "complete": True,
            "optimal": True,
        },
    },
    "ids": {
        "name": "Iterative Deepening Search (IDS)",
        "type": "Uninformed",
        "run": lambda s, g: ids(GRAPH, s, g),
        "concept": {
            "main_idea": "Runs depth-limited DFS over and over with limit 0, 1, 2, ... until the goal shows up. Gets BFS's shallowest answer with DFS's small memory use.",
            "node_selection": "Inside each iteration it acts like DFS (deepest node first), but never goes past the current depth limit.",
            "information_used": "Depth only. Re-expands shallow cities every iteration, so its node count is higher than BFS.",
            "complete": True,
            "optimal": "Only for fewest edges, not for distance",
        },
    },
    "greedy": {
        "name": "Greedy Best-First Search",
        "type": "Informed",
        "run": lambda s, g: greedy_best_first(GRAPH, s, g, COORDS),
        "concept": {
            "main_idea": "Always heads toward whichever city looks closest to the destination as the crow flies. Very fast, but can get fooled.",
            "node_selection": "Priority queue ordered by h(n), the straight-line (haversine) distance from the city to the goal. Lowest h(n) goes first.",
            "information_used": "Heuristic h(n) only. It ignores the distance already driven, which is why it isn't optimal.",
            "complete": "Yes on this finite graph (explored set)",
            "optimal": False,
        },
    },
    "astar": {
        "name": "A* Search",
        "type": "Informed",
        "run": lambda s, g: a_star(GRAPH, s, g, COORDS),
        "concept": {
            "main_idea": "Combines UCS and Greedy: it weighs the distance already driven plus an estimate of the distance left, so it heads toward the goal without skipping cheaper routes.",
            "node_selection": "Priority queue ordered by f(n) = g(n) + h(n). The city with the lowest estimated total trip goes first.",
            "information_used": "Both path cost g(n) (OSRM road km) and heuristic h(n) (straight-line km). Straight-line distance never overestimates road distance, so h is admissible and A* is optimal.",
            "complete": True,
            "optimal": True,
        },
    },
}


def run_algorithm(key, source, destination):
    algo = ALGORITHMS[key]
    t0 = time.perf_counter()
    result = algo["run"](source, destination)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    result.update({
        "algorithm": key,
        "algorithm_name": algo["name"],
        "runtime_ms": round(elapsed_ms, 4),
        "num_stops": len(result["path"]) - 1 if result["path"] else None,
    })
    return result


def validate(data, need_algorithm=True):
    source = (data or {}).get("source")
    destination = (data or {}).get("destination")
    if source not in GRAPH or destination not in GRAPH:
        return "Pick a valid source and destination city."
    if need_algorithm and data.get("algorithm") not in ALGORITHMS:
        return f"Unknown algorithm. Choose one of: {', '.join(ALGORITHMS)}"
    return None


@app.route("/")
def index():
    return render_template("index.html", region=MAP_DATA.get("region", ""))


@app.route("/api/graph")
def api_graph():
    return jsonify({
        "region": MAP_DATA.get("region"),
        "cities": MAP_DATA["cities"],
        "edges": MAP_DATA["edges"],
    })


@app.route("/api/algorithms")
def api_algorithms():
    return jsonify({
        key: {"name": a["name"], "type": a["type"], "concept": a["concept"]}
        for key, a in ALGORITHMS.items()
    })


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json(silent=True)
    error = validate(data)
    if error:
        return jsonify({"error": error}), 400
    result = run_algorithm(data["algorithm"], data["source"], data["destination"])
    result["concept"] = ALGORITHMS[data["algorithm"]]["concept"]
    return jsonify(result)


@app.route("/api/compare", methods=["POST"])
def api_compare():
    data = request.get_json(silent=True)
    error = validate(data, need_algorithm=False)
    if error:
        return jsonify({"error": error}), 400
    results = [run_algorithm(k, data["source"], data["destination"]) for k in ALGORITHMS]
    return jsonify({"results": results})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
