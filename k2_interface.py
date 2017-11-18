
import kivy
kivy.require('1.2.0')
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.properties import ObjectProperty, NumericProperty, ListProperty
from kivy.factory import Factory
from kivy.config import ConfigParser
from kivy.uix.settings import Settings

import rpncalc
import settings

interp = rpncalc.Interpreter(rpncalc.ops, {})

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

		elif text[0] == 'export':
			f = open(os.path.join(settings.functions_directory, text[1]), 'w+')
			commands = interp.stack[-1].stack
			for cmd in commands:
				f.write(cmd)
				f.write('\n')
			f.close()
		elif text[0] == 'quit':
			raise ShutErDownBoys()
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

class Calculator(Widget):
	entryline = ObjectProperty(None)
	lastOp = ""
	memorynum = ''
	operation = False
	stackdisplay = []

	def _execute(self, op):
		if op in '1234567890.':
			self.memorynum += op
			self.entryline.value.text = self.memorynum
			return
		else:
			if self.memorynum:
				parse(self.memorynum)
				self.memorynum = ''

		if op not in ['enter', 'step', 'resume']:
			parse(op)
		else:
			if op == 'step':
				interp.step()
			elif op == 'resume':
				interp.run()
		self.entryline.value.text = self.memorynum

		stack_size = len(interp.stack)
		for x in xrange(len(self.stackdisplay)):
			if x < stack_size:
				self.stackdisplay[x].value.text = str(interp.stack[-(x + 1)])
			else:
				self.stackdisplay[x].value.text = ''


	def _setText(self, op):
		if op == "." and "." in self.entryline.value.text:
			return
		if self.operation:
			self.entryline.value.text = op
			self.operation = False
		else:
			self.entryline.value.text += op

	def setup_stack_display(self, count):
		pass
		

class CalcApp(App):
	use_kivy_settings = False
	def build(self):
		self.Calc = Calculator()
		self.Calc.stackdisplay.append(self.Calc.stackline0)
		self.Calc.stackdisplay.append(self.Calc.stackline1)
		self.Calc.stackdisplay.append(self.Calc.stackline2)
		self.Calc.stackdisplay.append(self.Calc.stackline3)

		for x in range(len(self.Calc.stackdisplay)):
			self.Calc.stackdisplay[x].number.text = str(x)

		return self.Calc

	def build_config(self, config):
		config.setdefaults('Calculator Colors', \
			{
			'CC' : 'Off',
			'NB' : 'default',
			'NBT': 'default',
			'OB' : 'default',
			'OBT' : 'default',
			'SB' : 'default',
			'SBT' : 'default',
			'TIB' : 'default',
			'TIF' : 'default'
			})
	def on_config_change(self, config, section, key, value):
		if config is self.config:
			if key == "CC" and value == "On":
				pass
			else:
				print section, key, value
	def build_settings(self, settings):
		settings.add_json_panel('Customization',
				self.config,
				"settings_calc.json")
	def on_pause(self):
		return True
	def on_resume(self):
		pass

if __name__=='__main__':
	CA = CalcApp()
	CA.run()
