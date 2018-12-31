from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.web import server, resource
import cgi
import uuid
import json
from game_logic import *
prep_area = {}#contains game names & stuff for unstarted games
ongoing_games ={}#contains started games

RESULT_SUCCESS = 1
RESULT_ERROR = 0
EMPTY_SQUARE = 0
P1_CONST = 1
P1_TEMP = 2
P2_CONST = 3
P2_TEMP = 4
NEUTRAL_BLOCK = 5

class CreateGame(Resource):
	def getChild(self, name, request):        
		return CreateSub(name)
		
class CreateSub(Resource):
	isLeaf = True
	def __init__(self, name):
		Resource.__init__(self)
		if name == b'':
			name = uuid.uuid4().hex
		self.name = name.decode('utf-8')

	def render_POST(self, request):
		user_id = request.getSession().uid.decode('utf-8')
		player_name = request.args[b'player_name'][0].decode('utf-8')
		dim_x, dim_y = int(request.args[b'dim_x'][0]), int(request.args[b'dim_y'][0])
		prob = float(request.args[b'prob'][0])
		if self.name in prep_area or self.name in ongoing_games:
			print('game already in prep or ongoing')
			res = {'result': RESULT_ERROR, 'message': 'a game with this name already exists'}
		else:
			prep_area[self.name] = {'name':self.name, 'dim_x':dim_x, 'dim_y': dim_y, 'prob': prob,
									'players_list':{user_id:player_name}, 'ready':{}}
			print('game added to prep area: {}'.format(prep_area[self.name]))
			res = {i:v for i,v in prep_area[self.name].items()}
			res['result'] = RESULT_SUCCESS
		return json.dumps(res).encode('utf-8')

class JoinGame(Resource):
	def getChild(self, name, request):        
		return JoinSub(name)

class JoinSub(Resource):
	isLeaf = True
	def __init__(self, name):
		Resource.__init__(self)
		self.name = name.decode('utf-8')
		
	def render_POST(self, request):
		user_id = request.getSession().uid.decode('utf-8')
		player_name = request.args[b'player_name'][0].decode('utf-8')
		if self.name in ongoing_games:
			print('game already in progress')
			res = {'result': RESULT_ERROR, 'message': 'game already in progress'}
		elif self.name in prep_area:
			players_list = prep_area[self.name]['players_list']
			if player_name in players_list.values():#duplicate name thrown before duplicate userid, maybe switcharound for clarity?
				print('player name already exists in this game')
				res = {'result': RESULT_ERROR, 'message': 'player name already exists in this game'}
			else:
				if user_id in players_list:
					print('player already in this game')
					res = {'result': RESULT_ERROR, 'message': 'player already in this game'}
				else:
					prep_area[self.name]['players_list'][user_id] = player_name
					print('joining game %s as %s(uid:%s)' % (self.name, player_name, user_id))
					res = {'result': RESULT_SUCCESS, 'name': self.name, 'dim_x':prep_area[self.name]['dim_x'], 'dim_y':prep_area[self.name]['dim_y'], 'prob':prep_area[self.name]['prob']}
		else:
			print('game does not exist')
			res = {'result': RESULT_ERROR, 'message': 'game does not exist'}
		
		return json.dumps(res).encode('utf-8')




class StartGame(Resource):
	def getChild(self, name, request):        
		return StartSub(name)          

class StartSub(Resource):
	isLeaf = True
	def __init__(self, name):
		Resource.__init__(self)
		self.name = name.decode('utf-8')
	def render_GET(self, request):
		user_id = request.getSession().uid.decode('utf-8')
		if self.name in prep_area:
			players_list = prep_area[self.name]['players_list']
			if user_id in players_list:
				if user_id not in prep_area[self.name]['ready']:
					prep_area[self.name]['ready'][user_id] = 1
				ready_list = prep_area[self.name]['ready']
				if len(ready_list) == 2:
					game_obj = game(self.name, prep_area[self.name])
					first = random.randint(0,1)
					players = list(ready_list)
					ongoing_games[self.name] = {'game_obj':game_obj, players[first]:P1_CONST,players[1-first]:P2_CONST, 'players_list':prep_area[self.name]['players_list']}
					prep_area.pop(self.name)
					print('starting game')
					res = {'result': RESULT_SUCCESS, 'name': self.name}
				else:
					print('missing players to start game')
					res = {'result': RESULT_ERROR, 'message': 'missing players to start game'}
			else:
				res = {'result': RESULT_ERROR, 'message': 'player is not in this game'}
				print('player is not in this game')
		elif self.name in ongoing_games:
			print('game already in progress')
			res = {'result': RESULT_ERROR, 'message': 'game already in progress'}
		else:
			print('game not found')
			res = {'result': RESULT_ERROR, 'message': 'game not found'}
		
		return json.dumps(res).encode('utf-8')
		
