import unittest
import rpncalc
import decimal
import rpn_types
import errors

TEST_REFS = True
TEST_STRINGS = False


class BasicMath(unittest.TestCase):
	def setUp(self):
		self.interp = rpncalc.Interpreter(rpncalc.ops)
		self.x0 = 2
		self.x1 = 3
		self.interp.parse('%i %i' %(self.x0, self.x1))
	def test_start(self):
		self.assertEqual(self.interp.stack, [rpn_types.Value(self.x0), rpn_types.Value(self.x1)])

	def test_add(self):
		self.interp.parse('+')
		result = self.x0 + self.x1
		self.assertEqual(self.interp.stack, [rpn_types.Value(result)])

	def test_sub(self):
		self.interp.parse('-')
		result = self.x0 - self.x1
		self.assertEqual(self.interp.stack, [rpn_types.Value(result)])
	
	def test_mult(self):
		self.interp.parse('*')
		result = self.x0 * self.x1
		self.assertEqual(self.interp.stack, [rpn_types.Value(result)])

	def test_div(self):
		self.interp.parse('/')
		result = decimal.Decimal(self.x0) / decimal.Decimal(self.x1)
		self.assertEqual(self.interp.stack, [rpn_types.Value(result)])

	def test_mod(self):
		self.interp.parse('%')
		result = self.x0 % self.x1
		self.assertEqual(self.interp.stack, [rpn_types.Value(result)])

	def test_power(self):
		self.interp.parse('^')
		result = self.x0 ** self.x1
		self.assertEqual(self.interp.stack, [rpn_types.Value(result)])
	

class BasicComparisons(unittest.TestCase):
	def setUp(self):
		self.interp = rpncalc.Interpreter(rpncalc.ops)
		self.xbase = 53
		self.interp.parse(str(self.xbase))

	def test_start(self):
		self.assertEqual(self.interp.stack, [rpn_types.Value(self.xbase)])

	def test_equal_fail(self):
		self.interp.parse(str(self.xbase*2))
		self.interp.parse('==')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(0))

	def test_equal_success(self):
		self.interp.parse(str(self.xbase))
		self.interp.parse('==')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(1))

	def test_lessequal_greater_fail(self):
		self.interp.parse(str(self.xbase*2))
		self.interp.parse('<=')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(0))

	def test_lessequal_equal_success(self):
		self.interp.parse(str(self.xbase))
		self.interp.parse('<=')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(1))

	def test_lessequal_less_success(self):
		self.interp.parse(str(self.xbase / 2))
		self.interp.parse('<=')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(1))

	def test_greaterequal_greater_success(self):
		self.interp.parse(str(self.xbase*2))
		self.interp.parse('>=')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(1))

	def test_greaterequal_equal_success(self):
		self.interp.parse(str(self.xbase))
		self.interp.parse('>=')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(1))

	def test_greaterequal_less_fail(self):
		self.interp.parse(str(self.xbase / 2))
		self.interp.parse('>=')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(0))


	def test_less_greater_fail(self):
		self.interp.parse(str(self.xbase*2))
		self.interp.parse('<')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(0))

	def test_less_equal_fail(self):
		self.interp.parse(str(self.xbase))
		self.interp.parse('<')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(0))

	def test_less_less_success(self):
		self.interp.parse(str(self.xbase / 2))
		self.interp.parse('<')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(1))

	def test_greater_greater_success(self):
		self.interp.parse(str(self.xbase*2))
		self.interp.parse('>')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(1))

	def test_greater_equal_fail(self):
		self.interp.parse(str(self.xbase))
		self.interp.parse('>')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(0))

	def test_greater_less_fail(self):
		self.interp.parse(str(self.xbase / 2))
		self.interp.parse('>')
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(0))

