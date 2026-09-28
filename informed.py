"""
informed.py
Informed (heuristic) search: Greedy Best-First Search and A*.

graph:  adjacency dict {city: {neighbor: road_distance_km}}
coords: {city: (lat, lon)}

Heuristic h(n) = straight-line (great-circle / haversine) distance in km from n to the goal.
A road can never be shorter than the straight line, so h(n) never overestimates
-> admissible (and consistent), so A* is optimal on this graph.

Returns the same dict format as uninformed.py.
"""

import heapq
import math

from uninformed import _result

EARTH_RADIUS_KM = 6371.0


def haversine(a, b):
    """Great-circle distance in km between two (lat, lon) points."""
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def heuristic(node, goal, coords):
    return haversine(coords[node], coords[goal])


# ---------------------------------------------------------------------------
# Greedy Best-First Search
# Priority queue ordered by h(n) only -> expands whatever looks closest to the goal.
# Fast, but ignores the cost already traveled, so it is not optimal.
# ---------------------------------------------------------------------------
def greedy_best_first(graph, start, goal, coords):
    counter = 0
    frontier = [(heuristic(start, goal, coords), counter, start, [start])]
    explored = set()
    expanded_order = []

    while frontier:
        _, _, node, path = heapq.heappop(frontier)
        if node in explored:
            continue
        explored.add(node)
        expanded_order.append(node)

        if node == goal:
            return _result(graph, path, expanded_order)

        for nbr in sorted(graph[node]):
            if nbr not in explored:
                counter += 1
                heapq.heappush(frontier, (heuristic(nbr, goal, coords), counter, nbr, path + [nbr]))

    return _result(graph, None, expanded_order)


# ---------------------------------------------------------------------------
# A* Search
# Priority queue ordered by f(n) = g(n) + h(n)
#   g(n) = road distance traveled so far, h(n) = straight-line distance left.
# Goal test on pop -> optimal with an admissible heuristic.
# ---------------------------------------------------------------------------
def a_star(graph, start, goal, coords):
    counter = 0
    frontier = [(heuristic(start, goal, coords), 0.0, counter, start, [start])]
    best_g = {start: 0.0}
    explored = set()
    expanded_order = []

    while frontier:
        f, g, _, node, path = heapq.heappop(frontier)
        if node in explored:
            continue
        explored.add(node)
        expanded_order.append(node)

        if node == goal:
            return _result(graph, path, expanded_order)

        for nbr in sorted(graph[node]):
            new_g = g + graph[node][nbr]
            if nbr not in explored and new_g < best_g.get(nbr, float("inf")):
                best_g[nbr] = new_g
                counter += 1
                new_f = new_g + heuristic(nbr, goal, coords)
                heapq.heappush(frontier, (new_f, new_g, counter, nbr, path + [nbr]))

    return _result(graph, None, expanded_order)


# aliases
greedy = greedy_best_first
greedy_best_first_search = greedy_best_first
astar = a_star
a_star_search = a_star
