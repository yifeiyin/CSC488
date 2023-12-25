from __future__ import annotations
from typing import Union, List, Literal
from dataclasses import dataclass

class Node():
    pass

@dataclass
class PrimitiveType(Node):
    value: Literal['str', 'int', 'float', 'bool', 'none']

    def __init__(self, value):
        self.value = value
        assert value in ['str', 'int', 'float', 'bool', 'none']

    def __str__(self):
        return self.value

@dataclass
class NonPrimitiveType(Node):
    name: Union['tuple', 'list']
    value: PrimitiveType

    def __str__(self):
        return f'{self.name} of {str(self.value)}'

@dataclass
class Type(Node):
    value: Union[PrimitiveType, NonPrimitiveType]

    def __str__(self):
        return f"Type<{str(self.value)}>"

@dataclass
class Expression(Node):
    value: Union[BinaryOperation, UnaryOperation, Id, PrimitiveLiteral, NonPrimitiveLiteral]
               # Commented out because python wants them to be defined first, which results in a circular dependency

@dataclass
class PrimitiveLiteral(Node):
    name: Literal['str', 'int', 'float', 'bool', 'none']
    value: str

@dataclass
class NonPrimitiveLiteral(Node):
    name: Literal['tuple', 'list']
    children: List[Union[any, None]]

@dataclass(unsafe_hash=True)
class Id(Node):
    name: str

@dataclass
class BinaryOperation(Node): # Jat
    left: Expression
    operator: str
    right: Expression

@dataclass
class UnaryOperation(Node): # Jat
    operator: str
    right: Expression

@dataclass
class Assignment(Node): # Mostly done already
    left: Id
    type: Union[Type, None]
    right: Node

@dataclass
class IfStmt(Node): # Jat
    ifCond: Expression
    body: Block

@dataclass
class ElifStmt(Node): # Jat
    elifCond: Expression
    body: Block

@dataclass
class ElseStmt(Node): # Jat
    body: Block

@dataclass
class WhileStmt(Node): # Jat
    cond: Expression
    body: Block

@dataclass
class RangeValues(Node): # Yifei
    stop: Union[Expression, None]
    start: Union[Expression, None]
    step: Union[Expression, None]

@dataclass
class ForLoopRange(Node): # Yifei
    var: Id
    rangeVal: RangeValues
    body: Block

@dataclass
class ForLoopList(Node): # Yifei
    var: Id
    Lst: Expression
    body: Block

@dataclass
class Parameter(Node): # Jocob
    paramType: Type
    var: Id

@dataclass
class ParameterLst(Node): # Jocob
    lst: Union[List[Parameter], None]

@dataclass
class ArgumentLst(Node): # Jocob
    lst: Union[List[Expression], None]

@dataclass
class FunctionDef(Node): # Jocob
    name: Id
    lst: ParameterLst
    body: Block
    returnType: Union[Type, None]

@dataclass
class ReturnStmt(Node): # Jocob
    stmt: Expression


@dataclass
class FunctionCall(Node):
    name: Id
    lst: ArgumentLst

@dataclass
class Block(Node):
    lst: List[Union[FunctionDef, ReturnStmt, FunctionCall, ForLoopRange, ForLoopList, WhileStmt, \
                    IfStmt, ElifStmt, ElseStmt, Assignment]]

@dataclass
class LstAppend(Node):
    obj: Union[NonPrimitiveLiteral,Id]
    val: Expression

@dataclass
class NonPrimitiveIndex(Node):
    obj: Expression
    idx: Expression

@dataclass
class NonPrimitiveSlicing(Node):
    obj: Expression
    start: Union[Expression,None]
    end: Union[Expression,None]



