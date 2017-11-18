import rpncalc

def add(interp, b, a):
	comment = ''
	if a.comment and b.comment:
		comment = a.comment + '+' + b.comment
	return [rpncalc.Value(a.val + b.val, comment)]

def register():
	return {'add': add}
