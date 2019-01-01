import tkinter
import random
import requests
import argparse
import time
EMPTY_SQUARE = 0
P1_CONST = 1
P1_TEMP = 2
P2_CONST = 3
P2_TEMP = 4
NEUTRAL_BLOCK = 5

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--server', help='http://address:port of the server you connect to')
parser.add_argument('-g', '--game-id', help='a unique code used to join your game(you can make one up)')
parser.add_argument('-n', '--name', help='your display name in the game')
parser.add_argument('-x', '--dim-x', help='dim_x of board, not needed if joining')
parser.add_argument('-y', '--dim-y', help='dim_y of board, not needed if joining')
parser.add_argument('-p', '--prob', help='density of blocked squares, not needed if joining')
parser.add_argument('-t', '--turn-time', help='time per turn, not needed if joining')

args = parser.parse_args()              
         
address = args.server
game = args.game_id
pname = args.name
join = args.dim_x==None

if not join:
	dim_x = int(args.dim_x)
	dim_y = int(args.dim_y)
	prob = float(args.prob)
	turn_time = int(args.turn_time)



colors = {P1_CONST:'blue', P2_CONST:'forest green', P1_TEMP:'dodger blue', P2_TEMP:'green yellow', EMPTY_SQUARE:'grey', NEUTRAL_BLOCK:'black'}
jarjar = {}
lazy_slackers = ['we can\'t sit here all day!', 'turtle mode initiated...', 'time to make a mooooove!', 'zzzZZZzzZZZ', 'today???',
				'plz mov i slep.', 'think faster:)', '....well?????', 'the clock is ticking...', 'gogogogogo', 'gotta go fast', 
				'thisisaverysecretmessagepleasereaditfastbeforeitdisappears', 'ok bye']
class client:

	def __init__(self, address, game, pname):
		self.address = address
		self.game_name = game
		self.player_name = pname
		
	def send_play(self, x, y, ui):
		print(x, y)
		r = requests.post(self.address+'/play/'+self.game_name, cookies=jarjar, data={'play_x':x, 'play_y':y})
		args = r.json()
		ui.board.update(args['p1_gain'], args['p2_gain'], args['p1_resources'], args['p2_resources'], args['field'], args['turn'])
		ui.recolor_board()
		return r

	def send_create(self, dim_x, dim_y, prob, turn_time):
		r = requests.post(self.address+'/create/'+self.game_name, data={'player_name':self.player_name,'dim_x':dim_x, 'dim_y':dim_y, 'prob':prob, 'turn_time':turn_time}, cookies=jarjar)
		return r

	def send_join(self):
		r = requests.post(self.address+'/join/'+self.game_name, data={'player_name':self.player_name}, cookies=jarjar)
		
		return r

	def send_start(self):
		r = requests.get(self.address+'/start/'+self.game_name, cookies=jarjar)
		return r

	def send_status(self, verbose=False):
		par = {}
		if verbose:
			par['verbose'] = True
		r = requests.get(self.address+'/status/'+self.game_name, cookies=jarjar, params=par)
		return r

	def send_leave(self):
		#later
		pass

class board:
	def __init__(self, height, width, prob, turn_time):
		#placeholder
		self.height = height
		self.width = width
		self.field = [[NEUTRAL_BLOCK if (random.random() < prob) else EMPTY_SQUARE for i in range(self.width)] for j in range(self.height)]
		self.p1_resources = 0
		self.p2_resources = 0
		self.p1_gain = 0
		self.p2_gain = 0
		self.turn = 0
		#self.timer = -1
		
		self.turn_time = turn_time
		self.time_left = turn_time
	
	def update(self, p1_gain, p2_gain, p1_resources, p2_resources, field, turn):
		self.p1_gain = p1_gain
		self.p2_gain = p2_gain
		self.p1_resources = p1_resources
		self.p2_resources = p2_resources
		self.field = field
		if turn == self.turn:
			self.time_left -= 1
		else:
			self.time_left = self.turn_time
		
		self.turn = turn
	
		
