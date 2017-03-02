# https://jeffbradberry.com/posts/2015/09/intro-to-monte-carlo-tree-search/
import itertools
import functools
from djikstra import djikstra

PIECE_FLAT = 1
PIECE_WALL = 2
PIECE_CAP = 3

piece_names = {
	PIECE_FLAT:'F',
	PIECE_WALL: 'W',
	PIECE_CAP: 'C'
}

@functools.lru_cache(maxsize=16, typed=False)
def sequence_with_sum(n): # all sequences that sum to n. That's pretty nifty eh?
	if n == 0:
		yield ()
		return
	for x in range(1, n + 1):
		for s in sequence_with_sum(n - x):
			yield s + (x,)
	return

@functools.lru_cache(maxsize=16, typed=False)
def sequences_with_sum_below(n):
	return itertools.chain.from_iterable(map(sequence_with_sum, range(1, n)))

@functools.lru_cache(maxsize=128, typed=False)
def splits(material, range):
	range = min(range, material)
	return filter(lambda seq: len(seq) == range, sequences_with_sum_below(material))

# every change made to a board actually copies it effectively...
class Board:
	def __init__(self, size=5):
		pass

	def withSize(self, size=5):
		self.size = size
		self.squares = self.size * self.size
		self.playerTurn = 1
		self.moveno = 0
		self.stacks = ((),) * 25
		self.pieces = (20, 20)
		self.capstones = (1, 1)
		return self

	def fromParent(self, parent):
		self.size = parent.size
		self.squares = self.size * self.size
		self.stacks = parent.stacks
		self.playerTurn = parent.playerTurn
		self.moveno = parent.moveno
		self.pieces = parent.pieces
		self.capstones = parent.capstones
		return self

	def fromEncoding(str):
		str = str.replace(';', ',')
		segments = str.split(',')
		meta = segments[0:7]
		board = segments[7:]

		# TODO: finish this function

	def index(self, x, y):
		return self.size * y + x

	def split(self, fr, delta, sequence):
		usedPieces = 0
		stacks = list(self.stacks)
		dest = fr
		# TODO: debug this
		for count in reversed(sequence):
			dest += delta

			if usedPieces == 0:
				stacks[dest] += stacks[fr][-count:]
			else:
				stacks[dest] += stacks[fr][-(usedPieces + count):-(usedPieces)]
			usedPieces += count
		stacks[fr] = stacks[fr][:-usedPieces]
		self.stacks = tuple(stacks)

		self.moveno += 1
		self.playerTurn = -self.playerTurn

	def place(self, pos, piece):
		stacks = list(self.stacks)
		stacks[pos] += (piece,)
		self.stacks = tuple(stacks)

		if piece < 0:
			if piece == -PIECE_CAP:
				self.capstones = (self.capstones[0], self.capstones[1] - 1)
			else:
				self.pieces = (self.pieces[0], self.pieces[1] - 1)
		else:
			if piece == PIECE_CAP:
				self.capstones = (self.capstones[0] - 1, self.capstones[1])
			else:
				self.pieces = (self.pieces[0] - 1, self.pieces[1])

		self.moveno += 1
		self.playerTurn = -self.playerTurn

	def toTupple(self):
		return (
			self.size,
			self.playerTurn,
			self.moveno < 2,
			self.pieces,
			self.capstones,
			self.stacks
		)

	def apply_move(self, type, *args):
		copy = Board().fromParent(self)
		if type == 'place':
			copy.place(*args)
		elif type == 'split':
			copy.split(*args)
		else:
			assert False
		return copy

	def moves(self, placements=True):
		turn = self.playerTurn
		if self.moveno < 2:
			turn = -turn
			for i in range(0, self.squares):
				if len(self.stacks[i]) == 0:
					yield ('place', (i, PIECE_FLAT * turn))
			return

		haveCapstone = (turn > 0 and self.capstones[0] > 0) or (turn < 0 and self.capstones[1] > 0)
		stacks = self.stacks
		size = self.size

		for x, y in itertools.product(range(0, 5), range(0, 5)):
			i = self.index(x, y)
			if len(stacks[i]) == 0:
				if not placements: continue
				# placements
				yield ('place', (i, PIECE_FLAT * turn))
				yield ('place', (i, PIECE_WALL * turn))
				if haveCapstone:
					yield ('place', (i, PIECE_CAP * turn))
			elif stacks[i][-1] * turn > 0:
				piece = stacks[i][-1] * turn
				material = min(len(stacks[i]), self.size)

				# TODO: check that the split  does not walk over a capstone or wall.
				#       that is very muchly not allowed and should generally speaking be prevented.
				#       okay well that was fun.
				if x > 0:
					delta = self.index(-1, 0)
					for split in split(material, x):
						landOnIndex = self.index(x - len(split), y)
						yield ('split', (i, delta, split))
				if x < size - 1:
					delta = self.index(1, 0)
					for split in get_splits(material, size - x - 1):
						landOnIndex = self.index(x + len(split), y)
						yield ('split', (i, delta, split))
				if y > 0:
					delta = self.index(0 , -1)
					for split in splits(material, y):
						landOnIndex = self.index(x, y - len(split))
						yield ('split', (i, delta, split))
				if y < size - 1:
					delta = self.index(0, 1)
					for split in splits(material, size - y - 1):
						landOnIndex = self.index(x, y + len(split))
						yield ('split', (i, delta, split))

	# returns a list of offsets that do not go off the board from the given coordinate
	def directions_from_coordinate(x, y):
		if x > 0:
			yield -1
		if x < self.size - 1:
			yield 1
		if y > 0:
			yield -self.size
		if y < self.size - 1:
			yield self.size

	# returns the winner if one can be found using a rather simple flood fill implementation
	def get_winner(self):
		if self.pieces[0] + self.capstones[0] == 0 or self.pieces[1] + self.capstones[1] == 0:
			return sum(s[-1] == 0 and 0 (s[-1] > 0 and 1 or -1) for s in self.stacks)

		whiteCostsHor = tuple(not (len(s) > 0 and (s[-1] == PIECE_FLAT or s[-1] == PIECE_CAP)) and 1 or 0 for s in self.stacks)
		whiteCostsVrt = tuple(whiteCostsHor[x + y * self.size] for x, y in itertools.product(range(0, self.size), range(0, self.size)))

		if djikstra(whiteCostsHor, self.size) == 0 or djikstra(whiteCostsVrt, self.size) == 0:
			return 1

		blackCostsHor = tuple(not (len(s) > 0 and (s[-1] == -PIECE_FLAT or s[-1] == -PIECE_CAP)) and 1 or 0 for s in self.stacks)
		blackCostsVrt = tuple(blackCostsHor[x + y * self.size] for x, y in itertools.product(range(0, self.size), range(0, self.size)))

		if djikstra(blackCostsHor, self.size) == 0 or djikstra(blackCostsVrt, self.size) == 0:
			return -1

		return 0

	def __hash__(self):
		return hash(self.toTupple())

	def __eq__(self, other):
		return self.toTupple() == other.toTupple()

	def __repr__(self):
		return repr(self.stacks)

	def __str__(self):
		output = []
		output.append(("%2s " + "    %-6s " * self.size) % (("",) + tuple([chr(ord('A') + x) for x in range(0, self.size)])))
		for y in range(0, self.size):
			row = []
			for x in range(0, self.size):
				row.append("".join([(p < 0 and "b" or "w") + piece_names[abs(p)] for p in self.stacks[self.index(x, y)]]))
			output.append(("%2d|" + "%-10s|" * self.size) % ((y,) + tuple(row)))
		return "\n".join(output)

	def __repr__(self):
		meta = []
		meta.append(str(self.size))
		meta.append(str(self.moveno))
		meta.append(self.playerTurn < 0 and 'b' or 'w')
		meta.append(str(self.pieces[0]))
		meta.append(str(self.pieces[1]))
		meta.append(str(self.capstones[0]))
		meta.append(str(self.capstones[1]))

		board = []
		for s in self.stacks:
			if len(s) > 0:
				board.append(("".join([p < 0 and 'b' or 'w' for p in s])) + piece_names[abs(s[-1])])
			else:
				board.append("")

		return ",".join(meta) + ";" + ",".join(board)
