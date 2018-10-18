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
       '==': operators.equal, # tested
       '>': operators.greater, # tested
       '<': operators.less, # tested
       '>=': operators.gequal, # tested
       '<=': operators.lequal, # tested
       'not': operators.negate, # tested
       '!': operators.call,
       '!!': operators.call_as_list,
       'if': operators.condition_if,
       'ifelse': operators.condition_ifelse,
       'while': operators.condition_while,
       'break': operators.condition_while_break,
       '^': operators.exponent, # tested
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
       'hcf': operators.halt_catch_fire}

 #functions which cannot appear in a variable name. (ex: testsize will be a variable, but test+ will beak into test and +).
inline_break = {'+': operators.add,
                '-': operators.sub,
                '*': operators.mult,
                '/': operators.div,
                '%': operators.modulus,
                '=': operators.assign,
                '`': operators.remove,
                '?': operators.show_vars,
                '\'': operators.comment,
                '==': operators.equal,
                '>': operators.greater,
                '<': operators.less,
                '>=': operators.gequal,
                '<=': operators.lequal,
                '!': operators.call,
                '^': operators.exponent}

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
		i = Interpreter(self.builtin_functions,self.inline_break_list,parent=self)
		i.loop_count = self.loop_count
		try:
			for x in function.stack:
				i.parse(str(x))
		except errors.WhileBreak as e:
			self.absorb_child(i)
			raise e

		self.absorb_child(i)

	def call_as_list(self, function):
		i = Interpreter(self.builtin_functions,self.inline_break_list,parent=self)
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

				if self.paused:
					if not step:
						self.broken_commands.append(input_string)
						return

				if self.in_string:
					#TODO: make strings their own type or at least better integrate them into lists
					for pos in xrange(len(input_string)):
						if input_string[pos] == "'":
							self.in_string = False
							if self.function_depth > 0:
								self.function_stack[self.function_depth - 1].append("'")
							self.parse(input_string[(pos + 1):])
							return
						if self.function_depth == 0:
							val = rpn_types.Value(ord(input_string[pos]))
							val.mode = rpn_types.DISPLAY_ASCII
							self.push(val)
						else:
							self.function_stack[self.function_depth - 1].append(input_string[pos])

					self.message("String Mode")
					return

				elif '#' in input_string:
					self.parse( input_string.split('#')[0])
					return

				elif ' ' in input_string:
					if "'" in input_string:
						nostring, string_data = input_string.split("'", 1)
						self.parse(nostring)
						if self.function_depth > 0:
							self.function_stack[self.function_depth - 1].append("'")
						self.in_string = True
						self.parse(string_data)
					else:
						for subparse in input_string.split(' '):
							self.parse(subparse)
					return
				else:

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

					if self.function_depth > 0:
						self.function_stack[self.function_depth - 1].append(input_string)
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
						self.push(rpn_types.Value(val))
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

							if input_string[0] == '\\':
								val = None
								try:
									if len(input_string) == 1:
										val = int(self.pop()[0].val)
									else:
										val = int(input_string[1:])
									if self.stacksize() > 0:
										item = self.pop()[0]
										self.push(item)
									else:
										raise errors.NotEnoughOperands("Can't get subitem of an element that isn't there")
									#self.push(item)
									#self.message(str(item))
									try:
										v = item.get_index(val)
										self.parse(str(v))
									except IndexError:
										raise errors.OutOfBounds("Cannot access out of array bounds")
									#self.message('parsing ' + str(v))
									#self.push(rpn_types.Value(v))
									return
								except ValueError:

									if len(input_string) == 1:
										varname = str(self.pop()[0].val)
									varname = input_string[1:]
									if self.stacksize() > 0:
										item = self.pop()[0]
										self.push(item)
									else:
										raise errors.NotEnoughOperands("Can't get subitem of an element that isn't there")
									try:
										v = item.get_var(varname)
										self.parse(str(v))
									except IndexError:
										raise errors.OutOfBounds("Cannot access out of array bounds")
									#self.message('parsing ' + str(v))
									#self.push(rpn_types.Value(v))
									return

									raise

							elif input_string[0] not in '0123456789.':
								self.push(self.get_var(input_string))

			except (errors.NotEnoughOperands, errors.CantAssign, errors.CantCloseBlock, errors.CantExecute, TypeError, AttributeError, decimal.DivisionByZero, errors.FunctionRequired, errors.OutOfBounds, errors.VarNotFound) as e:
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
