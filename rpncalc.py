import inspect
import copy
import decimal

import sys
sys.setrecursionlimit(10000)

DEBUG = False

log = []

DISPLAY_BIN = 2
DISPLAY_DEC = 10
DISPLAY_OCT = 8
DISPLAY_HEX = 16
DISPLAY_ASCII = 128

def add(interp, b, a):
	comment = ''
	if a.comment and b.comment:
		comment = a.comment + '+' + b.comment
	return [Value(a.val + b.val, comment)]
def sub(interp, b, a):
	comment = ''
	if a.comment and b.comment:
		comment = a.comment + '-' + b.comment
	return [Value(a.val - b.val, comment)]
def mult(interp, b, a):
	comment = ''
	result = 0
	if a.comment and b.comment:
		comment = a.comment + '*' + b.comment

	if type(a.val) is decimal.Decimal:
		if type(b.val) is float:
			result = a.val * decimal.Decimal(b.val)
			interp.message("Mangling a float to a decimal")
		else:
			result = a.val * b.val
			
	elif type(b.val) is decimal.Decimal:
		if type(a.val) is float:
			result = decimal.Decimal(a.val) * b.val
			interp.message("Mangling a float to a decimal")
		else:
			result = a.val * b.val
	else:
		result = a.val * b.val

	return [Value(result)]
def div(interp, b, a):
	comment = ''
	if a.comment and b.comment:
		comment = a.comment + '/' + b.comment
	return [Value(a.val / b.val, comment)]
def convert_int(interp, a):
	return [Value(int(a.val))]
def convert_dec(interp, a):
	return [Value(decimal.Decimal(a.val))]
def convert_float(interp, a):
	return [Value(float(a.val))]
def modulus(interp, b,a):
	comment = ''
	if a.comment and b.comment:
		comment = a.comment + '%' + b.comment
	return [Value(a.val % b.val, comment)]
def swap(interp, a,b):
	return (a, b)
def assign(interp, var, val):
	result = var.reassign(interp,val)
	if result is not None:
		return [result]
	else:
		raise CantAssign('Cannot Do Assignment')
		
def remove(interp, a):
	return None
		
def removes(interp, count):
	interp.message('Dropping ' + str(count.val) )
	interp.pop(count.val)

def group(interp, count):
	newstack = []
	for item in interp.pop(count.val):
		newstack.append(str(item))
	return [Function(stack=newstack[::-1])]



def append(interp, func, item):
	if not type(func) is Function:
		raise FunctionRequired()
	func.stack.append(str(item))
	return [func]

def prepend(interp, func, item):
	if not type(func) is Function:
		raise FunctionRequired()
	func.stack.insert(0, str(item))
	return [func]

def show_vars(interp):
	for value in interp.variables.itervalues():
		interp.message(str(value))
def comment(interp, a, b):
	if hasattr(a, 'name'):
		b.comment = a.name
		interp.variables.pop(a.name)
		return [b]
	else:
		raise CantAssign('Cannot create comment')

def equal(interp, a, b):
	if a.val == b.val:
		return [Value(1)]
	else:
		return [Value(0)]

def lequal(interp, a, b):
	if a.val <= b.val:
		return [Value(1)]
	else:
		return [Value(0)]
def gequal(interp, a, b):
	if a.val >= b.val:
		return [Value(1)]
	else:
		return [Value(0)]
def less(interp, a, b):
	if a.val < b.val:
		return [Value(1)]
	else:
		return [Value(0)]
def greater(interp, a, b):
	if a.val > b.val:
		return [Value(1)]
	else:
		return [Value(0)]

def call(interp, a):
	if type(a) is Function:
		interp.call(a)
	else:
		raise CantExecute('Cannot Execute a Non-Function')

def condition_if(interp, func, condition):
	if condition.val == 1:
		if type(func) is Function:
			interp.call(func)
		else:
			return [ func ] 

def condition_ifelse(interp, func_false, func_true, condition):
	if condition.val == 1:
		if type(func_true) is Function:
			interp.call(func_true)
		else:
			return [ func_true ]
	else:
		if type(func_false) is Function:
			interp.call(func_false)
		else:
			return [ func_false ]

