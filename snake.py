from colors_cli import Clrs
from time import sleep
import keyboard, curses, threading
from random import randint
import sys

#Tengo el next position para los casos en los que se cambia de dirección. Para no perder. Ej
# va a izq, y se pulsa der o (abj y der, rápido (antes de que pase el SLEEP)). Eso no movería la serpiente
_next_snake_dir = "up"
_snake_dir = "up"
_stdscr = None

def on_key_event():
	global _stdscr
	global _next_snake_dir
	while True:
		key = _stdscr.getch()
		if key == curses.KEY_UP:
			_next_snake_dir = "up"
		elif key == curses.KEY_DOWN:
			_next_snake_dir = "down"
		elif key == curses.KEY_LEFT:
			_next_snake_dir = "left"
		elif key == curses.KEY_RIGHT:
			_next_snake_dir = "right"
		elif key == "q":
			sys.exit(1)

MAP_ROWS = 10
MAP_COLS = 10

MAX_FOOD = 1
SLEEP = 0.25

STR_EMPTY = "  "
STR_FOOD = "🬇🬃"
STR_SNAKE = "🬇🬃"


STR_WINNER = "GAME OVER. YOU WIN"
STR_LOOSER = "GAME OVER. YOU LOOSE"

_map = []
_snake = []

COLOR_BLACK = 1
COLOR_GREEN = 2
COLOR_YELLOW = 3
COLOR_BLUE = 4
COLOR_MAGENTA = 5
COLOR_CYAN = 6
COLOR_WHITE = 7
COLOR_RED = 8
COLOR_ORANGE = 9

