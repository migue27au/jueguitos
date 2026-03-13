#!/usr/bin/python3 

import copy
from colors_cli import Clrs
from time import sleep, perf_counter
import keyboard, curses, threading, sys
from random import randint, choice, choices

_game_over = False
_stdscr = None
_pressed_keys = set()

STR_LOOSER = "GAME OVER. YOU LOOSE"

MAP_ROWS = 50
MAP_COLS = 50
MIN_ROWS = 1
MIN_COLS = 1

STR_FULL = "██"
STR_NONE = "  "

COLOR_BLACK = 1
COLOR_WHITE = 7
COLOR_GREEN = 2
COLOR_YELLOW = 3
COLOR_BLUE = 4
COLOR_MAGENTA = 5
COLOR_CYAN = 6
COLOR_RED = 8
COLOR_ORANGE = 9

SHIP_ORIENTATIONS = ["^",">", "v", "<"]
SHIP_COLOR = COLOR_GREEN

SHOOT_ORIENTATIONS = ["|","–"]
SHOOT_VERTICAL = 0
SHOOT_HORIZONTAL = 1
SHOOT_COLOR = COLOR_RED

ASTEROID_STR = "##"
ASTEROID_COLOR = COLOR_YELLOW
ASTEROID_DIRECTIONS = [
	"north",		# N
	"northeast",	# NE
	"east",			# E
	"southeast",	# SE
	"south",		# S
	"southwest",	# SW
	"west",			# W
	"northwest"		# NW
]

SHIP_SPEED_INCREASE = 0.05

DIFFICULTY = 1   # 1=easy, 2=normal, 3=hard
DIFFICULTY_TABLE = {
    1: {  # EASY
        "speed": ([0.05, 0.1, 0.2, 0.3], [2, 5, 3, 0]),
        "size":  ([2, 3, 4, 7], [4, 3, 2, 1]),
        "asteroid_rates": 1
    },
    2: {  # NORMAL
        "speed": ([0.05, 0.1, 0.2, 0.3], [1, 4, 4, 1]),
        "size":  ([2, 3, 4, 7], [4, 3, 2, 1]),
        "asteroid_rates": 0.5
    },
    3: {  # HARD
        "speed": ([0.05, 0.1, 0.2, 0.3], [0, 2, 6, 2]),
        "size":  ([2, 3, 4, 7], [4, 3, 2, 1]),
        "asteroid_rates": 0.2
    }
}

DELAY = 0.01


class Asteroid():
	direction = ""
	position = {"y":int(MAP_ROWS/2), "x":int(MAP_COLS/2)}
	size = 3
	speed = 0.5

	def __init__(self):
		self.direction = ""
		self.position = {"y":int(MAP_ROWS/2), "x":int(MAP_COLS/2)}
		self.size = 3
		self.speed = 1

		self.random()

	def random(self):
		border = choice(["up","right","down","left"])

		speed_values, speed_weights = DIFFICULTY_TABLE[DIFFICULTY]["speed"]
		size_values, size_weights = DIFFICULTY_TABLE[DIFFICULTY]["size"]

		self.speed = choices(speed_values, weights=speed_weights)[0]
		self.size = choices(size_values, weights=size_weights)[0]

		if border == "up":
			self.position['x'] = randint(int(MAP_COLS/6), int(MAP_COLS*5/6))
			self.position['y'] = MIN_ROWS
			self.direction = choice(["south", "southeast", "southwest"])

		elif border == "right":
			self.position['x'] = MAP_COLS - 1
			self.position['y'] = randint(int(MAP_ROWS/6), int(MAP_ROWS*5/6))
			self.direction = choice(["west", "northwest", "southwest"])

		elif border == "down":
			self.position['x'] = randint(int(MAP_COLS/6), int(MAP_COLS*5/6))
			self.position['y'] = MAP_ROWS - 1
			self.direction = choice(["north", "northeast", "northwest"])

		elif border == "left":
			self.position['x'] = MIN_COLS
			self.position['y'] = randint(int(MAP_ROWS/6), int(MAP_ROWS*5/6))
			self.direction = choice(["east", "northeast", "southeast"])

	def move(self):

		deltas = {
			"north":(-1*self.speed, 0),
			"northeast": (-1*self.speed, 1*self.speed),
			"east": (0, 1*self.speed),
			"southeast": (1*self.speed, 1*self.speed),
			"south":(1*self.speed, 0),
			"southwest": (1*self.speed, -1*self.speed),
			"west": (0, -1*self.speed),
			"northwest": (-1*self.speed, -1*self.speed)
		}

		dy, dx = deltas.get(self.direction, (0, 0))

		self.position["y"] += dy
		self.position["x"] += dx

		x = self.position["x"]
		y = self.position["y"]

		# comprobar si está completamente fuera del mapa
		if (
			x > MAP_COLS or
			x + self.size < 0 or
			y > MAP_ROWS or
			y + self.size < 0
		):
			return True   # eliminar asteroide

		return False

	def getDraw(self):
		return ASTEROID_STR

	def getColor(self):
		return ASTEROID_COLOR

	def checkCollision(self,x,y):
		if self.position['x'] <= x and self.position['x']+self.size >= x:
			if self.position['y'] <= y and self.position['y']+self.size >= y:
				return True
		return False

