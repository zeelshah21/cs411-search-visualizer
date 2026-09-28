# CS 411 Project 1 - Illinois search visualizer (Flask backend)

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
            "main_idea": "Searches level by level. First it checks all cities 1 road away, then 2 roads away, and keeps going until it finds the destination.",
            "node_selection": "Uses a FIFO queue so the city added first gets expanded first (shallowest node).",
            "information_used": "Only depth (how many roads). It doesn't look at distance so it finds the path with the fewest stops, not the shortest one.",
            "complete": True,
            "optimal": "Only for fewest edges, not for distance",
        },
    },
    "dfs": {
        "name": "Depth-First Search (DFS)",
        "type": "Uninformed",
        "run": lambda s, g: dfs(GRAPH, s, g),
        "concept": {
            "main_idea": "Goes as deep as it can down one path before backtracking. It keeps following one route until it gets stuck or finds the goal.",
            "node_selection": "Uses a LIFO stack so the newest city found gets expanded first (deepest node).",
            "information_used": "Nothing except the order cities were found. No cost and no heuristic, so paths can be really long.",
            "complete": "Yes on this finite graph (explored set prevents loops)",
            "optimal": False,
        },
    },
    "ucs": {
        "name": "Uniform-Cost Search (UCS)",
        "type": "Uninformed",
        "run": lambda s, g: ucs(GRAPH, s, g),
        "concept": {
            "main_idea": "Expands out from the start based on total distance so far, so it grows by miles instead of by number of stops.",
            "node_selection": "Uses a priority queue and always picks the city with the lowest path cost g(n).",
            "information_used": "Path cost g(n) (road distance from OSRM). No heuristic.",
            "complete": True,
            "optimal": True,
        },
    },
    "ids": {
        "name": "Iterative Deepening Search (IDS)",
        "type": "Uninformed",
        "run": lambda s, g: ids(GRAPH, s, g),
        "concept": {
            "main_idea": "Runs depth-limited DFS with limit 0, 1, 2, ... until it finds the goal. Gets the same answer as BFS but uses less memory like DFS.",
            "node_selection": "Each round works like DFS (deepest first) but stops at the current depth limit.",
            "information_used": "Only depth. It re-expands the shallow cities every round so it expands more nodes than BFS.",
            "complete": True,
            "optimal": "Only for fewest edges, not for distance",
        },
    },
    "greedy": {
        "name": "Greedy Best-First Search",
        "type": "Informed",
        "run": lambda s, g: greedy_best_first(GRAPH, s, g, COORDS),
        "concept": {
            "main_idea": "Always goes to the city that looks closest to the destination in a straight line. Pretty fast but it can pick bad routes.",
            "node_selection": "Priority queue sorted by h(n), the straight-line (haversine) distance to the goal. Lowest h(n) goes first.",
            "information_used": "Only the heuristic h(n). It ignores how far it already drove, that's why it's not optimal.",
            "complete": "Yes on this finite graph (explored set)",
            "optimal": False,
        },
    },
    "astar": {
        "name": "A* Search",
        "type": "Informed",
        "run": lambda s, g: a_star(GRAPH, s, g, COORDS),
        "concept": {
            "main_idea": "Basically UCS + Greedy. It uses the distance already driven plus an estimate of what's left, so it moves toward the goal but doesn't skip cheaper routes.",
            "node_selection": "Priority queue sorted by f(n) = g(n) + h(n). Lowest estimated total goes first.",
            "information_used": "Uses g(n) (OSRM road km) and h(n) (straight-line km). Straight-line distance is never more than road distance so h is admissible and A* is optimal.",
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
