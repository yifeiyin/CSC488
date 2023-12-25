n: int = input_int("How many number to add?")
result: int = 0
if n <= 0:
	print("You did not enter a positive number")

while n > 0:
	n = n - 1
	tmp: int = input_int()
	result = result + tmp

print("The sum is")
print(result)
