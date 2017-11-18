import rpncalc
#import readline
import curses
import sys
import os
import math
import pkgutil
import settings

STACK = 0
GRAPH_XY = 1
GRAPH_X = 2

mode = STACK

screen = curses.initscr()
screen.keypad(1)
YMAX, XMAX = screen.getmaxyx()
curses.noecho()

stackbox = curses.newwin(YMAX-4,XMAX -1,0,0)
inputbox = curses.newwin(3,XMAX -1,YMAX-5,0)
msgbox   = curses.newwin(3,XMAX -1,YMAX-3,0)
numbox = curses.newwin(YMAX-4, 4, 0, 0)
inputbox.keypad(1)

loaded_plugins = {}
#load the plugins
def load_all_modules_from_dir(dirname):
	for importer, package_name, _ in pkgutil.iter_modules([dirname]):
		full_package_name = '%s.%s' % (dirname, package_name)
		if full_package_name not in sys.modules:
			module = importer.find_module(package_name).load_module(full_package_name)
			yield module


for module in load_all_modules_from_dir('plugins'):
	loaded_plugins.update(module.register())

function_list = rpncalc.ops.copy()
function_list.update(loaded_plugins)

if settings.allow_inline_breaks:
	interp = rpncalc.Interpreter(function_list, rpncalc.inline_break)
else:
	interp = rpncalc.Interpreter(function_list, {})


class ShutErDownBoys(Exception):
	pass

class BadPythonCommand(Exception):
	pass


input_string_pre  = ''
input_string_post = ''
history = []
history_position = 0

historyfile = open('history', 'w+')
history = historyfile.readlines()

inputbox.box()
stackbox.box()
msgbox.box()
inputbox.overlay(screen)
stackbox.overlay(screen)
msgbox.overlay(screen)
screen.refresh()

def editor_validator(keystroke):
	#raise Exception('ERRORRRRR: ' + str(keystroke))
	message = str(keystroke)
	tbox.do_command(keystroke)

def import_file(filename):
	f = open(filename)
	commands = f.read()
	f.close()
	for command in commands.split('\n'):
		if len(command) > 0:
			if command[0] == "#":
				continue
			parse(command)

def parse(input_string):
	global mode
	if input_string[0] == ':': # interface commands start with a colon
		input_string = input_string[1:]
		text = input_string.split()
		if text[0] == 'import':
			import_file(os.path.join(settings.functions_directory, text[1]))

		elif text[0] == 'export':
			f = open(os.path.join(settings.functions_directory, text[1]), 'w+')
			commands = interp.stack[-1].stack
			for cmd in commands:
				f.write(cmd)
				f.write('\n')
			f.close()
		elif text[0] == 'quit':
			raise ShutErDownBoys()
		elif text[0] == 'step':
			interp.step()
		elif text[0] == 'run':
			interp.resume()
		elif text[0] == '!':
			try:
				command = ''
				for character in input_string[1:]:
					if character == '?':
						command += str(interp.pop()[0].val)
					else:
						command += character
						
				res = eval(command)
				interp.parse(str(res))
			except Exception as e:
				raise BadPythonCommand('Bad Python Command (' + command + ') ' + e.message)
		elif text[0] == 'graph':
			if len(text) > 1:
				if text[1] == 'x':
					mode = GRAPH_X
					interp.message("X Graph Mode")
				elif text[1] == 'xy':
					mode = GRAPH_XY
					interp.message("XY Graph Mode")
			elif mode == GRAPH_XY:
				mode = GRAPH_X
				interp.message("X Graph Mode")
			else:
				mode = GRAPH_XY
				interp.message("XY Graph Mode")
		elif text[0] == 'stack':
			interp.message("Stack Mode")
			mode = STACK

	else:
		interp.parse(input_string, True)

if settings.auto_import_functions:
	for dirpath, dirnames, filenames in os.walk(settings.auto_functions_directory):
		for filename in filenames:
			import_file(os.path.join(settings.auto_functions_directory, filename))


def setupnumbox():
	numbox.clear()
	numbox.box()
	for y in range(1, YMAX - 5):
		numbox.addstr(numbox.getmaxyx()[0] - y - 1, 1, str(y - 1))
setupnumbox()
loop = True

screen.clear()
inputbox.overlay(screen)
stackbox.overlay(screen)
msgbox.overlay(screen)
numbox.overlay(screen)
screen.refresh()