class SubroutineTest(unittest.TestCase):
	def setUp(self):
		self.interp = rpncalc.Interpreter(rpncalc.ops)
	
	def test_simple(self):
		function = '[ 2 ] '
		function_stack = ['2']
		self.interp.parse(function)
		self.assertEqual([str(x) for x in self.interp.stack[-1].stack], function_stack)

	def test_simple2(self):
		function = '[ 2 3 ]'
		function_stack = ['2', '3']
		self.interp.parse(function)
		self.assertEqual([str(x) for x in self.interp.stack[-1].stack], function_stack)

	def test_simple3(self):
		function = '[ 2 3  + ]'
		function_stack = ['2', '3', '+']
		self.interp.parse(function)
		self.assertEqual([str(x) for x in self.interp.stack[-1].stack], function_stack)

	def test_simple4(self):
		function = '[ 2 3  + ] !'
		self.interp.parse(function)
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(5))

	def test_strings(self):
		if TEST_STRINGS:
			function = "[ 'hello world' ] !"
			self.interp.parse(function)
			result = []
			for x in self.interp.stack:
				result.append(chr(x.val))
			result = ''.join(result)
			self.assertEqual(result, 'hello world')

	def test_nested(self):
		function = '[ [ 2 3  + ] ! 7 + ] !'
		self.interp.parse(function)
		self.assertEqual(self.interp.stack[-1], rpn_types.Value(12))

	def test_recursive(self):
		function = '[ q = ` b = ` a = b + c = ` a int b int c int q 1 - q = 0 < [ q fib !  ] if ] fib = '
		result = [1, 1, 2, 3, 5, 8, 13]
		result2 = [rpn_types.Value(i) for i in result]
		self.interp.parse('1 1 5')
		self.interp.parse(function)
		self.interp.parse('!')
		self.assertEqual(self.interp.stack, result2)

	def test_scope1(self):
		#test that the function can see variables in its parent without changing them
		function = '3 a = [ a 1 + ] !'
		result = [3, 4]
		result2 = [rpn_types.Value(i) for i in result]
		self.interp.parse(function)
		self.assertEqual(self.interp.stack, result2)

	def test_scope2(self):
		#test that the function can change unsigiled vars in its parent
		function = '3 a = [ 4 a = ] !'
		result = [4, 4]
		result2 = [rpn_types.Value(i) for i in result]
		self.interp.parse(function)
		self.assertEqual(self.interp.stack, result2)

	def test_scope3a(self):
		#test that sigils make vars local
		function = '3 $a = [ 4 $a = ] !'
		result = [3, 4]
		result2 = [rpn_types.Value(i) for i in result]
		self.interp.parse(function)
		self.assertEqual(self.interp.stack, result2)

	def test_scope3b(self):
		#test that sigils make vars local
		function = '3 $a = [ 4 a = ] !'
		result = [3, 4]
		result2 = [rpn_types.Value(i) for i in result]
		self.interp.parse(function)
		self.assertEqual(self.interp.stack, result2)

	def test_scope3c(self):
		#test that sigils make vars local
		function = '3 a = [ 4 $a = ] !'
		result = [3, 4]
		result2 = [rpn_types.Value(i) for i in result]
		self.interp.parse(function)
		self.assertEqual(self.interp.stack, result2)

	def test_references1(self):
		# make sure we can reference all the elements in an array via parameter 
		if TEST_REFS:
			tests = [(r'[1 2 3] 0 \ ', 1),
			(r'[1 2 3] 1 \ ', 2),
			(r'[1 2 3] 2 \ ', 3),
			(r'[1 [2] 3] 1 \ ', '[ 2 ]'),
			(r'[1 [2] 3] 1 \ 0 \ ', '2'),
			(r'[1 [2] 3] 1 \ ! ', '2'),
			(r'1 0 \ ', 1)]

			for t in tests:
				self.interp.parse(t[0])
				self.assertEqual(str(self.interp.stack[-1]), str(t[1]))

	def test_references2(self):
		# make sure we can't reference outside an array
		if TEST_REFS:
			tests = [(r'[ 1 2 3 ] 3 \ '),
				 (r'1 1 \ ')]
			for t in tests:
				self.assertRaises(errors.OutOfBounds,self.interp.parse,t)

	def test_references3(self):
		if TEST_REFS:
			# make sure we reference up the sack out of a function
			tests = [(r'[ 1 2 3 ] [ 2 \ ] !', '3')]

			for t in tests:
				self.interp.parse(t[0])
				self.assertEqual(str(self.interp.stack[-1]), str(t[1]))


