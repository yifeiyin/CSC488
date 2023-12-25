sa: str = "Hello, "
sb: str = "World"
sc: str = "!"
s: str = sa + sb + sc

ia: int = -10
ib: int = -0
fa: float = -10.0
fb: float = -0.0
bt: bool = True
bf: bool = False
nn: None = None

o1: int = ib * ia
o2: int = ib / ia
o3: int = ib + ia
o4: int = ib - ia
o5: int = -ia

o11: float = fb * fa
o12: float = fb / fa
o13: float = fb + fa
o14: float = fb - fa

o21: bool = bt and bf
o22: bool = bt & bf
o23: bool = bt or bf
o24: bool = bt | bf
o25: bool = not bf

o31: int = 1 + 2 * 3 / 4 - 5
o32: int = 1 + 2 * 3 / (4 - 5)
o33: int = (1 + 2 * 3) / (4 - 5)

o41: float = 1.0 + 2.2 * 3.1 / 4.8 - 5.0
o42: float = 1.0 + 2.2 * 3.1 / (4.8 - 5.0)
o43: float = (1.0 + 2.2 * 3.1) / (4.8 - 5.0)

o51: bool = True and False or True
o52: bool = True or False and True
o53: bool = True and (False or True)
o54: bool = (True or False) and True
o55: bool = (True and False) or True
o56: bool = True or (False and True)
