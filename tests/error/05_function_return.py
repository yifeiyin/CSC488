# Incorrect type in assignment involving function return type
# Type Checker Error: Assignment type mismatch. RHS should be Type<str> instead of Type<int>.
def func() -> int:
	return 1

a: str = func()
