import random
from board2 import Board

b = Board().withSize(size=5)
for x in range(0, 20):
	moves = list(b.moves())
	print(repr(b))
	for type, args in moves:
		print(repr(b.apply_move(type, *args)))

	type, args = random.choice(moves)
	b = b.apply_move(type, *args)
	print("")
