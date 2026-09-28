"""
uninformed.py
Uninformed (blind) search: BFS, DFS, UCS, IDS.

graph: adjacency dict  {city: {neighbor: road_distance_km, ...}, ...}

Every function returns a dict:
    found           -> True/False
    path            -> list of cities from start to goal ([] if not found)
    cost            -> total road distance of the path in km
    nodes_expanded  -> how many nodes were taken off the frontier and expanded
    expanded_order  -> the cities in the order they were expanded (for the visualizer)
"""

import heapq
from collections import deque


def path_cost(graph, path):
    """Sum the edge distances along a path."""
    return round(sum(graph[path[i]][path[i + 1]] for i in range(len(path) - 1)), 2)


def _result(graph, path, expanded_order):
    return {
        "found": bool(path),
        "path": path or [],
        "cost": path_cost(graph, path) if path else None,
        "nodes_expanded": len(expanded_order),
        "expanded_order": expanded_order,
    }


def _neighbors(graph, node):
    # sorted so the results are deterministic (same run -> same answer)
    return sorted(graph[node])


# ---------------------------------------------------------------------------
# Breadth-First Search
# FIFO queue -> expands the shallowest node first (fewest edges).
# Goal test when a node is generated (AIMA version).
# ---------------------------------------------------------------------------
def bfs(graph, start, goal):
    if start == goal:
        return _result(graph, [start], [start])

    frontier = deque([start])
    parent = {start: None}          # also works as the "reached" set
    expanded_order = []

    while frontier:
        node = frontier.popleft()
        expanded_order.append(node)
        for nbr in _neighbors(graph, node):
            if nbr not in parent:
                parent[nbr] = node
                if nbr == goal:
                    return _result(graph, _build_path(parent, goal), expanded_order)
                frontier.append(nbr)

    return _result(graph, None, expanded_order)


# ---------------------------------------------------------------------------
# Depth-First Search
# LIFO stack -> always expands the deepest (most recently added) node.
# Graph-search version with an explored set so it can't loop forever.
# ---------------------------------------------------------------------------
def dfs(graph, start, goal):
    frontier = [(start, [start])]
    explored = set()
    expanded_order = []

    while frontier:
        node, path = frontier.pop()
        if node in explored:
            continue
        explored.add(node)
        expanded_order.append(node)

        if node == goal:
            return _result(graph, path, expanded_order)

        # push in reverse so the alphabetically-first neighbor is popped first
        for nbr in reversed(_neighbors(graph, node)):
            if nbr not in explored:
                frontier.append((nbr, path + [nbr]))

    return _result(graph, None, expanded_order)


# ---------------------------------------------------------------------------
# Uniform-Cost Search
# Priority queue ordered by g(n) = path cost so far.
# Goal test when a node is popped, which is what makes it optimal.
# ---------------------------------------------------------------------------
def ucs(graph, start, goal):
    counter = 0                                   # tie-breaker for heapq
    frontier = [(0.0, counter, start, [start])]
    best_g = {start: 0.0}
    explored = set()
    expanded_order = []

    while frontier:
        g, _, node, path = heapq.heappop(frontier)
        if node in explored:
            continue
        explored.add(node)
        expanded_order.append(node)

        if node == goal:
            return _result(graph, path, expanded_order)

        for nbr in _neighbors(graph, node):
            new_g = g + graph[node][nbr]
            if nbr not in explored and new_g < best_g.get(nbr, float("inf")):
                best_g[nbr] = new_g
                counter += 1
                heapq.heappush(frontier, (new_g, counter, nbr, path + [nbr]))

    return _result(graph, None, expanded_order)


# ---------------------------------------------------------------------------
# Iterative Deepening Search
# Runs depth-limited DFS with limit 0, 1, 2, ... until the goal is found.
# Only checks for cycles along the current path (keeps DFS's low memory).
# ---------------------------------------------------------------------------
def ids(graph, start, goal, max_depth=None):
    if max_depth is None:
        max_depth = len(graph)          # a simple path can't be longer than this
    expanded_order = []                 # counts ALL iterations (re-expansions included)

    for limit in range(max_depth + 1):
        result = _depth_limited(graph, start, goal, limit, [start], expanded_order)
        if result is not None:
            out = _result(graph, result, expanded_order)
            out["depth_reached"] = limit
            return out

    return _result(graph, None, expanded_order)


def _depth_limited(graph, node, goal, limit, path, expanded_order):
    expanded_order.append(node)
    if node == goal:
        return path
    if limit == 0:
        return None
    for nbr in _neighbors(graph, node):
        if nbr not in path:             # avoid cycles on the current path
            found = _depth_limited(graph, nbr, goal, limit - 1, path + [nbr], expanded_order)
            if found is not None:
                return found
    return None


def _build_path(parent, goal):
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    return path[::-1]


# longer aliases
breadth_first_search = bfs
depth_first_search = dfs
uniform_cost_search = ucs
iterative_deepening_search = ids