while loop:
	try:
		screen.clear()
		inputbox.clear()
		inputbox.box()

		stackbox.erase()
		stackbox.box()

		msgbox.clear()
		msgbox.box()

		inputbox.addstr(1, 2, input_string_pre)
		inputbox.addstr(1, 2 + len(input_string_pre), input_string_post)

		event = inputbox.getch(1, 2 + len(input_string_pre))

		if event == 13:
			event = curses.KEY_ENTER
		if event == 10:
			event = curses.KEY_ENTER
		elif event == 8:
			event = curses.KEY_BACKSPACE
		elif event == 127:
			event = curses.KEY_DC

		if event <= 255:
			if event > 0:
				input_string_pre += chr(event)
		else:
			if event == curses.KEY_BACKSPACE:
				if len(input_string_pre) > 0:
					input_string_pre = input_string_pre[:-1]
			elif event == curses.KEY_DC:
				if len(input_string_post) > 0:
					input_string_post = input_string_post[1:]
			elif event == curses.KEY_LEFT:
				if len(input_string_pre) > 0:
					input_string_post = input_string_pre[-1] + input_string_post
					input_string_pre = input_string_pre[:-1]
			elif event == curses.KEY_RIGHT:
				if len(input_string_post) > 0:
					input_string_pre = input_string_pre + input_string_post[0]
					input_string_post = input_string_post[1:]
			elif event == curses.KEY_UP:
				if history_position < len(history):
					history_position += 1
					input_string_post = ''
					input_string_pre = history[-history_position]
			elif event == curses.KEY_DOWN:
				if history_position > 1:
					history_position -= 1
					input_string_post = ''
					input_string_pre = history[-history_position]
				if history_position == 1:
					input_string_post = ''
					input_string_pre = ''
			elif event == curses.KEY_ENTER:
				input_string = input_string_pre + input_string_post
				if input_string != '':
					history.append(input_string)
					history_position = 0
					input_string_post = ''
					input_string_pre = ''
					parse(input_string)
			elif event == 262: #home key
				input_string_post = input_string_pre + input_string_post
				input_string_pre = ''
			elif event == 360: #end key
				input_string_pre = input_string_pre + input_string_post
				input_string_post = ''
			elif event == curses.KEY_RESIZE:
				if curses.is_term_resized(YMAX, XMAX):
					YMAX, XMAX = screen.getmaxyx()
					interp.message("Screen Resized to " + str(YMAX) + ", " + str(XMAX))
					screen.clear
					curses.resizeterm(YMAX, XMAX)
					screen.resize(YMAX, XMAX)
					stackbox.resize(YMAX-4,XMAX -1)
					inputbox.resize(3,XMAX -1)
					msgbox.resize(3,XMAX -1)
					numbox.resize(YMAX-4, 4)

					stackbox.mvwin(0,0)
					inputbox.mvwin(YMAX-5,0)
					msgbox.mvwin(YMAX-3,0)
					numbox.mvwin( 0, 0)

					setupnumbox()
			else:
				interp.message(str(event))

		if mode == STACK:
			stack = interp.stack[:]
			if interp.function_stack is not None:
				stack += ['['] + interp.function_stack 
			max_stack = min(len(stack), YMAX-5)
			if max_stack >= 0:
				for row in range(1,max_stack + 1):
					stackbox.addstr(YMAX- 5 - row, 5, str(stack[-row]))
		elif mode == GRAPH_XY:
			stackbox.clear()
			stack = interp.stack[:]
			xs = [x.val for x in stack[::2] if type(x) is not rpncalc.Function]
			ys = [y.val for y in stack[1::2] if type(y) is not rpncalc.Function]
			maxlength = min(len(xs), len(ys))
			if maxlength <= 1:
				mode = STACK
				continue
			x0 = min(xs)
			xmax = max(xs)
			dx = xmax - x0
			y0 = min(ys)
			ymax = max(ys)
			dy = ymax - y0


			frame_ymax, frame_xmax = stackbox.getmaxyx()
			frame_ymax -= 3
			frame_xmax -= 3
			frame_x0 = 3
			frame_dx = frame_xmax - frame_x0
			frame_y0 = 1
			frame_dy = frame_ymax - frame_y0

			lastx = xs[0]
			lasty = ys[0]

			for index in range(maxlength):
				xpos = int(frame_x0 + frame_dx * (xs[index] - x0)/dx + 1)
				ypos = int(frame_y0 + frame_dy * (ymax - ys[index])/dy + 1)
				deltax = xs[index] - lastx
				deltay = ys[index] - lasty
				
				if deltax == 0:
					symbol = '|'
				else:
					slope = float(deltay) / float(deltax)
					if slope > 0:
						symbol = '/'
					elif slope == 0:
						symbol = '-'
					else:
						symbol = '\\'
				lastx = xs[index]
				lasty = ys[index]

				stackbox.addstr(ypos, xpos, symbol)

		elif mode == GRAPH_X:
			stackbox.clear()
			stack = interp.stack[:]
			xs = [x.val for x in interp.stack if type(x) is not rpncalc.Function]
			x0 = min(xs)
			xmax = max(xs)
			dx = xmax - x0

			frame_ymax, frame_xmax = stackbox.getmaxyx()
			frame_ymax -= 3
			frame_xmax -= 3
			frame_x0 = 4
			frame_dx = frame_xmax - frame_x0
			frame_y0 = 1
			frame_dy = frame_ymax - frame_y0

			maxlength = min(len(xs), frame_xmax - frame_x0)

			if maxlength <= 1:
				mode = STACK
				continue


			for index in range(maxlength):
				xpos = index + frame_x0
				ypos = int(frame_y0 + frame_dy * (xmax - xs[index])/dx + 1)
				stackbox.addstr(ypos, xpos, 'X')

		if interp.messages:
			message_string = '| '.join(interp.messages)
			msgbox.addstr(1, 5, message_string[:(XMAX - 8)])


		screen.clear()
		inputbox.overlay(screen)
		stackbox.overlay(screen)
		msgbox.overlay(screen)
		numbox.overlay(screen)
		screen.refresh()




	except ShutErDownBoys:
		loop = False
	except KeyboardInterrupt:
		input_string = input_string_pre + input_string_post
		if input_string:
			input_string_post = ''
			input_string_pre = ''
		else:
			loop = False
	except BadPythonCommand as e:
		interp.message(e.message)
	except:
		curses.endwin()
		for x in rpncalc.log:
			print(x)
		raise

curses.endwin()
for v in interp.stack:
	print(v)

for x in rpncalc.log:
	print(x)

if settings.history > 0:
	historyfile = open('history', 'w')
	history_to_log = history
	if len(history) > settings.history:
		history_to_log = history[-settings.history:]
	for historyitem in history_to_log:
		historyfile.write(('%s\n' % historyitem.strip()))
	historyfile.close()

sys.exit(0)
