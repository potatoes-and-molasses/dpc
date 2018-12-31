import requests
import json
import time
import sys
import argparse

gamename = sys.argv[1]
dim_x, dim_y, prob = 30, 30, 0.3
player1_name = 'test1'
player2_name = 'test2'
address = 'http://127.0.0.1:65422/'

jarjar = {} #for session id

def send_create(game_name, player_name, players_count):
    r = requests.post(address+'create/'+game_name, data={'player_name':player_name,'dim_x':dim_x, 'dim_y':dim_y, 'prob':prob}, cookies=jarjar)
    return r

def send_join(game_name, player_name):
    r = requests.post(address+'join/'+game_name, data={'player_name':player_name}, cookies=jarjar)
    return r

def send_start(game_name):
    r = requests.get(address+'start/'+game_name, cookies=jarjar)
    return r

def send_status(game_name):
    r = requests.get(address+'status/'+game_name, cookies=jarjar)
    return r

def send_play(game_name, play_x, play_y):
	r = requests.post(address+'play/'+game_name, cookies=jarjar, data={'play_x':play_x, 'play_y':play_y})
	return r
r = send_create(gamename, player1_name, 0)
jarjar = r.cookies
time.sleep(1)
r = send_start(gamename)

time.sleep(1)
jarjar={}
r = send_join(gamename, player2_name)
time.sleep(1)
jarjar = r.cookies
r = send_start(gamename)
time.sleep(1)
r = send_play(gamename, 4, 4)
