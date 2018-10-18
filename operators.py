import decimal
import rpn_types
import errors
import copy

def add(interp, b, a):
	comment = ''
	if a.comment and b.comment:
		comment = a.comment + '+' + b.comment
	return [rpn_types.Value(a.val + b.val, comment)]
def sub(interp, b, a):
	comment = ''
	if a.comment and b.comment:
		comment = a.comment + '-' + b.comment
	return [rpn_types.Value(a.val - b.val, comment)]
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

	return [rpn_types.Value(result)]
def div(interp, b, a):
	comment = ''
	if a.comment and b.comment:
		comment = a.comment + '/' + b.comment
	return [rpn_types.Value(a.val / b.val, comment)]
def convert_int(interp, a):
	return [rpn_types.Value(int(a.val))]
def convert_dec(interp, a):
	return [rpn_types.Value(decimal.Decimal(a.val))]
def convert_float(interp, a):
	return [rpn_types.Value(float(a.val))]
def modulus(interp, b,a):
	comment = ''
	if a.comment and b.comment:
		comment = a.comment + '%' + b.comment
	return [rpn_types.Value(a.val % b.val, comment)]
def swap(interp, a,b):
	return (a, b)
def assign(interp, var, val):
	result = var.reassign(interp,val)
	if result is not None:
		return [result]
	else:
		raise errors.CantAssign('Cannot Do Assignment')
		
def remove(interp, a):
	return None
		
def removes(interp, count):
	interp.message('Dropping ' + str(count.val) )
	interp.pop(count.val)

def group(interp, count):
	newstack = []
	for item in interp.pop(count.val):
		newstack.append(str(item))
	return [rpn_types.Function(stack=newstack[::-1])]


def append(interp, func, item):
	if not type(func) is rpn_types.Function:
		raise errors.FunctionRequired()
	func.stack.append(str(item))
	return [func]

def pop(interp, func):
	if not type(func) is rpn_types.Function:
		raise errors.FunctionRequired()
	item = func.pop()
	return [func, item]



def prepend(interp, func, item):
	if not type(func) is rpn_types.Function:
		raise errors.FunctionRequired()
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
		raise errors.CantAssign('Cannot create comment')

def equal(interp, a, b):
	if a.val == b.val:
		return [rpn_types.Value(1)]
	else:
		return [rpn_types.Value(0)]

def lequal(interp, a, b):
	if a.val <= b.val:
		return [rpn_types.Value(1)]
	else:
		return [rpn_types.Value(0)]
def gequal(interp, a, b):
	if a.val >= b.val:
		return [rpn_types.Value(1)]
	else:
		return [rpn_types.Value(0)]
def less(interp, a, b):
	if a.val < b.val:
		return [rpn_types.Value(1)]
	else:
		return [rpn_types.Value(0)]
def greater(interp, a, b):
	if a.val > b.val:
		return [rpn_types.Value(1)]
	else:
		return [rpn_types.Value(0)]

def call(interp, a):
	if type(a) is rpn_types.Function:
		interp.call(a)
	else:
		raise errors.CantExecute('Cannot Execute a Non-Function')

def call_as_list(interp, a):
	if type(a) is rpn_types.Function:
		interp.call_as_list(a)
	else:
		raise errors.CantExecute('Cannot Execute a Non-Function')


def condition_if(interp, func, condition):
	if condition.val == 1:
		if type(func) is rpn_types.Function:
			interp.call(func)
		else:
			return [ func ] 

def condition_ifelse(interp, func_false, func_true, condition):
	if condition.val == 1:
		if type(func_true) is rpn_types.Function:
			interp.call(func_true)
		else:
			return [ func_true ]
	else:
		if type(func_false) is rpn_types.Function:
			interp.call(func_false)
		else:
			return [ func_false ]

def condition_while(interp, func):
#TODO: need to make the while loop work with code execution break / pause
	interp.loop_count += 1

	if type(func) is not rpn_types.Function:
		raise errors.CantExecute('While loop needs a function')

	result = 1
	try:
		while result == 1:
			interp.call(func)

			condition_result = interp.pop()[0]
			result = condition_result.val
	except errors.WhileBreak:
		pass

	interp.loop_count -= 1
	return []


def condition_while_break(interp):
	if interp.loop_count > 0:
		raise errors.WhileBreak()
	else:
		interp.message("Not in a loop, cannot break")
	return []



def duplicate(interp, a):
	new_a = copy.deepcopy(a)
	return [a, new_a]

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
	return [rpn_types.Value(a.val ** b.val, comment)]

def size(interp):
	return [rpn_types.Value(len(interp))]
	#return [rpn_types.Value(interp.stacksize())]

def subsize(interp, a):
	return [a, rpn_types.Value(len(a))]


def negate(interp, a):
	if a.val == 1:
		return [ rpn_types.Value(0) ]
	else:
		return [ rpn_types.Value(1) ]

def binary(interp):
	original = interp.stack[-1].mode
	try:
		interp.stack[-1].mode = rpn_types.DISPLAY_BIN
		str(interp.stack[-1])
	except:
		interp.stack[-1].mode = original
		interp.message("Could not change display mode to binary for " + str(interp.stack[-1]))
		
def ascii_mode(interp):
	original = interp.stack[-1].mode
	try:
		interp.stack[-1].mode = rpn_types.DISPLAY_ASCII
		str(interp.stack[-1])
	except Exception as e:
		raise e
		interp.stack[-1].mode = original
		interp.message("Could not change display mode to ascii for " + str(interp.stack[-1]))

def hexadecimal(interp):
	original = interp.stack[-1].mode
	try:
		interp.stack[-1].mode = rpn_types.DISPLAY_HEX
		str(interp.stack[-1])
	except:
		interp.stack[-1].mode = original
		interp.message("Could not change display mode to hex for " + str(interp.stack[-1]))

def octal(interp):
	original = interp.stack[-1].mode
	try:
		interp.stack[-1].mode = rpn_types.DISPLAY_OCT
		str(interp.stack[-1])
	except:
		interp.stack[-1].mode = original
		interp.message("Could not change display mode to octal for " + str(interp.stack[-1]))

def set_decimal(interp):
	interp.stack[-1].mode = rpn_types.DISPLAY_DEC

def add_null(interp):
	interp.push(rpn_types.NULL())

def is_null(interp, a):
	if type(a) is rpn_types.NULL:
		return [rpn_types.Value(1)]
	else:
		return [rpn_types.Value(0)]

def concat(interp, item0, item1):

	if type(item0) is not rpn_types.Function:
		func = rpn_types.Function()
		func.stack.insert(0, str(item0))
	else:
		func = item0

	if type(item1) is not rpn_types.Function:
		func.stack.insert(0, str(item1))
	else:
		func.stack = item1.stack + func.stack

	return [func]

def halt_catch_fire(interp):
	interp.debug = True
	if interp.last_fault is not None:
		interp.message("Catching Fire on " + str(interp.last_fault))
		raise interp.last_fault
