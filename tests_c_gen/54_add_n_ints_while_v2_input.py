n: int = input_int()
should_continue: bool = True
result: int = 0
while should_continue:
	tmp: int = input_int()
	result = result + tmp
	n = n - 1
	print(n)
	if n == 0:
		print(42)
		should_continue = False
print(result)
