import rpncalc
#import readline
import sys
import os
import math
import pkgutil
import settings

STACK = 0
GRAPH_XY = 1
GRAPH_X = 2

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

historyfile = open('history', 'r')
history = historyfile.readlines()

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
	input_string = str(input_string)
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
	else:
		interp.parse(input_string, True)

if settings.auto_import_functions:
	for dirpath, dirnames, filenames in os.walk(settings.auto_functions_directory):
		for filename in filenames:
			import_file(os.path.join(settings.auto_functions_directory, filename))

loop = True

interp.message("Welcone To The Basic RPN Calculator Interface")

while loop:
	try:
		print
		stack = interp.stack[-5:]
		start = len(stack)

		if start == 0:
			print 'Empty'

		for row in stack:
			print start, ') ', row
			start = start - 1

		if interp.messages:
			print interp.messages


		input_string = raw_input(">")
		if len(input_string) > 0:
			parse(input_string)
		

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
		for x in rpncalc.log:
			print(x)
		raise

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