class Shoot():
	direction = ""
	position = {"y":int(MAP_ROWS/2), "x":int(MAP_COLS/2)}
	speed = 1

	def __init__(self, y, x, direction):
		self.direction = direction
		self.position = {"y":y, "x":x}

	def move(self):
		if self.direction == "left" and self.position["x"] > MIN_COLS:
			self.position["x"]-=self.speed
			return False
		elif self.direction == "right" and self.position["x"] < MAP_COLS:
			self.position["x"]+=self.speed
			return False
		elif self.direction == "up" and self.position["y"] > MIN_ROWS:
			self.position["y"]-=self.speed
			return False
		elif self.direction == "down" and self.position["y"] < MAP_ROWS:
			self.position["y"]+=self.speed
			return False
		else:
			return True

	def getDraw(self):
		if self.direction in ["left", "right"]:
			return SHOOT_ORIENTATIONS[SHOOT_HORIZONTAL]
		elif self.direction in ["up", "down"]:
			return SHOOT_ORIENTATIONS[SHOOT_VERTICAL]
	
	def getColor(self):
		return SHOOT_COLOR


class Ship():
	orientation = 0
	position = {"y":int(MAP_ROWS/2), "x":int(MAP_COLS/2)}
	speed = 0.05
	moving = {"y":0, "x":0}

	def __init__(self):
		speed = 0.05
		self.moving = ""
		self.orientation = 0
		self.position = {"y":int(MAP_ROWS/2), "x":int(MAP_COLS/2)}
		self.moving = {"y":0, "x":0}

	def thrust(self, direction):
		if direction == "left" and self.position["x"] > MIN_COLS:
			self.moving["x"] -= self.speed
		elif direction == "right" and self.position["x"] < MAP_COLS:
			self.moving["x"] += self.speed
		elif direction == "up" and self.position["y"] > MIN_ROWS:
			self.moving["y"] -= self.speed
		elif direction == "down" and self.position["y"] < MAP_ROWS:
			self.moving["y"] += self.speed
	
	def move(self):
		if self.position["x"] + self.moving["x"] < MIN_COLS:
			self.moving["x"] = 0
			self.position["x"] = MIN_COLS
		elif self.position["x"] + self.moving["x"] > MAP_COLS:
			self.moving["x"] = 0
			self.position["x"] = MAP_COLS
		else:
			self.position["x"] += self.moving["x"]

		if self.position["y"] + self.moving["y"] < MIN_ROWS:
			self.moving["y"] = 0
			self.position["y"] = MIN_ROWS
		elif self.position["y"] + self.moving["y"] > MAP_ROWS:
			self.moving["y"] = 0
			self.position["y"] = MAP_ROWS
		else:
			self.position["y"] += self.moving["y"]

	def rotate(self, direction):
		if direction == "left":
			if self.orientation > 0:
				self.orientation -= 1
			else:
				self.orientation = len(SHIP_ORIENTATIONS)-1
		elif direction == "right":
			self.orientation = (self.orientation + 1)%(len(SHIP_ORIENTATIONS))
	def getDraw(self):
		return SHIP_ORIENTATIONS[self.orientation]
	
	def getColor(self):
		return SHIP_COLOR


def custom_addstr(y,x,string,color):
	global _stdscr
	_stdscr.addstr(int(y),int(x*2), str(string), curses.color_pair(color))

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
			if game_map[r][c]["filled"] == 1:
				custom_addstr(1+r, 1+c, STR_FULL, game_map[r][c]["color"])
			else:
				custom_addstr(1+r, 1+c, STR_NONE, game_map[r][c]["color"])

def printShip(ship):
	custom_addstr(ship.position["y"], ship.position["x"], ship.getDraw(), ship.getColor())

def printShoot(shoot):
	if shoot.position["y"] > 0 and shoot.position["x"] > 0 and shoot.position["y"] < MAP_ROWS+1 and shoot.position["x"] < MAP_COLS+1:
		custom_addstr(shoot.position["y"], shoot.position["x"], shoot.getDraw(), shoot.getColor())

def printAsteroid(asteroid):
	for x in range(asteroid.size):
		for y in range(asteroid.size):
			if int(asteroid.position["y"]+y) > 0 and int(asteroid.position["y"]+y) < MAP_ROWS+1:
				if int(asteroid.position["x"]+x) > 0 and int(asteroid.position["x"]+x) < MAP_COLS+1:
					custom_addstr(int(asteroid.position["y"]+y), int(asteroid.position["x"]+x), asteroid.getDraw(), asteroid.getColor())


