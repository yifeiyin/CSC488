a: [int] = [1,2,3]
b: [float] = [1.0,2.0,3.0]
c: [int] = []

result1: int = 0
for v in a:
	result1 = result1 + v

result2: float = 0.0
for w in b:
	result2 = result2 + w

for v in [1,2,3]:
	result1 = result1 + v

for w in [1.0,2.0,3.0]:
	result2 = result2 + w

for i in range(20):
	result1 = result1 + i

for i in range(-20, 20):
	result1 = result1 + i

for i in range(-20, 20, 4):
	result1 = result1 + i