def condition_while(interp, func):
#TODO: need to make the while loop work with code execution break / pause
	interp.loop_count += 1

	if type(func) is not Function:
		raise CantExecute('While loop needs a function')

	result = 1
	try:
		while result == 1:
			interp.call(func)

			condition_result = interp.pop()[0]
			result = condition_result.val
	except WhileBreak:
		pass

	interp.loop_count -= 1
	return []


def condition_while_break(interp):
	if interp.loop_count > 0:
		raise WhileBreak()
	else:
		interp.message("Not in a loop, cannot break")
	return []



def duplicate(interp, a):
	return [a, a]

def rotate(interp, a, b, c):
	return [ b, a, c ]

def over (interp, a, b):
	return [b, a, b]

def tuck (interp, a, b):
	return [a, b, a]

def pick(interp, number):
	items = interp.pop(number.val + 1)
	items.reverse()
	return items + [items[0]]

def roll(interp, number):
	items = interp.pop(number.val + 1)
	items.reverse()
	return items[1:] + [items[0]]

def exponent(interp, b, a):
	comment = ''
	if a.comment and b.comment:
		comment = a.comment + '^' + b.comment
	return [Value(a.val ** b.val, comment)]

def size(interp):
	return [Value(interp.stacksize())]

def negate(interp, a):
	if a.val == 1:
		return [ Value(0) ]
	else:
		return [ Value(1) ]

def binary(interp):
	original = interp.stack[-1].mode
	try:
		interp.stack[-1].mode = DISPLAY_BIN
		str(interp.stack[-1])
	except:
		interp.stack[-1].mode = original
		interp.message("Could not change display mode to binary for " + str(interp.stack[-1]))
		
def ascii_mode(interp):
	original = interp.stack[-1].mode
	try:
		interp.stack[-1].mode = DISPLAY_ASCII
		str(interp.stack[-1])
	except:
		interp.stack[-1].mode = original
		interp.message("Could not change display mode to ascii for " + str(interp.stack[-1]))

def hexadecimal(interp):
	original = interp.stack[-1].mode
	try:
		interp.stack[-1].mode = DISPLAY_HEX
		str(interp.stack[-1])
	except:
		interp.stack[-1].mode = original
		interp.message("Could not change display mode to hex for " + str(interp.stack[-1]))

def octal(interp):
	original = interp.stack[-1].mode
	try:
		interp.stack[-1].mode = DISPLAY_OCT
		str(interp.stack[-1])
	except:
		interp.stack[-1].mode = original
		interp.message("Could not change display mode to octal for " + str(interp.stack[-1]))

def set_decimal(interp):
	interp.stack[-1].mode = DISPLAY_DEC

def add_null(interp):
	interp.push(NULL())

def is_null(interp, a):
	if type(a) is NULL:
		return [Value(1)]
	else:
		return [Value(0)]

def concat(interp, item0, item1):

	if type(item0) is not Function:
		func = Function()
		func.stack.insert(0, str(item0))
	else:
		func = item0

	if type(item1) is not Function:
		func.stack.insert(0, str(item1))
	else:
		func.stack = item1.stack + func.stack

	return [func]

 # default built in functions
ops = {'+': add, # tested
       '-': sub, # tested
       '*': mult, # tested
       '/': div, # tested
       '%': modulus, # tested
       'int': convert_int,
       'float': convert_float,
       'swap': swap,
       'dup': duplicate,
       'rot': rotate,
       'over': over,
       'tuck': tuck,
       'pick': pick,
       'roll': roll,
       '=': assign,
       '`': remove,
       'drop': remove,
       'drops': removes,
       'group': group,
       'append': append,
       'prepend': prepend,
       '?': show_vars,
       '"': comment,
       '==': equal, # tested
       '>': greater, # tested
       '<': less, # tested
       '>=': gequal, # tested
       '<=': lequal, # tested
       'not': negate, # tested
       '!': call,
       'if': condition_if,
       'ifelse': condition_ifelse,
       'while': condition_while,
       'break': condition_while_break,
       '^': exponent, # tested
       'size': size,
       'bin': binary,
       'hex': hexadecimal,
       'oct': octal,
       'dec': decimal,
       'ascii': ascii_mode,
       'null': add_null,
       'isnull': is_null,
       'cat': concat}

 #functions which cannot appear in a variable name. (ex: testsize will be a variable, but test+ will beak into test and +).