class GameStatus(Resource):
	def getChild(self, name, request):        
		return StatusSub(name)

class StatusSub(Resource):
	isLeaf = True
	def __init__(self, name):
		Resource.__init__(self)
		self.name = name.decode('utf-8')
		
	def render_GET(self, request):
		#will return representation of the current board state, who's turn is it, resources count, etc..
		if self.name in prep_area:
			res = {'result': RESULT_SUCCESS, 'name':self.name, 'state': 'prep_area', 'gameinfo':{i:v for i,v in prep_area[self.name].items() if i!='name'}}
			print(res)
		elif self.name in ongoing_games:
			
			#print(pnames)
			if b'verbose' in request.args:
				#send board state and everything as well..
				cg = ongoing_games[self.name]['game_obj']
				
				res = {'result': RESULT_SUCCESS, 'p1_gain':cg.p1_gain, 'p2_gain':cg.p2_gain, 'p1_resources':cg.p1_resources, 'p2_resources':cg.p2_resources, 'field':cg.field, 'turn':cg.current_turn}
			else:
				rev = {j:i for i, j in ongoing_games[self.name].items() if (j==P1_CONST or j==P2_CONST)}
				pnames = [ongoing_games[self.name]['players_list'][rev[P1_CONST]], ongoing_games[self.name]['players_list'][rev[P2_CONST]]]
				res = {'result': RESULT_SUCCESS, 'name':self.name, 'state': 'ongoing_game', 'player1':pnames[0], 'player2':pnames[1]}
				print(res)
		else:
			print('game not found')
			res = {'result': RESULT_ERROR, 'message': 'game not found'}
		
		return json.dumps(res).encode('utf-8')

class PlayGame(Resource):
	def getChild(self, name, request):        
		return PlaySub(name)

class PlaySub(Resource):
	isLeaf = True
	def __init__(self, name):
		Resource.__init__(self)
		self.name = name.decode('utf-8')
		
	def render_POST(self, request):
		#will be used to tell game server what play was made
		if self.name in ongoing_games:
		
			play_x = int(request.args[b'play_x'][0].decode('utf-8'))
			play_y = int(request.args[b'play_y'][0].decode('utf-8'))
			user_id = request.getSession().uid.decode('utf-8')
			cg = ongoing_games[self.name]['game_obj']
			ret = cg.cross_pick(play_x, play_y, ongoing_games[self.name][user_id])

			if ret:
				res = {'result': RESULT_SUCCESS, 'name': self.name, 'p1_gain':cg.p1_gain, 'p2_gain':cg.p2_gain, 'p1_resources':cg.p1_resources, 'p2_resources':cg.p2_resources, 'field':cg.field, 'turn':cg.current_turn}
				print(res)
			else:
				
				res = {'result': RESULT_ERROR, 'message': 'illegal move {} {} {}'.format(play_x, play_y, user_id)}
				print(res['message'])
		else:
			res = {'result': RESULT_ERROR, 'message': 'game with such name is not in progress'}
			print(res['message'])
		
		return json.dumps(res).encode('utf-8')

class LeaveGame(Resource):
	def getChild(self, name, request):
		return LeaveSub(name)

class LeaveSub(Resource):
	def __init__(self, name):
		Resource.__init__(self)
		self.name = name.decode('utf-8')
	
	def render_POST(self, request):
		user_id = request.getSession().uid.decode('utf-8')
		if self.name in prep_area:
			if user_id in prep_area[self.name]['players_list']:
				if user_id in prep_area[self.name]['ready']:
					prep_area[self.name]['ready'].pop(user_id)
					print('removed user from ready list')
				prep_area[self.name]['players_list'].pop(user_id)
				print('removed user from players list')
				res = {'result': RESULT_SUCCESS, 'name':self.name}
				
			else:
				res = {'result': RESULT_ERROR, 'message': 'player is not in this game'}
				print('player is not in this game')
		else:
			print('game not found in prep area')
			res = {'result': RESULT_ERROR, 'message': 'game not found in prep area'}

		return json.dumps(res).encode('utf-8')
		
		
root = Resource()
root.putChild(b'join', JoinGame()) #join existing open game
root.putChild(b'leave', LeaveGame()) #leave existing open game
root.putChild(b'create', CreateGame()) #create new game
root.putChild(b'start', StartGame()) #start game, use once both seats are taken
root.putChild(b'status', GameStatus()) #metrics endpoint
root.putChild(b'play', PlayGame()) #attempt to make a move
site = server.Site(root)
reactor.listenTCP(65422, site)
reactor.run()