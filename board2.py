# https://jeffbradberry.com/posts/2015/09/intro-to-monte-carlo-tree-search/
import itertools


PIECE_FLAT = 1
PIECE_WALL = 2
PIECE_CAP = 3

piece_names = {
	PIECE_FLAT:'F',
	PIECE_WALL: 'W',
	PIECE_CAP: 'C'
}

def get_color(piece):
	if piece == 0: return 0
	if piece < 0: return -1
	return 1

def sequence_with_sum(n): # all sequences that sum to n. That's pretty nifty eh?
	if n == 0:
		yield ()
		return
	for x in range(1, n + 1):
		for s in sequence_with_sum(n - x):
			yield s + (x,)
	return

def sequences_with_sum_below(n):
	return itertools.chain.from_iterable(map(sequence_with_sum, range(1, n)))

def build_split_table(maxrange, material):
	# build a split table for a given range and material amount...
	return filter(lambda seq: len(seq) <= maxrange, sequences_with_sum_below(material + 1))

_split_table = [[list(build_split_table(r, m)) for r in range(1, m + 1)] for m in range(1, 8)]
def get_splits(material=1, range=1, size=5):
	material = min(material, size)
	range = min(range, material)
	return _split_table[material-1][range-1]

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
				stacks[dest] += stacks[fr][-(usedPieces + count):]
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
				self.capstones = (self.capstones[0] - 1, self.capstones[1])
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

		haveCapstone = (turn > 0 and b.capstones[0]) or (turn < 0 and b.capstones[1])
		stacks = self.stacks
		size = self.size
		for i in range(0, self.squares):
			if len(stacks[i]) == 0:
				if not placements: continue
				# placements
				yield ('place', (i, PIECE_FLAT * turn))
				yield ('place', (i, PIECE_WALL * turn))
				if haveCapstone:
					yield ('place', (i, PIECE_CAP * turn))
			elif stacks[i][-1] * turn > 0:
				piece = stacks[i][-1] * turn
				x = i % 8
				y = int(i / 8)
				material = len(stacks[i])
				if x > 0:
					delta = self.index(-1, 0)
					for split in get_splits(material, x, size=size):
						yield ('split', (i, delta, split))
				if x < size - 1:
					delta = self.index(1, 0)
					for split in get_splits(material, size - x - 1, size=size):
						yield ('split', (i, delta, split))
				if y > 0:
					delta = self.index(0 , -1)
					for split in get_splits(material, y, size=size):
						yield ('split', (i, delta, split))
				if y < size - 1:
					delta = self.index(0, 1)
					for split in get_splits(material, size - y - 1, size=size):
						yield ('split', (i, delta, split))


	def get_winner(self):
		def sides_connected(mask):
			size = self.size

			def recursive(flood, x, y):
				flood[self.index(x, y)] = True
				if x > 0 and not flood[self.index(x - 1, y)] and mask[self.index(x - 1, y)]:
					recursive(flood, x - 1, y)
				if x < size - 1 and not flood[self.index(x + 1, y)] and mask[self.index(x + 1, y)]:
					recursive(flood, x + 1, y)
				if y > 0 and not flood[self.index(x, y - 1)] and mask[self.index(x, y - 1)]:
					recursive(flood, x, y - 1)
				if y < size - 1 and not flood[self.index(x, y + 1)] and mask[self.index(x, y + 1)]:
					recursive(flood, x, y + 1)

			floodHor = [False] * self.squares
			for x in range(0, size):
				recursive(floodHor, x, 0)
			for x in range(0, size):
				if floodHor[self.index(x, size - 1)]: return True
			floodVrt = [False] * self.squares
			for y in range(0, size):
				recursive(floodVrt, 0, y)
			for y in range(0, size):
				if floodVrt[self.index(size - 1, x)]: return True
			return False

		if self.pieces[0] + self.capstones[0] == 0 or self.pieces[1] + self.capstones[1] == 0:
			return sum(s[-1] == 0 and 0 (s[-1] > 0 and 1 or -1) for s in self.stacks)

		costsWhite = [len(stack) > 0 and stack[-1] > 0 for stack in self.stacks]
		costsBlack = [len(stack) > 0 and stack[-1] < 0 for stack in self.stacks]
		if sides_connected(costsWhite):
			return 1
		elif sides_connected(costsBlack):
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

b = Board().withSize(size=5)