inline_break = {'+': add,
                '-': sub,
                '*': mult,
                '/': div,
                '%': modulus,
                '=': assign,
                '`': remove,
                '?': show_vars,
                '\'': comment,
                '==': equal,
                '>': greater,
                '<': less,
                '>=': gequal,
                '<=': lequal,
                '!': call,
                '^': exponent}

class FunctionRequired(Exception):
	pass

class NotEnoughOperands(Exception):
	pass

class CantCloseBlock(Exception):
	pass

class CantAssign(Exception):
	pass

class CantExecute(Exception):
	pass

class WhileBreak(Exception):
	pass

class Function(object):
	def __init__(self, name=None, stack = None, comment = ''):
		self.name = name
		if stack is None:
			self.stack = []
		else:
			self.stack = stack
		self.comment = comment
	
	def reassign(self, interp, val):
		if type(val) == Variable:
			var = Variable(self.name, val.val)
			interp.variables[self.name] = var
			return var
		elif type(val) == Value:
			var = Variable(self.name, val.val)
			interp.variables[self.name] = var
			return var
		elif type(val) == Function:
			self.stack = val.stack
			interp.variables[self.name] = self 
			return self 
	def __str__(self):
		name = ''
		for x in self.stack:
			name += str(x) + " "
		name = '[ ' + name + ']'

		if self.name is not None:
			name += ' ' + self.name + ' = '

		if self.comment:
			name += ' ' + self.comment + '"'
		return name

class Variable(object):
	def __init__(self, name, val=0, comment='', mode=DISPLAY_DEC) :
		self.name = name
		self.val = val
		self.comment = comment
		self.mode = mode
	def reassign(self, interp, val):
		if type(val) == Variable:
			self.val = val.val
			return self
		elif type(val) == Value:
			self.val = val.val
			return self
		elif type(val) == Function:
			f = Function(self.name, val.stack, self.comment)
			interp.variables[self.name] = f
			return f

	def __str__(self) :
		string = ''
		if self.mode == DISPLAY_DEC:
			string += str(self.val)
		elif self.mode == DISPLAY_HEX:
			string += "Ox%X" % self.val
		elif self.mode == DISPLAY_OCT:
			string += "0o%o" % self.val
		elif self.mode == DISPLAY_BIN:
			string += str(bin(self.val))
		elif self.mode == DISPLAY_ASCII:
			string += str(repr(chr(self.val)))
		string += ' ' + str(self.name) + ' = '
		if self.comment:
			string += ' ' + self.comment + '"'
		return string
	def __eq__(self, other):
		return self.val == other.val
	def __ne__(self, other):
		return self.val != other.val

class NULL(object):
	def __init__(self, comment=''):
		self.comment = comment
	def __str__(self) :
		return 'NULL'


class Value(object):
	def __init__(self, val=0, comment='', mode=DISPLAY_DEC) :
		self.val = val
		self.comment = comment
		self.mode = mode
	def reassign(self, interp, val):
		return None
	def __str__(self) :

		if self.mode == DISPLAY_DEC:
			string = str(self.val)
		elif self.mode == DISPLAY_HEX:
			string = "Ox%X" % self.val
		elif self.mode == DISPLAY_OCT:
			string = "0o%o" % self.val
		elif self.mode == DISPLAY_BIN:
			string = str(bin(self.val))
		elif self.mode == DISPLAY_ASCII:
			string = str(repr(chr(self.val)))

		if self.comment:
			string += ' ' + self.comment + '"'
		return string
	def __eq__(self, other):
		return self.val == other.val
	def __ne__(self, other):
		return self.val != other.val

