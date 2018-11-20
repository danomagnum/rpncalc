import inspect
import copy
import decimal
import operators
import rpn_types
import errors

import sys
sys.setrecursionlimit(10000)

DEBUG = False


log = []
 # default built in functions
ops = {'+': operators.add, # tested
       '-': operators.sub, # tested
       '*': operators.mult, # tested
       '/': operators.div, # tested
       '%': operators.modulus, # tested
       'int': operators.convert_int,
       'float': operators.convert_float,
       'swap': operators.swap,
       'dup': operators.duplicate,
       'rot': operators.rotate,
       'over': operators.over,
       'tuck': operators.tuck,
       'pick': operators.pick,
       'roll': operators.roll,
       '=': operators.assign,
       '`': operators.remove,
       'drop': operators.remove,
       'drops': operators.removes,
       'group': operators.group,
       'append': operators.append,
       'prepend': operators.prepend,
       'pop': operators.pop,
       '?': operators.show_vars,
       '"': operators.comment,
       '==': operators.equal,
       '>': operators.greater,
       '<': operators.less,
       '>=': operators.gequal,
       '<=': operators.lequal,
       'not': operators.negate,
       '!': operators.call,
       '!!': operators.call_as_list,
       'if': operators.condition_if,
       'ifelse': operators.condition_ifelse,
       'while': operators.condition_while,
       'break': operators.condition_while_break,
       '^': operators.exponent,
       '\\size': operators.subsize,
       'size': operators.size,
       'bin': operators.binary,
       'hex': operators.hexadecimal,
       'oct': operators.octal,
       'dec': operators.decimal,
       'ascii': operators.ascii_mode,
       'NULL': operators.add_null,
       'isnull': operators.is_null,
       'cat': operators.concat,
       'hcf': operators.halt_catch_fire,
       '\\': operators.reference}

FUNCSTART = '['
FUNCEND = ']'
BREAK = '@'

FLOW_TOKENS = [FUNCSTART, FUNCEND, BREAK]


