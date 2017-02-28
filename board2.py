# https://jeffbradberry.com/posts/2015/09/intro-to-monte-carlo-tree-search/

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

	def split(self, fr, sequence):
		usedPieces = 0
		stacks = list(self.stacks)
		for pos, count in reversed(sequence):
			stacks[pos] += stacks[fr][-(usedPieces + count + 1):-(usedPieces + 1)]
			usedPieces += count
		stacks[fr] = stacks[fr][:-usedPieces]
		self.stacks = tuple(stacks)

	def index(self, x, y):
		return self.size * y + x

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
	def toTupple(self):
		return (
			self.size,
			self.playerTurn,
			self.moveno < 2,
			self.pieces,
			self.capstones,
			self.stacks
		)


	def iterate_moves(self):
		turn = self.playerTurn
		if self.moveno < 2:
			turn = -turn
			for i in range(0, self.squares):
				b = Board().fromParent(self)
				b.place(i, PIECE_FLAT * turn)
				yield b
			return

		haveCapstone = (turn > 0 and b.capstones[0]) or (turn < 0 and b.capstones[1])

		for i in range(0, self.size * self.size):
			if len(self.stacks[i]) == 0:
				# placements
				b = Board().fromParent(self)
				b.place(i, PIECE_FLAT * turn)
				yield b
				b = Board().fromParent(self)
				b.place(i, PIECE_WALL * turn)
				yield b
				if haveCapstone:
					b = Board().fromParent(self)
					b.place(i, PIECE_CAP * turn)
					yield

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

b = Board().withSize(size=5)
b.place(0, PIECE_FLAT)
b.place(1, PIECE_FLAT)
b.place(2, PIECE_FLAT)
b.place(3, PIECE_FLAT)
b.place(4, PIECE_FLAT)
print b
print b.get_winner()
