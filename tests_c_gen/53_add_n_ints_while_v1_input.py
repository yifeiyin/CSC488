n: int = input_int()
result: int = 0
while n > 0:
	tmp: int = input_int()
	result = result + tmp
	n = n - 1
print(result)