def main(stdscr):
	global _stdscr
	global _next_action
	global _game_over
	
	stdscr.nodelay(True)
	stdscr.keypad(True)

	_stdscr = stdscr

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
	
	game_map = [
		[{'filled':0,'color':COLOR_WHITE} for _ in range(MAP_COLS)]
		for _ in range(MAP_ROWS)
	]
	#custom_addstr(2, MAP_COLS+5, f"{str(game_map)}", COLOR_RED)
	
	start_time = perf_counter()
	last_spawn = start_time

	ship = Ship()
	shoots = []
	asteroids = []	
	
	points = 0


	while(_game_over == False):
		keys = []

		while True:
			key = stdscr.getch()
			if key == -1:
				break
			keys.append(key)

		for key in keys:
			if key == ord('w'):
				ship.thrust("up")
			elif key == ord('a'):
				ship.thrust("left")
			elif key == ord('s'):
				ship.thrust("down")
			elif key == ord('d'):
				ship.thrust("right")
			elif key in (27, ord('q')):
				_game_over = True
			elif key == curses.KEY_LEFT:
				ship.rotate("left")
			elif key == curses.KEY_RIGHT:
				ship.rotate("right")
			elif key == curses.KEY_UP or key == curses.KEY_DOWN:
				direction = ""
				if SHIP_ORIENTATIONS[ship.orientation] == "v":
					direction = "down"
				elif SHIP_ORIENTATIONS[ship.orientation] == "^":
					direction = "up"
				elif SHIP_ORIENTATIONS[ship.orientation] == "<":
					direction = "left"
				elif SHIP_ORIENTATIONS[ship.orientation] == ">":
					direction = "right"

				shoots.append(Shoot(ship.position['y'], ship.position['x'], direction))
			
		now = perf_counter()
		elapsed_ms = (now - start_time) * 1000

		ship.move()

		if now - last_spawn >= DIFFICULTY_TABLE[DIFFICULTY]['asteroid_rates']:
			last_spawn = now
			a = Asteroid()
			asteroids.append(a)

		stdscr.erase()
		printTable(game_map)
		
		for shoot in shoots:
			printShoot(shoot)
			if shoot.move():
				shoots.remove(shoot)
		
		printShip(ship)

		for asteroid in asteroids:
			printAsteroid(asteroid)
			custom_addstr(asteroids.index(asteroid)+10, MAP_COLS+5, f"Asteroid: {asteroid.position}", COLOR_YELLOW)
			if asteroid.move():
				asteroids.remove(asteroid)

			# Check if collision with asteroid
			for asteroid_aux in asteroids:
				if asteroid_aux != asteroid and asteroid.checkCollision(asteroid_aux.position['x'], asteroid_aux.position['y']):
					if asteroid_aux in asteroids and asteroid.size > asteroid_aux.size:
						asteroids.remove(asteroid_aux)
					elif asteroid in asteroids:
							asteroids.remove(asteroid)
				elif asteroid_aux != asteroid and asteroid.checkCollision(asteroid_aux.position['x']+asteroid_aux.size, asteroid_aux.position['y']+asteroid_aux.size):
					if asteroid_aux in asteroids and asteroid.size > asteroid_aux.size:
						asteroids.remove(asteroid_aux)
					elif asteroid in asteroids:
							asteroids.remove(asteroid)

			# Check if collision with shoot
			for shoot in shoots:
				if asteroid.checkCollision(shoot.position['x'], shoot.position['y']):
					if asteroid in asteroids:
						asteroids.remove(asteroid)
						points+=1

			# Check if collission with ship
			if asteroid.checkCollision(ship.position['x'], ship.position['y']):
				_game_over = True


		custom_addstr(5, MAP_COLS+5, f"Points: {points}", COLOR_YELLOW)
		custom_addstr(6, MAP_COLS+5, f"Ship: {ship.position['x']} {ship.position['y']} {SHIP_ORIENTATIONS[ship.orientation]}", COLOR_YELLOW)
		custom_addstr(7, MAP_COLS+5, f"Elapsed: {now}", COLOR_YELLOW)
		custom_addstr(8, MAP_COLS+5, f"Asteroids: {len(asteroids)}", COLOR_YELLOW)
		
		sleep(DELAY)
		_stdscr.refresh()
		_pressed_keys.clear()
	
	stdscr.erase()
	custom_addstr(1,1, f"{STR_LOOSER}\tPoints: {points}", COLOR_RED)
	_stdscr.refresh()
	sleep(4)

if __name__ == '__main__':
	curses.set_escdelay(25)
	curses.wrapper(main)