class Interpreter(object):
	def __init__(self, builtin_functions=None,  stack=None, parent=None):
		if builtin_functions is None:
			builtin_functions = {}

		self.builtin_functions = builtin_functions

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

		self.debug = DEBUG
		self.last_fault = None

	def __str__(self):
		stackstring = ''
		for x in self.stack:
			stackstring += str(x) + '\n'
		return stackstring
	def message(self, text):
		self.messages.append(text)
	def push(self, value):
		if self.function_depth > 0:
			self.function_stack[self.function_depth - 1].append(value)
		else:
			self.stack.append(value)
	def pop(self, count = 1):
		vals = []

		if count > len(self.stack):
			if self.parent is not None:
				if count > self.stacksize():
					raise errors.NotEnoughOperands('Not Enough Operands (Parent checked)')
				else:
					mine = len(self.stack)
					parents = count - mine
					for x in range(mine):
						vals.append(self.stack.pop())
					vals += self.parent.pop(parents)
			else:
				raise errors.NotEnoughOperands('Not Enough Operands (No Parent)')
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
		if self.function_depth == 0:
			self.function_stack = [[]]
		else:
			self.function_stack.append([])

		self.function_depth += 1

	def function_end(self):
		self.function_depth -= 1

		f = rpn_types.Function(stack = self.function_stack[self.function_depth])

		#self.message('closing function ' + str(f))
		
		if self.function_depth == 0:
			#finish recording function
			self.function_stack = None
			self.push(f)
		else:
			self.function_stack[self.function_depth - 1].append(f)
			self.function_stack.pop()
	
	def absorb_child(self, child):
		if child.paused:
			self.paused = True
			self.child = child
		else:
			for item in child.stack:
				if hasattr(item, 'name'):
					if item.name not in self.variables.keys() or item.name[0] == '$':
						# was a local variable
						if type(item) is rpn_types.Variable:
							item = rpn_types.Value(item.val, item.comment)
							pass
						elif type(item) is rpn_types.Function:
							item.name = None # make it a lambda

				self.push(item)
		self.messages += child.messages

	def call(self, function):
		i = Interpreter(self.builtin_functions,parent=self)
		i.loop_count = self.loop_count
		try:
			for x in function.stack:
				i.parse(str(x))
		except errors.WhileBreak as e:
			self.absorb_child(i)
			raise e

		self.absorb_child(i)

	def call_as_list(self, function):
		i = Interpreter(self.builtin_functions,parent=self)
		i.loop_count = self.loop_count
		try:
			for x in function.stack:
				i.parse(str(x))
		except errors.WhileBreak as e:
			self.absorb_child(i)
			raise e

		f = rpn_types.Function()
		f.stack = i.stack
		self.push(f)

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

				tokens = tokenize(self.operatorlist, input_string)
				for token in tokens:
					if self.paused:
						if not step:
							self.broken_commands.append(token)
							continue
					if type(token) is rpn_types.Flow_Control:

						if token.val == FUNCSTART:
							self.function_start()
							continue
						if token.val == FUNCEND:
							self.function_end()
							continue

					if self.function_depth > 0:
						self.function_stack[self.function_depth - 1].append(token)
						continue

					if type(token) is rpn_types.Flow_Control:
						if token.val == BREAK:
							self.message("Break!")
							self.paused = True
							continue

					if type(token) is rpn_types.Value:
						self.push(token)
						continue

					if type(token) is rpn_types.Operator:
						func = self.builtin_functions[token.val]
						argcount = len(inspect.getargspec(func).args) - 1
						args = [self] + self.pop(argcount)
						result = func(*args)
						if result is not None:
							for val in result:
								self.push(val)
						continue

					if type(token) is rpn_types.Variable_Placeholder:	
						self.push(self.get_var(token.val))

			except (errors.NotEnoughOperands, errors.CantAssign, errors.CantCloseBlock, errors.CantExecute, TypeError, AttributeError, decimal.DivisionByZero, errors.FunctionRequired, errors.OutOfBounds, errors.VarNotFound, ValueError) as e:
				self.last_fault = e
				if not self.debug:
					if root:
						self.message('Stack Unchanged - ' + (e.message))
						self.restore()
						return
					else:
						raise
				raise
			except errors.WhileBreak as e:
				raise e

			except Exception as e:
				if not self.debug:
					if root:
						self.message(str(e.message) + ' - Stack Unchanged')
						self.restore()
						raise
						return
					raise
				raise


	def new_var(self, name):
		var = rpn_types.Variable(name)
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

	def __len__(self):
		return self.stacksize()

def flatten(list_of_lists):
	if type(list_of_lists) is str:
		return list_of_lists
	result = []
	for sublist in list_of_lists:
		if type(sublist) is str:
			result.append(sublist)
		else:
			result.append(flatten(sublist))
	return result

def splitup(string):
	result = []
	comment = '#'
	ignore = [' ', '']
	break_tokens = ['[', ']',
	                '+', '-', '*', '/', '^', '%',
                        '`',
                        '?',
			' '
			]

	working = string.split(comment)[0]
	working = working.split(' ')

	for token in break_tokens:
		subresult = []
		for part in working:
			if token in part:
				parted = part.split(token)
				for a in parted:
					subresult.append(a)
					subresult.append(token)
				subresult.pop()
			else:
				subresult.append(part)
		working = flatten(subresult)

	working = [x for x in working if x not in ignore]

	return working

def tokenize(ops, input_string):

	# first split the input string into a list of sub-strings
	input_tokens = splitup(input_string)

	output_tokens = []

	for token in input_tokens:
		if token in FLOW_TOKENS:
			output_tokens.append(rpn_types.Flow_Control(token))
			continue
		# check if the input is just a value.
		try:
			val = decimal.Decimal(token)
			output_tokens.append(rpn_types.Value(val))
			continue
		except:
			#the input is not just a value so lets see if it is a function
			if token in ops:
				output_tokens.append(rpn_types.Operator(token))
				continue
			else:
				output_tokens.append(rpn_types.Variable_Placeholder(token))
				continue
	
	return output_tokens
