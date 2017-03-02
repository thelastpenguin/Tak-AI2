from board2 import *

class Minmax():
	def __init__(self, eval):
		self._eval = eval

	def minmax(self, board, depth=2):
		if depth == 0 or board.get_winner() != 0:
			return (self._eval(board) * board.playerTurn, None)

		children = ((move, board.apply_move(move[0], *move[1])) for move in board.moves())
		return max(
			(
				# should be running negamax since we negate the score from 1 level down.
				-self.minmax(board, depth - 1)[0],
				move
			) for move, board in children
		)
	def __call__(self, board):
		return self.minmax(board, depth=2)
