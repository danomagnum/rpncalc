#####################################################################################
#
# the builtin functions in math are C functions, so I can't introspect into their 
# function parameters.  So, I'll just hard code the quantity.  The dicts were
# created by copying the result of dir(math) out of a shell and trimming them.

import rpncalc
import math

def noparam_gen(constant):
	return lambda interp: [rpncalc.Value(math.__dict__[constant])]

noparam = ['e', 'pi']

def oneparam_gen(function):
	return lambda interp, a : [rpncalc.Value(math.__dict__[function](a.val))]

oneparam = ['acos',
            'acosh',
            'asin',
            'asinh',
            'atan',
            'atanh',
            'ceil',
            'cos',
            'cosh',
            'degrees',
            'erf',
            'erfc',
            'expm1',
            'fabs',
            'factorial',
            'floor',
            'frexp',
            'gamma',
            'isinf',
            'isnan',
            'lgamma',
            'log10',
            'log1p',
            'modf',
            'exp',
            'radians',
            'sin',
            'sinh',
            'sqrt',
            'tan',
            'tanh',
            'trunc']

def twoparam_gen(function):
	return lambda interp, a, b : [rpncalc.Value(math.__dict__[function](a.val, b.val))]

twoparam = ['copysign',
            'fmod',
            'ldexp',
            'log',
            'atan2',
            'hypot']

def register():
	result = {}
	for const in noparam:
		result['math.%s' % const] = noparam_gen(const)
	for func in oneparam:
		result['math.%s' % func] = oneparam_gen(func)
	for func in twoparam:
		result['math.%s' % func] = twoparam_gen(func)
	return result
