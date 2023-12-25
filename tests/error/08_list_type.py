# Operator type error involving variable with inferred type
# Type Checker Error: Type mismatch on Binary Operator left=Type<int> right=Type<str>
s: str = 'hi'
for v in [1]:
	v = v + s
