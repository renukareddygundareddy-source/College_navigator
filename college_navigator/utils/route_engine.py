"""
utils/route_engine.py
----------------------
Shortest-path route computation over the campus walkway graph
(graph_nodes + graph_edges) using Dijkstra's algorithm.

Why a graph instead of a straight line?
A straight line from A to B would cut through buildings, gardens and
walls. Real navigation needs to follow actual walkable paths. We model
the campus as a weighted undirected graph: nodes = path junctions,
edges = walkway segments with a real-world distance in meters. This is
the same core idea used by Google Maps / OSRM, just scoped down to a
campus and computed locally instead of calling an external routing
service (which keeps the project free, offline-capable, and easy to
customize for any campus layout).

Average human walking speed used for ETA: 1.4 m/s (~5 km/h).
"""

import heapq
import math
import sqlite3

WALKING_SPEED_MPS = 1.4  # meters per second


def _get_graph(conn):
    """Load nodes and edges into adjacency-list form."""
    nodes = {}
    for row in conn.execute("SELECT id, label, latitude, longitude FROM graph_nodes"):
        nodes[row[0]] = {"label": row[1], "lat": row[2], "lng": row[3]}

    adjacency = {node_id: [] for node_id in nodes}
    for row in conn.execute("SELECT node_a_id, node_b_id, distance_m FROM graph_edges"):
        a, b, dist = row
        adjacency[a].append((b, dist))
        adjacency[b].append((a, dist))  # undirected

    return nodes, adjacency


def dijkstra(nodes, adjacency, start_id, end_id):
    """
    Classic Dijkstra shortest-path search.
    Returns (ordered list of node_ids on the path, total distance in meters)
    or (None, None) if unreachable.
    """
    distances = {node_id: math.inf for node_id in nodes}
    previous = {node_id: None for node_id in nodes}
    distances[start_id] = 0
    visited = set()

    heap = [(0, start_id)]
    while heap:
        current_dist, current_id = heapq.heappop(heap)
        if current_id in visited:
            continue
        visited.add(current_id)

        if current_id == end_id:
            break

        for neighbor_id, edge_dist in adjacency.get(current_id, []):
            if neighbor_id in visited:
                continue
            new_dist = current_dist + edge_dist
            if new_dist < distances[neighbor_id]:
                distances[neighbor_id] = new_dist
                previous[neighbor_id] = current_id
                heapq.heappush(heap, (new_dist, neighbor_id))

    if distances[end_id] == math.inf:
        return None, None

    # reconstruct path
    path = []
    node = end_id
    while node is not None:
        path.append(node)
        node = previous[node]
    path.reverse()

    return path, distances[end_id]


def compute_route(db_path, start_node_id, end_node_id):
    """
    High level helper used by the Flask API layer.

    Returns a dict:
    {
        "coordinates": [[lat, lng], [lat, lng], ...],  # for Leaflet polyline
        "distance_m": 123.4,
        "eta_minutes": 1.5,
        "node_path": [1, 2, 5]
    }
    or None if no route exists.
    """
    conn = sqlite3.connect(db_path)
    try:
        nodes, adjacency = _get_graph(conn)

        if start_node_id not in nodes or end_node_id not in nodes:
            return None

        path, distance = dijkstra(nodes, adjacency, start_node_id, end_node_id)
        if path is None:
            return None

        coordinates = [[nodes[n]["lat"], nodes[n]["lng"]] for n in path]
        eta_seconds = distance / WALKING_SPEED_MPS
        eta_minutes = round(eta_seconds / 60, 1)

        return {
            "coordinates": coordinates,
            "distance_m": round(distance, 1),
            "eta_minutes": max(eta_minutes, 0.1),
            "node_path": path,
        }
    finally:
        conn.close()
