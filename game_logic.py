import tkinter
import random






EMPTY_SQUARE = 0
P1_CONST = 1
P1_TEMP = 2
P2_CONST = 3
P2_TEMP = 4
NEUTRAL_BLOCK = 5
BREAK_PROGRESS = 'break'
CONTINUE_PROGRESS = 'cont'
opposites = {P1_CONST:P2_CONST, P1_TEMP:P2_TEMP, P2_CONST:P1_CONST, P2_TEMP:P1_TEMP}
temp_mark = {P1_CONST:P1_TEMP, P2_CONST:P2_TEMP}
turn = [P1_CONST, P2_CONST]
blocked = {P1_CONST:[NEUTRAL_BLOCK, P2_CONST], P2_CONST:[NEUTRAL_BLOCK, P1_CONST]}

def resolve_clash(current, new):
	#rules for what happens when tmp colors overlap, not really sure what its gonna be yet, maybe replace old with new, maybe return to 0, just putting it out here to easily test different methods
	if current == opposites[temp_mark[new]]:
		return temp_mark[new]#change to EMPTY_SQUARE for trying the other variant
	elif current == opposites[new]:
		return BREAK_PROGRESS
	elif current == new:
		return CONTINUE_PROGRESS
	elif current == NEUTRAL_BLOCK:
		return BREAK_PROGRESS
	else:
		return temp_mark[new]

class game:

	def __init__(self, name, args):
		self.height = args['dim_y']
		self.width = args['dim_x']
		self.field = [[NEUTRAL_BLOCK if (random.random() < args['prob']) else EMPTY_SQUARE for i in range(self.width)] for j in range(self.height)]
		self.current_turn = 0
		self.p1_resources = 0
		self.p2_resources = 0
		self.p1_gain = 0
		self.p2_gain = 0
		
	def cross_pick(self, x, y, c):
		if c != turn[self.current_turn % 2]:
			return 0
		if self.field[y][x] in blocked[c]:
			return 0
		self.field[y][x] = c
		self.current_turn += 1
		
		#fill left
		for i in range(len(self.field[y][:x]))[::-1]:
			ret = resolve_clash(self.field[y][i], c)
			if ret == BREAK_PROGRESS:
				break
			elif ret == CONTINUE_PROGRESS:
				continue
			else:
				self.field[y][i] = ret
				
		#fill right
		for i in range(len(self.field[y][x:])-1):
			ret = resolve_clash(self.field[y][x+i+1], c)
			if ret == BREAK_PROGRESS:
				break
			elif ret == CONTINUE_PROGRESS:
				continue
			else:
				self.field[y][x+i+1] = ret
				
		#fill up		  
		for i in range(len(self.field[:y]))[::-1]:
			ret = resolve_clash(self.field[i][x], c)
			if ret == BREAK_PROGRESS:
				break
			elif ret == CONTINUE_PROGRESS:
				continue
			else:
				self.field[i][x] = ret
				
		#fill down
		for i in range(len(self.field[y+1:])):
			ret = resolve_clash(self.field[y+i+1][x], c)
			if ret == BREAK_PROGRESS:
				break
			elif ret == CONTINUE_PROGRESS:
				continue
			else:
				self.field[y+i+1][x] = ret

		self.update_resources()
		return 1
	
	def update_resources(self):
		print(self.field)
		p1_tmp, p2_tmp = 0, 0
		for i in self.field:
			for j in i:
				if j == P1_TEMP or j == P1_CONST:
					p1_tmp += 1
				elif j == P2_TEMP or j == P2_CONST:
					p2_tmp += 1
		self.p1_gain = p1_tmp
		self.p2_gain = p2_tmp
		if self.current_turn % 2: #equiv to p1 turn
			self.p1_resources += p1_tmp
			
			print('player1 current resources: %s (+%s)' % (self.p1_resources, p1_tmp))
		else:
			self.p2_resources += p2_tmp
			
			print('player2 current resources: %s (+%s)' % (self.p2_resources, p2_tmp))
		
	def __repr__(self):
		return '\n'.join(str(i) for i in self.field)