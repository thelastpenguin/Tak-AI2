from board2 import *
from minmax import *
from eval import *

b = Board().withSize(size=5)

evaluator = Pipeline(
	(MFlatCoverage(), 1.0),
	(MDjikstraDistance(), 4.0)
)
print (evaluator)

ai = Minmax(evaluator)

while True:
	score, (type, args) = ai(b)
	b = b.apply_move(type, *args)
	print(b)
	if b.get_winner() != 0:
		break 
