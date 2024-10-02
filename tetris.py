#!/usr/bin/python3 

import copy
from colors_cli import Clrs
from time import sleep
import keyboard, curses, threading, sys
from random import randint, choice

_game_over = False
_stdscr = None
_next_move = ""

STR_LOOSER = "GAME OVER. YOU LOOSE"

MAP_ROWS = 20
MAP_COLS = 10

STR_FULL = "██"
STR_NONE = "  "
STR_BLCK = "##"

COLOR_BLACK = 1
COLOR_WHITE = 7
COLOR_GREEN = 2
COLOR_YELLOW = 3
COLOR_BLUE = 4
COLOR_MAGENTA = 5
COLOR_CYAN = 6
COLOR_RED = 8
COLOR_ORANGE = 9

def on_key_event():
	global _stdscr
	global _next_move
	global _game_over
	while _game_over == False:
		key = _stdscr.getch()
		if key == curses.KEY_UP:
			_next_move = "rotate"
		elif key == curses.KEY_DOWN:
			_next_move = "down"
		elif key == curses.KEY_LEFT:
			_next_move = "left"
		elif key == curses.KEY_RIGHT:
			_next_move = "right"
		elif key in (27, 'q'):
			_game_over = True

BLOCK_ARRAY_STICK = ([[1],
					  [1],
					  [1],
					  [1]], COLOR_CYAN)
BLOCK_ARRAY_CUBE = 	([[1,1],
					  [1,1]], COLOR_YELLOW)
BLOCK_ARRAY_L1 =	([[1,0],
					  [1,0],
					  [1,1]], COLOR_ORANGE)
BLOCK_ARRAY_L2 =	([[0,1],
					  [0,1],
					  [1,1]], COLOR_BLUE)
BLOCK_ARRAY_Z1 = 	([[1,1,0],
				 	  [0,1,1]], COLOR_RED)
BLOCK_ARRAY_Z2 = 	([[0,1,1],
				 	  [1,1,0]], COLOR_GREEN)
BLOCK_ARRAY_T = 	([[0,1,0],
				 	  [1,1,1]], COLOR_MAGENTA) 

blocks = (BLOCK_ARRAY_STICK, BLOCK_ARRAY_CUBE, BLOCK_ARRAY_L1, BLOCK_ARRAY_L2, BLOCK_ARRAY_Z1, BLOCK_ARRAY_Z2, BLOCK_ARRAY_T)

class Block():
	color = ""
	array = []
	position = {"y":-3,"x":int(MAP_COLS/2)}
	
	def __init__(self, array = [], color = ""):
		self.array = array
		self.color = color
		self.position = {"y":-3,"x":int(MAP_COLS/2)-1}

	def rotate(self, game_map):
		array_rotated = [[0] * len(self.array) for _ in range(len(self.array[0]))]

		for y in range(len(self.array)):
			for x in range(len(self.array[0])):
				array_rotated[x][len(self.array)-y-1] = self.array[y][x]
		if len(array_rotated)+self.position["y"] >= MAP_ROWS:
			return
		if len(array_rotated[0])+self.position["x"] >= MAP_COLS:
			return
		self.array = array_rotated

	def left(self, game_map):
		for y in range(len(self.array)):
			for x in range(len(self.array[0])):
				if self.array[y][x] == 1:
					if self.position["x"]+x-1 > 0 and self.position["y"]+y > 0:
						if game_map[self.position["y"]+y][self.position["x"]+x-1]["f"] == 1:
							return
		if self.position["x"] > 0:
			self.position["x"]-=1

	def right(self, game_map):
		for y in range(len(self.array)):
			for x in range(len(self.array[0])):
				if self.array[y][x] == 1:
					if self.position["x"]+x+1 < MAP_COLS and self.position["y"]+y > 0:
						if game_map[self.position["y"]+y][self.position["x"]+x+1]["f"] == 1:
							return

		if self.position["x"] + len(self.array[0]) < MAP_COLS:
			self.position["x"]+=1

	def down(self, game_map):
		while self.gravity(game_map) == 0:
			pass

	def gravity(self, game_map):
		#si he llegado al suelo devuelves un 1
		if self.position["y"]+len(self.array) >= MAP_ROWS:
			return 1

		#devuelves 2 si el bloque inferior al que está mi bloque está ocupado en el game_map
		for y in range(len(self.array)):
			for x in range(len(self.array[0])):
				if self.array[y][x] == 1:
					if self.position["y"]+y > 0 and self.position["x"]+x >= 0:
						if game_map[self.position["y"]+y+1][self.position["x"]+x]["f"] == 1:
							if self.position["y"]+y <= 0:
								return -1
							else:
								return 2

		#si bajo una unidad devuelves un 0
		self.position["y"] += 1
		return 0
	
	def new(self):
		random_block = choice(blocks)
		self.array = copy.copy(random_block[0])
		self.color = copy.copy(random_block[1])
		self.position = {"y":-3,"x":int(MAP_COLS/2)-1}