def printMap():

	global _map
	global _snake
	global _stdscr
	finished_map = [["" for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
	for seg in _snake:
		finished_map[seg["y"]][seg["x"]] = STR_SNAKE
	
	_stdscr.clear()
	_stdscr.addstr(0, 0, "██"*(MAP_COLS+2))
	_stdscr.addstr(1+MAP_ROWS, 0, "██"*(MAP_COLS+2))
	for i in range(len(_map)):
		_stdscr.addstr(i+1, 0, "██")
		_stdscr.addstr(i+1, 2+MAP_COLS*len(STR_EMPTY), "██")
	for i,row in enumerate(_map):
		for j,cell in enumerate(row):
			#print(i,j)
			if cell["food"] == True:
				_stdscr.addstr(i+1, 1+j*len(STR_FOOD), STR_FOOD, curses.color_pair(COLOR_YELLOW))
			else:
				if finished_map[i][j] == STR_SNAKE:
					_stdscr.addstr(i+1, 1+j*len(STR_SNAKE), STR_SNAKE, curses.color_pair(COLOR_GREEN))
				else:
					_stdscr.addstr(i+1, 1+j*len(STR_EMPTY), STR_EMPTY)
	_stdscr.refresh()


# FUNCION TERMINADA
def moveSnake():
	global _next_snake_dir
	global _snake_dir
	global _snake
	# Guardo la posición de la cabeza para poder moverla después
	_head = {"x":_snake[0]["x"], "y":_snake[0]["y"]}
	
	#Muevo la cola de la serpiente. La nueva posición se correspondería con la posición del segmento de serpiente anterior
	for i in range(len(_snake)-1,0,-1):
		_snake[i]["x"] = (_snake[i-1]["x"])%MAP_COLS
		_snake[i]["y"] = (_snake[i-1]["y"])%MAP_ROWS

	#Movimiendo la cabeza en la nueva dirección
	if _snake_dir == "up" and _next_snake_dir != "down":
		_snake_dir = _next_snake_dir
	elif _snake_dir == "down" and _next_snake_dir != "up":
		_snake_dir = _next_snake_dir
	elif _snake_dir == "left" and _next_snake_dir != "right":
		_snake_dir = _next_snake_dir
	elif _snake_dir == "right" and _next_snake_dir != "left":
		_snake_dir = _next_snake_dir

	if _snake_dir == "up":
		_snake[0]["y"] = (_head["y"]-1)%MAP_ROWS
	elif  _snake_dir == "down":
		_snake[0]["y"] = (_head["y"]+1)%MAP_ROWS
	elif _snake_dir == "left":
		_snake[0]["x"] = (_head["x"]-1)%MAP_COLS
	elif _snake_dir == "right":
		_snake[0]["x"] = (_head["x"]+1)%MAP_COLS

	# Comprobración de que la cabeza no se ha comido ninguna parte de la serpiente
	for seg in _snake[1:]:
		if seg["x"] == _snake[0]["x"] and seg["y"] == _snake[0]["y"]:
			return False

	return True

# return 0, si la comida no está en la serpiente
# return 1, si la comida está en la cabeza de la serpiente (se la ha comido)
# return 2, si la comida está en el cuerpo de la serpiente (util cuando se ubica una nueva comida)
def checkIfFoodInSnake(food_poss):
	global _snake
	for food_pos in food_poss:
		if food_pos["x"] == _snake[0]["x"] and food_pos["y"] == _snake[0]["y"]:
			return 1
		for seg in _snake[1:]:
			if food_pos["x"] == seg["x"] and food_pos["y"] == seg["y"]:
				return 2
	return 0

def checkIfFoodPreviouslyPlace(food_pos, food_poss):
	for food in food_poss:
		if food_pos["x"] == food["x"] and food_pos["y"] == food["y"]:
			return True
	return False

def newFood():
	global _map
	global _snake
	food_poss = []
	for i, row in enumerate(_map):
		for j, cell in enumerate(row):
			if cell["food"] ==  True:
				food_poss.append({"x":j,"y":i})

	#Compruebo si la serpiente ha comido una comida
	for f, food_pos in enumerate(food_poss):
		#print(checkIfFoodInSnake([food_pos], _snake))
		if checkIfFoodInSnake([food_pos]) == 1:
			# elimino la comida
			_map[food_pos["y"]][food_pos["x"]]["food"] = False
			food_poss.pop(f)
			#añado uno a la serpiente
			_snake.append({"x":_snake[-1]["x"],"y":_snake[-1]["y"]})
			break

	#Pongo la comida si hace falta
	while len(food_poss) < MAX_FOOD:
		#nueva posicion de la comida
		food_pos = {"x":randint(0,MAP_COLS-1), "y":randint(0,MAP_ROWS-1)}
		#si la comida la he puesto donde está la serpiente o si la he puesto donde ya había comida vuelvo a intentarlo
		while checkIfFoodInSnake(food_poss+[food_pos]) != 0 or checkIfFoodPreviouslyPlace(food_pos, food_poss):
			food_pos = {"x":randint(0,MAP_COLS-1), "y":randint(0,MAP_ROWS-1)}

		food_poss.append(food_pos)
		_map[food_pos["y"]][food_pos["x"]]["food"] = True

def main(stdscr):
	global _snake_dir
	global _map
	global _snake
	global _stdscr
	_stdscr = stdscr

	curses.curs_set(0)
	# Configurar colores
	curses.start_color()
	curses.init_pair(COLOR_BLACK, curses.COLOR_BLACK, curses.COLOR_WHITE)
	curses.init_pair(COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
	curses.init_pair(COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
	curses.init_pair(COLOR_MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
	curses.init_pair(COLOR_CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
	curses.init_pair(COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
	curses.init_pair(COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(COLOR_ORANGE, 208, curses.COLOR_BLACK)

	_map = [[{"food":False} for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
	#_snake = [{"x":int(MAP_COLS/2), "y":int(MAP_ROWS/2)},{"x":int(MAP_COLS/2), "y":int(MAP_ROWS/2)+1},{"x":int(MAP_COLS/2), "y":int(MAP_ROWS/2)+2}, {"x":int(MAP_COLS/2), "y":int(MAP_ROWS/2)+2},{"x":int(MAP_COLS/2), "y":int(MAP_ROWS/2)+2}]
	_snake = [{"x":int(MAP_COLS/2), "y":int(MAP_ROWS/2)},{"x":int(MAP_COLS/2), "y":int(MAP_ROWS/2)+1}]

	stat_thread = threading.Thread(target=on_key_event)
	stat_thread.start()

	while True:
		newFood()
		#Imprimo el mapa
		printMap()
		#Espero el tiempo para actualizar
		sleep(SLEEP)

		#Despues de esperar muevo la serpiente y compruebo que no me haya comido a mi mismo
		if moveSnake() == False:
			break
	_stdscr.clear()
	if len(_snake) == MAP_COLS*MAP_ROWS:
		print()
		_stdscr.addstr(0, 0, STR_WINNER, curses.color_pair(COLOR_BLUE))
	else:
		_stdscr.addstr(0, 0, STR_LOOSER, curses.color_pair(COLOR_RED))
	_stdscr.refresh()

	sleep(2)

if __name__ == '__main__':
	curses.set_escdelay(25)
	curses.wrapper(main)