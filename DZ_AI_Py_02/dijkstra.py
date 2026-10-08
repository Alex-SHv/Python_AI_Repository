import heapq

from graph import GRAPH


def dijkstra(graph, start, end):
    cost = {node: float("inf") for node in graph}
    prev = {node: None for node in graph}
    cost[start] = 0
    queue = [(0, start)]
    done = set()

    while queue:
        current, node = heapq.heappop(queue)
        if node in done:
            continue
        done.add(node)

        for neighbor, road in graph[node].items():
            new_cost = current + road["distance"]
            if new_cost < cost[neighbor]:
                cost[neighbor] = new_cost
                prev[neighbor] = node
                heapq.heappush(queue, (new_cost, neighbor))

    if cost[end] == float("inf"):
        return None

    path = [end]
    while prev[path[-1]] is not None:
        path.append(prev[path[-1]])
    path.reverse()
    return route_info(graph, path)


def route_info(graph, path):
    roads = [graph[a][b] for a, b in zip(path, path[1:])]
    return {
        "path": path,
        "distance": sum(r["distance"] for r in roads),
        "time": sum(r["time"] for r in roads),
    }


def all_paths(graph, start, end, path=None):
    path = path or [start]
    if path[-1] == end:
        return [route_info(graph, path)]
    results = []
    for neighbor in graph[path[-1]]:
        if neighbor not in path:
            results += all_paths(graph, start, end, path + [neighbor])
    return results


def find_routes(start, end, graph=GRAPH):
    best = dijkstra(graph, start, end)
    others = [r for r in all_paths(graph, start, end) if r["path"] != best["path"]]
    return {"best": best, "alternatives": sorted(others, key=lambda r: r["distance"])}


def format_path(path):
    return " → ".join(path)