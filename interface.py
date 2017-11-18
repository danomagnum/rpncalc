import rpncalc
import sys
import os
import math
import pkgutil
import settings

STACK = 0
GRAPH_XY = 1
GRAPH_X = 2

def load_all_modules_from_dir(dirname):
	for importer, package_name, _ in pkgutil.iter_modules([dirname]):
		full_package_name = '%s.%s' % (dirname, package_name)
		if full_package_name not in sys.modules:
			module = importer.find_module(package_name).load_module(full_package_name)
			yield module

class ShutErDownBoys(Exception):
	pass

class BadPythonCommand(Exception):
	pass

class Interface(object):
	def __init__(self):
		self.history = []
		self.history_position = 0

		historyfile = open('history', 'r')
		self.history = historyfile.readlines()

		self.mode = STACK


		loaded_plugins = {}
		for module in load_all_modules_from_dir('plugins'):
			loaded_plugins.update(module.register())

		function_list = rpncalc.ops.copy()
		function_list.update(loaded_plugins)

def parse(input_string):
	global mode
	if input_string[0] == ':': # interface commands start with a colon
		input_string = input_string[1:]
		text = input_string.split()
		if text[0] == 'step':
			interp.step()
		elif text[0] == 'run':
			interp.resume()
		elif text[0] == 'import':
			import_file(os.path.join(functions_directory, text[1]))

	def import_file(self, filename):
		f = open(filename)
		commands = f.read()
		f.close()
		for command in commands.split('\n'):
			if len(command) > 0:
				if command[0] == "#":
					continue
				self.parse(command, False)

	def parse(self, input_string, add_to_history=True):
		if input_string == '':
			return
		else:
			if add_to_history:
				self.history.append(input_string)
				self.history_position = 0
		if input_string[0] == ':': # interface commands start with a colon
			input_string = input_string[1:]
			text = input_string.split()
			if text[0] == 'import':
				import_file(os.path.join(functions_directory, text[1]))

				stackbox.mvwin(0,0)
				inputbox.mvwin(YMAX-5,0)
				msgbox.mvwin(YMAX-3,0)
				numbox.mvwin( 0, 0)

				setupnumbox()
			else:
				interp.message(str(event))

		if mode == STACK:
			stack = interp.get_stack()
			if interp.function_stack is not None:
				stack += ['['] + interp.function_stack 
			if interp.paused:
				stack += ['@'] + interp.get_broken_commands()
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
				return
				#continue
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
					self.mode = GRAPH_XY
					self.interp.message("XY Graph Mode")
		elif text[0] == 'stack':
			self.interp.message("Stack Mode")
			self.mode = STACK

		else:
			self.interp.parse(input_string, True)

	def auto_import_functions(self):
		if settings.auto_import_functions:
			for dirpath, dirnames, filenames in os.walk(settings.auto_functions_directory):
				for filename in filenames:
					self.import_file(os.path.join(settings.auto_functions_directory, filename))

	def history_back(self):
		if self.history_position < len(self.history):
			self.history_position += 1
			return(self.history[-self.history_position])

	def history_forward(self):
		if self.history_position > 1:
			self.history_position -= 1
			return(self.history[-self.history_position])
		elif self.history_position == 1:
			return('')

	def print_stack(self):
		for v in self.interp.stack:
			print(v)

	def save_history(self):
		if settings.history > 0:
			historyfile = open('history', 'w')
			history_to_log = self.history
			if len(self.history) > settings.history:
				history_to_log = self.history[-settings.history:]
			for historyitem in history_to_log:
				historyfile.write(('%s\n' % historyitem.strip()))
			historyfile.close()

