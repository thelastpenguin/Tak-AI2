import sys
import queue

_cache = {}
_cleanup_queue = queue.Queue()
_max_cache_size = 100000

def djikstra(costs, size):
	if costs in _cache:
		return _cache[costs]

	q = queue.PriorityQueue()
	distances = [sys.maxsize] * (size * size)
	visited = [False] * (size * size)

	for x in range(0, size):
		distances[x] = costs[x]
		q.put((x, 0, distances[x]))

	def process_neighbor(lastx, lasty, x, y):
		if x < 0 or x >= size or y < 0 or y >= size: return
		cur = x + y * size
		if visited[cur]: return # ignore vistied neighbors
		parent = lastx + lasty * size
		distances[cur] = min(distances[cur], distances[parent] + costs[cur])
		q.put((x, y, distances[cur]))

	while not q.empty():
		x, y, dist = q.get()
		if visited[x + y * size]: continue
		visited[x + y * size] = True
		process_neighbor(x, y, x + 1, y)
		process_neighbor(x, y, x - 1, y)
		process_neighbor(x, y, x, y + 1)
		process_neighbor(x, y, x, y - 1)

	dist = min(distances[x + size * (size - 1)] for x in range(0, size))
	_cache[costs] = dist
	_cleanup_queue.put(costs)

	if _cleanup_queue.qsize() > _max_cache_size:
		del _cache[_cleanup_queue.get()]

	return dist