class Interpreter(object):
	def __init__(self, builtin_functions=None, inline_break_list=None, stack=None, parent=None):
		if builtin_functions is None:
			builtin_functions = {}

		self.builtin_functions = builtin_functions

		if inline_break_list is None:
			inline_break_list = {}

		self.inline_break_list = inline_break_list

		if stack is None:
			stack = []
		self.stack = stack

		self.operatorlist = self.builtin_functions.keys()
		self.operatorlist = sorted(self.operatorlist, key=lambda a: len(a), reverse=True)

		self.variables = {}

		self.backup_stack = None
		self.backup_vars = None

		self.messages = []

		self.function_stack = None
		self.function_depth = 0

		self.parent = parent
		self.loop_count = 0

		self.in_string = False

		self.paused = False
		self.broken_commands = []
		self.child = None

	def __str__(self):
		stackstring = ''
		for x in self.stack:
			stackstring += str(x) + '\n'
		return stackstring
	def message(self, text):
		self.messages.append(text)
	def push(self, value):
		if self.function_stack is not None:
			self.function_stack.append(value)
		else:
			self.stack.append(value)
	def pop(self, count = 1):
		vals = []

		if count > len(self.stack):
			if self.parent is not None:
				if count > self.stacksize():
					raise NotEnoughOperands('Not Enough Operands (Parent checked)')
				else:
					mine = len(self.stack)
					parents = count - mine
					for x in range(mine):
						vals.append(self.stack.pop())
					vals += self.parent.pop(parents)
			else:
				raise NotEnoughOperands('Not Enough Operands (No Parent)')
		else:
			for x in range(count):
				vals.append(self.stack.pop())
		return vals
	
	def stacksize(self, me_only = False):
		count = len(self.stack)
		if not me_only:
			if self.parent is not None:
				count += self.parent.stacksize()
		return count

	def backup(self):
		self.backup_stack = copy.deepcopy(self.stack)
		self.backup_vars = copy.deepcopy(self.variables)

	def backedup(self):
		if self.backup_stack is None:
			return False

		if self.backup_vars is None:
			return False

		return True

	def restore(self, clear_backups = True):
		self.stack = self.backup_stack
		self.variables = self.backup_vars

		if clear_backups:
			self.backup_stack = None
			self.backup_vars = None


	def function_start(self):
		if self.function_stack is None:
			#start recording function
			self.function_stack = []
		else:
			self.function_stack.append('[')

		self.function_depth += 1

	def function_end(self):
		self.function_depth -= 1
		
		if self.function_depth == 0:
			#finish recording function
			f = Function(stack = self.function_stack)
			self.function_stack = None
			self.push(f)
		else:
			self.function_stack.append(']')
	
	def absorb_child(self, child):
		if child.paused:
			self.paused = True
			self.child = child
		else:
			for item in child.stack:
				if hasattr(item, 'name'):
					if item.name not in self.variables.keys() or item.name[0] == '$':
						# was a local variable
						if type(item) is Variable:
							item = Value(item.val, item.comment)
							pass
						elif type(item) is Function:
							item.name = None # make it a lambda

				self.push(item)
		self.messages += child.messages

	def call(self, function):
		i = Interpreter(self.builtin_functions,self.inline_break_list,parent=self)
		i.loop_count = self.loop_count
		try:
			for x in function.stack:
				i.parse(x)
		except WhileBreak as e:
			self.absorb_child(i)
			raise e

		self.absorb_child(i)

	def step(self):
		if self.child is None:
			if len(self.broken_commands):
				command = self.broken_commands[0]
				self.parse(command, step=True)
				self.broken_commands = self.broken_commands[1:]
			else:
				if self.parent is not None:
					self.parent.absorb_child(self)
					self.parent.broken_child = None
					self.parent.message('done with child')
					return
		else:
			self.child.step()

	def resume(self):
		if self.child is not None:
			self.child.resume()
			self.absorb_child(self.child)
			self.child = None

		self.paused = False
		for command in self.broken_commands:
			self.parse(command)
		if self.paused == False:
			self.broken_commands = []

	def get_stack(self):
		stack = self.stack[:]
		if self.child is not None:
			stack += self.child.get_stack()
		return stack
	def get_broken_commands(self):
		commands = []
		if self.child is not None:
			commands += self.child.get_broken_commands()
		commands += self.broken_commands
		return commands
			
	def parse(self, input_string, root = False, step = False):
		if self.child:
			self.child.parse(input_string, step=step)
		else:
			if input_string == '':
				return

			if root:
				self.backup()
				self.messages = []

			try:
				# first split the input up into multiple components if there are any and parse them in order

				if self.paused:
					if not step:
						self.broken_commands.append(input_string)
						return

				if self.in_string:
					for pos in xrange(len(input_string)):
						if input_string[pos] == "'":
							self.in_string = False
							if self.function_stack is not None:
								self.function_stack.append("'")
							self.parse(input_string[(pos + 1):])
							return
						if self.function_stack is None:
							val = Value(ord(input_string[pos]))
							val.mode = DISPLAY_ASCII
							self.push(val)
						else:
							self.function_stack.append(input_string[pos])

					self.message("String Mode")
					return

				elif '#' in input_string:
					self.parse( input_string.split('#')[0])
					return

				elif ' ' in input_string:
					if "'" in input_string:
						nostring, string_data = input_string.split("'", 1)
						self.parse(nostring)
						if self.function_stack is not None:
							self.function_stack.append("'")
						self.in_string = True
						self.parse(string_data)
					else:
						for subparse in input_string.split(' '):
							self.parse(subparse)
					return
				else:
					# handle the flow control items
				#	for symbol in ('[', ']'):
				#		if symbol in input_string:
				#			if symbol == '[':
				#				self.function_start()
				#			elif symbol == ']':
				#				self.function_end()
				#			else:
				#				components = input_string.split(symbol)
				#				if components[-1] == '':
				#					components = components[:-1]
				#				for subparse in components:
				#					if subparse != '':
				#						self.parse(subparse)
				#					self.parse(symbol)
				#			return


					if '[' in input_string:
						components = input_string.split('[')
						for component in components[:-1]:
							if component != '':
								self.parse(component)
							self.function_start()
						if components[-1] != '':
							self.parse(components[-1])
						return
					if ']' in input_string:
						components = input_string.split(']')
						for component in components[:-1]:
							if component != '':
								self.parse(component)
							self.function_end()
						if components[-1] != '':
							self.parse(components[-1])
						return

					if self.function_stack is not None:
						self.function_stack.append(input_string)
						return
					elif input_string[0] == "'":
						self.in_string = True
						if len(input_string) > 1:
							self.parse(input_string[1:])

						self.message("String Mode")
						return
					elif input_string == '@':
						self.message("Break!")
						self.paused = True
						return


					# check if the input is just a value.
					try:
						val = decimal.Decimal(input_string)
						self.push(Value(val))
						return
					except:
						#the input is not just a value so lets see if it is a function
						if input_string in self.operatorlist:
							func = self.builtin_functions[input_string]
							argcount = len(inspect.getargspec(func).args) - 1
							args = [self] + self.pop(argcount)
							result = func(*args)
							if result is not None:
								for val in result:
									self.push(val)
							return
						else:
							#the input string is not just a function shorthand.
							#search through the string and see if there are any functions here.
							for funcname in self.inline_break_list:
								if funcname in input_string:
									components = input_string.split(funcname)
									if components[-1] == '':
										components = components[:-1]
									for subparse in components:
										if subparse != '':
											self.parse(subparse)
										self.parse(funcname)
									return
							#must be a variable
							if input_string[0] not in '0123456789.':
								self.push(self.get_var(input_string))

			except (NotEnoughOperands, CantAssign, CantCloseBlock, CantExecute, TypeError, AttributeError, decimal.DivisionByZero, FunctionRequired) as e:
				if not DEBUG:
					if root:
						self.message('Stack Unchanged - ' + (e.message))
						self.restore()
						return
					else:
						raise
				raise
			except WhileBreak as e:
				raise e

			except Exception as e:
				if not DEBUG:
					if root:
						self.message(str(e.message) + ' - Stack Unchanged')
						self.restore()
						raise
						return
					raise
				raise


	def new_var(self, name):
		var = Variable(name)
		self.variables[name] = var
		return var
	
	def get_var(self, name, create = True):
		if name not in self.variables.keys():
			if name[0] != '$':
				if self.parent is not None:
					var = self.parent.get_var(name, False)
					if var is not None:
						return var
					#if name in self.parent.variables.keys():
						#return self.parent.get_var(name)
			if create:
				return self.new_var(name)
			else:
				return None
		else:
			return self.variables[name]

	