def custom_addstr(y,x,string,color):
	global _stdscr
	_stdscr.addstr(y,x*2, str(string), curses.color_pair(color))

def custom_refresh():
	global _stdscr
	_stdscr.refresh()

#Imprime el area de juego
def printTable(game_map):
	#barra horizontal superior
	custom_addstr(0, 0, STR_FULL*(MAP_COLS+2), COLOR_WHITE)
	#barra horizontal inferior
	custom_addstr(MAP_ROWS+1, 0, STR_FULL*(MAP_COLS+2), COLOR_WHITE)
	for r in range(MAP_ROWS):
		#barra vertical izquierda
		custom_addstr(1+r, 0, STR_FULL, COLOR_WHITE)
		#barra vertical derecha
		custom_addstr(1+r, 1+MAP_COLS, STR_FULL, COLOR_WHITE)

		#relleno del centro con el game_map
		for c in range(MAP_COLS):
			if game_map[r][c]["f"] == 1:
				custom_addstr(1+r, 1+c, STR_FULL, game_map[r][c]["c"])
			else:
				custom_addstr(1+r, 1+c, STR_NONE, game_map[r][c]["c"])
	custom_addstr(2, 1, "--"*(MAP_COLS), COLOR_WHITE)

def printBlock(block):
	for y in range(len(block.array)):
		for x in range(len(block.array[0])):
			if block.array[y][x] == 1 and block.position["y"]+y >= 0:
				custom_addstr(1+block.position["y"]+y, 1+block.position["x"]+x, STR_BLCK, block.color)

def main(stdscr):
	global _stdscr
	global _next_move
	global _game_over
	
	_stdscr = stdscr
	threading.Thread(target=on_key_event).start()

	curses.curs_set(0)
	# Configurar colores
	curses.start_color()
	curses.init_pair(COLOR_BLACK, curses.COLOR_BLACK, curses.COLOR_BLACK)
	curses.init_pair(COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
	curses.init_pair(COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
	curses.init_pair(COLOR_MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
	curses.init_pair(COLOR_CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
	curses.init_pair(COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
	curses.init_pair(COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(COLOR_ORANGE, 208, curses.COLOR_BLACK)
	
	block = Block()
	game_map = [[{'f':0,'c':COLOR_WHITE}]*MAP_COLS for _ in range(MAP_ROWS)]
	#custom_addstr(2, MAP_COLS+5, f"{str(game_map)}", COLOR_RED)
	
	block.new()
	points = 0
	while(_game_over == False):
		if _next_move != "":
			if _next_move == "rotate":
				block.rotate(game_map)
			elif _next_move == "left":
				block.left(game_map)
			elif _next_move == "right":
				block.right(game_map)
			elif _next_move == "down":
				block.down(game_map)
			_next_move = ""

		# Comprueba filas completas
		for y in range(MAP_ROWS):
			cols_filled_counter = 0
			for x in range(MAP_COLS):
				if game_map[y][x]["f"] == 1:
					cols_filled_counter+=1
			if cols_filled_counter >= MAP_COLS:
				#Si toda la fila está completa elimina la fila (todas las superiores una unidad abajo)
				points += 1
				for row in range(y-1,-1,-1):
					game_map[row+1] = game_map[row]

		stdscr.clear()
		printTable(game_map)
		printBlock(block)		

		gravity = block.gravity(game_map)
		custom_addstr(0, MAP_COLS+5, f"Gravity: {gravity}", COLOR_RED)
		custom_addstr(1, MAP_COLS+5, f"Block position: {block.position['y']}, {block.position['x']}", COLOR_RED)
		custom_addstr(2, MAP_COLS+5, f"Block size: {len(block.array)}, {len(block.array[0])}", COLOR_RED)

		custom_addstr(5, MAP_COLS+5, f"Points: {points}", COLOR_YELLOW)
		#Si ha llegado al suelo o sobre otro bloque saco un bloque nuevo y actualizo el game_map
		if gravity >= 1:
			for y in range(len(block.array)):
				for x in range(len(block.array[0])):
					if block.array[y][x] == 1:
						game_map[block.position["y"]+y][block.position["x"]+x] = {'f':1,'c':block.color}
			if gravity == 2:
				if block.position["y"] <= 0:
					break
			block.new()
		elif gravity == -1:
			break
		
		_stdscr.refresh()
		sleep(0.5)
	
	custom_addstr(1,1, f"{STR_LOOSER}", COLOR_RED)
	_stdscr.refresh()
	sleep(4)

if __name__ == '__main__':
	curses.set_escdelay(25)
	curses.wrapper(main)
