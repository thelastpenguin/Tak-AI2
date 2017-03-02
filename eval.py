from board2 import *
import sys
from djikstra import djikstra

class Pipeline:
	def __init__(self, *modules):
		self._modules = []
		self._weights = []

		for module, weight in modules:
			self._weights.append(float(weight))
			self._modules.append(module)

	def add_module(self, name, weight, module):
		self._modules.append(module)
		self._weights.append(float(weight))
		return self

	def __call__(self, board):
		game_over = board.get_winner()
		if game_over < 0 or game_over > 0:
			return game_over * 100000 # returns the game over score.

		#indexesWithPieces = [i for i in range(0, board.squares) if len(board.stacks[i]) > 0]

		return sum(m(board) * w for m, w in zip(self._modules, self._weights) if w != 0)

	def __str__(self):
		return "Pipeline(\n\t%s\n)" % (",\n\t".join("(" + str(m) + ", " + str(w) + ")" for m, w in zip(self._modules, self._weights)))

class MFlatCoverage:
	name = "Flat Coverage"
	def __call__(self, board):
		scores = {
			PIECE_FLAT: 1.0,
			-PIECE_FLAT: -1.0
		}
		return sum(s[-1] in scores and scores[s[-1]] or 0 for s in board.stacks if len(s) > 0)

	def __str__(self):
		return "MFlatCoverage()"

class MNoFeedTheBeast:
	name = "No Feed the Beast"
	def __init__(self, domWeight=1.3, subWeight=1.0):
		# TODO: add a way for these to be changed
		self._domWeight = float(domWeight)
		self._subWeight = float(subWeight)

	def mutate(self):
		# TODO: implement mutation of the individual modules...
		pass

	def __call__(self, board):
		total = 0

		domWeight = self._domWeight
		subWeight = self._subWeight

		for s in board.stacks:
			if len(s) == 0: continue
			if s[-1] < 0:
				wB = domWeight
				wW = subWeight
			else:
				wB = subWeight
				wW = domWeight
			total += sum(p < 0 and wB or wW for p in s)

		return total

	def __str__(self):
		return "MNoFeedTheBeast(domWeight=%d, subWeight=%d)" % (self._domWeight, self._subWeight)

class MDjikstraDistance:
	name = "Djikstra Distance"

	def __call__(self, board):
		whiteCostsHor = tuple(not (len(s) > 0 and (s[-1] == PIECE_FLAT or s[-1] == PIECE_CAP)) and 1 or 0 for s in board.stacks)
		blackCostsHor = tuple(not (len(s) > 0 and (s[-1] == -PIECE_FLAT or s[-1] == -PIECE_CAP)) and 1 or 0 for s in board.stacks)
		whiteCostsVrt = tuple(whiteCostsHor[x + y * board.size] for x, y in itertools.product(range(0, board.size), range(0, board.size)))
		blackCostsVrt = tuple(blackCostsHor[x + y * board.size] for x, y in itertools.product(range(0, board.size), range(0, board.size)))

		whiteHorDist = djikstra(whiteCostsHor, board.size)
		blackHorDist = djikstra(blackCostsHor, board.size)
		whiteVrtDist = djikstra(whiteCostsVrt, board.size)
		blackVrtDist = djikstra(blackCostsVrt, board.size)

		return whiteHorDist + whiteVrtDist - blackHorDist - blackVrtDist

	def __str__(self):
		return "MDjikstraDistance()"

# pipeline = Pipeline(
# 	(MFlatCoverage(), 1.0),
# 	(MNoFeedTheBeast(domWeight=1.3, subWeight=1.0), 0.1),
# 	(MDjikstraDistance(), 0.1)
# )