class StringsTest(unittest.TestCase):
	if TEST_STRINGS:
		def setUp(self):
			self.interp = rpncalc.Interpreter(rpncalc.ops)
		
		def test_1(self):
			function = "'hello world'"
			self.interp.parse(function)
			result = []
			for x in self.interp.stack:
				result.append(chr(x.val))
			result = ''.join(result)
			self.assertEqual(result, 'hello world')


def example_operation_noparams(interp):
	return []
def example_operation_oneparam(interp, a):
	return []
def example_operation_twoparam(interp, a, b):
	return []

class OperandCounts(unittest.TestCase):
	def setUp(self):
		paramlist = {'none':example_operation_noparams,
		             'one': example_operation_oneparam,
		             'two': example_operation_twoparam}
		self.interp = rpncalc.Interpreter(paramlist)

	def test_not_enough_operands0(self):
		try:
			self.interp.parse('none')
		except errors.NotEnoughOperands:
			self.fail("Raised a NotEnoughOperands exception when we should not have!")

	def test_not_enough_operands1(self):
			self.assertRaises(errors.NotEnoughOperands,self.interp.parse,'one')

	def test_not_enough_operands2(self):
			self.assertRaises(errors.NotEnoughOperands,self.interp.parse,'two')

			self.interp.parse('1')

			self.assertRaises(errors.NotEnoughOperands,self.interp.parse,'two')

class While(unittest.TestCase):
	def setUp(self):
		self.interp = rpncalc.Interpreter(rpncalc.ops)

	def test_break_outside_loop(self):
		self.interp.parse('break')
		self.assertEqual(self.interp.messages[0], 'Not in a loop, cannot break')

	def test_basic_countdown(self):
		self.interp.parse('5 [ dup 1 - dup 0 < ] while')
		result = [5, 4, 3, 2, 1, 0]
		result2 = [rpn_types.Value(i) for i in result]
		self.assertEqual(self.interp.stack, result2)

	def test_break(self):
		self.interp.parse('1 2 3 4 5 6 7 [ 4 >= [ 4 break ] if 1 ] while')
		result = [1, 2, 3, 4]
		result2 = [rpn_types.Value(i) for i in result]
		self.assertEqual(self.interp.stack, result2)

	
class Bulk(unittest.TestCase):
	def setUp(self):
		self.interp = rpncalc.Interpreter(rpncalc.ops)


	def test_start(self):
		self.assertEqual(self.interp.stack, [])

	def check_inline(self, test, result):
		self.interp.parse(test)
		self.assertEqual(str(self.interp.stack[0]), str(rpn_types.Value(result)))
		#self.assertEqual(self.interp.stack, [rpn_types.Value(result)])

	def check_function(self, test, result):
		self.interp.parse(test)
		self.assertEqual(str(self.interp.stack[0]), str(rpn_types.Value(result)))
		#self.assertEqual(self.interp.stack, [rpn_types.Value(result)])


bulk_tests = [('5 1 2 + 4 * + 3 -', 14),
              ('3 1 2 + *', 9),
              ('4 2 5 * + 1 3 2 * + /', 2),
	      ('9 5 3 + 2 4 ^ - +', 1),
	      ('6 4 5 + * 25 2 3 + / -', 49),
	      ('10 A = 20 B = + ', 30),
	      ('10 A = 20 B = + drop A int', 10),
	      ('10 A = 20 B = + drop B int', 20)]

test_id = 0
for test in bulk_tests:
	test_id += 1
	setattr(Bulk, "test_" + str(test_id), lambda self: self.check_inline(test[0], test[1]))
	setattr(Bulk, "testf_" + str(test_id), lambda self: self.check_function('[ ' + test[0] + ' ] !', test[1]))



if __name__ == '__main__':
	unittest.main()