class game_ui(tkinter.Frame):
	def __init__(self, board, score_indicators, turn_indicator, time_indicator, client, master=None):
		tkinter.Frame.__init__(self, master)
		self.master = master
		self.board = board
		self.client = client
		self.buttons = [[EMPTY_SQUARE for i in range(board.width)] for i in range(board.height)]
		self.score_indicators = score_indicators
		self.turn_indicator = turn_indicator
		self.time_indicator = time_indicator
		for i in range(board.height)[::-1]:
			for j in range(board.width)[::-1]:
				self.buttons[i][j] = tkinter.Button(master,height=1,width=3)
				self.buttons[i][j].configure(command=lambda r=i,s=j: self.client.send_play(s, r, self))
				self.buttons[i][j].grid(row=i,column=j)
				
	def recolor_board(self):
		for i in range(self.board.height)[::-1]:
			for j in range(self.board.width)[::-1]:
				self.buttons[i][j].configure(bg=colors[self.board.field[i][j]])
		tmp_resource = [self.board.p1_resources, self.board.p2_resources]
		tmp_gain = [self.board.p1_gain, self.board.p2_gain]
		for i,s in enumerate(self.score_indicators):
			s.configure(text='%s: %s (+%s) ' % (pnames[i],tmp_resource[i],tmp_gain[i]))
		turn_now = self.board.turn % 2
		self.turn_indicator.configure(text='%s\'s turn' % pnames[turn_now], fg=colors[P2_CONST if turn_now else P1_CONST])
		shown_time = 'time left: %s' % self.board.time_left if self.board.time_left > 0 else random.choice(lazy_slackers)
		self.time_indicator.configure(text=shown_time, fg=colors[P2_CONST if turn_now else P1_CONST])
		return 0 



cl = client(address, game, pname)
if join:
	res = cl.send_join()
	args = res.json()
	dim_x, dim_y, prob, turn_time = args['dim_x'], args['dim_y'], args['prob'], args['turn_time']
else:
	res = cl.send_create(dim_x, dim_y, prob, turn_time)
jarjar = res.cookies

nice_board = board(dim_x, dim_y, prob, turn_time)
r = input('press enter when ready')
res = cl.send_start()
if not res.json()['result']:
	print('waiting for players to join...')
	while 1:
		res = cl.send_status()
		#print(res.content)
		if res.json()['state']=='ongoing_game':
			break
		time.sleep(2)

def update_task():
	res = cl.send_status(verbose=True)
	j = res.json()
	nice_board.update(j['p1_gain'],j['p2_gain'],j['p1_resources'],j['p2_resources'],j['field'], j['turn'])
	
	app.recolor_board()
	root.after(1000, update_task)
		
res = cl.send_status().json()
pnames = (res['player1'],res['player2'])

root = tkinter.Tk()
score_frame=tkinter.Frame(root)
board_frame=tkinter.Frame(root)
score_frame.pack(side=tkinter.TOP,fill=tkinter.X)
turn_frame=tkinter.Frame(root)
turn_frame.pack(side=tkinter.TOP)
turn_indicator = tkinter.Label(turn_frame, text='game starting...', fg=colors[NEUTRAL_BLOCK])
turn_indicator.pack(side=tkinter.TOP)
time_indicator = tkinter.Label(turn_frame, text='time left: ?', fg = colors[NEUTRAL_BLOCK])
time_indicator.pack(side=tkinter.BOTTOM)
p1_score,p2_score = tkinter.Label(score_frame, text='player1',fg=colors[P1_CONST]), tkinter.Label(score_frame, text='player2',fg=colors[P2_CONST])
p1_score.pack(side=tkinter.LEFT)
p2_score.pack(side=tkinter.RIGHT)
board_frame.pack(side=tkinter.BOTTOM,fill=tkinter.X)
app = game_ui(nice_board, (p1_score, p2_score), turn_indicator, time_indicator, cl, board_frame)
app.recolor_board()
root.after(1000, update_task)
root.mainloop()

cl.send_leave()