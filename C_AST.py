from __future__ import annotations
from typing import Union, List, Literal
from dataclasses import dataclass
import json


@dataclass
class Type:
    value: Union[Literal['str_t', 'int_t', 'float_t', 'bool_t', 'none_t'],NonPrimitiveType]

    def __init__(self, value):
        if value.__class__.__name__ != 'NonPrimitiveType':
            assert value in ['str_t', 'int_t', 'float_t', 'bool_t', 'none_t']
        self.value = value



@dataclass
class NonPrimitiveType:
    type: Union['list', 'tuple']
    value: Type


@dataclass
class Id:
    name: str
    def __init__(self, name):
        assert isinstance(name, str), f"Got {name=}"
        self.name = name


@dataclass
class Declaration:
    id: Id
    type: Type


@dataclass
class UnaryOperation:
    left: Id
    type: Type
    operator: str
    operand: Id


@dataclass
class BinaryOperation:
    left: Id
    type: Type
    operator: str
    operand_a: Id
    operand_b: Id


@dataclass
class Parameter:
    paramType: Type
    var: Id


@dataclass
class ParameterLst:
    lst: List[Parameter]


@dataclass
class FunctionDeclaration:
    name: Id
    lst: ParameterLst
    body: Block
    returnType: Union[Type, None]


@dataclass
class IfStmt:
    ifCond: Id
    body: Block


@dataclass
class ElifStmt:
    elifCond: Id
    body: Block


@dataclass
class ElseStmt:
    body: Block


@dataclass
class WhileStmt:
    cond: Id
    body: Block


@dataclass
class RangeValues:
    stop: Union[Expression, None]
    start: Union[Expression, None]
    step: Union[Expression, None]


@dataclass
class ForLoopRange:
    var: Id
    rangeVal: RangeValues
    body: Block


@dataclass
class ForLoopList:
    var: Id
    indexVar : Id
    length : any
    Lst: Expression
    body: Block


@dataclass
class Expression:
    value: Union[BinaryOperation, UnaryOperation, Id]


@dataclass
class ArgumentLst:
    lst: Union[List[Expression], List[Id], None]


@dataclass
class ReturnStmt:
    stmt: Expression


@dataclass
class FunctionCall:
    name: Id
    lst: ArgumentLst


@dataclass
class Block:
    lst: List[Union[FunctionDeclaration, ReturnStmt, FunctionCall, ForLoopRange, ForLoopList, WhileStmt, \
                    IfStmt, ElifStmt, ElseStmt, BinaryOperation, UnaryOperation]]


@dataclass
class Assignment:
    id: Id
    val: any


@dataclass
class String:
    val: str
    len: int


@dataclass
class ReturnStatement:
    value: Id


@dataclass
class PrimitiveLiteral:
    id: Id
    type: Type
    value: any


@dataclass
class LstAdd:
    obj: Id
    value: any
    type: Type
    idx: Union[str, int]

@dataclass
class NonPrimitiveIndex:
    result: Id
    obj: Id
    type: Type
    idx: Id


@dataclass
class NonPrimitiveLiteral:
    head: Id
    type: NonPrimitiveType
    value: List[Union[Id, PrimitiveLiteral]]

@dataclass
class NonPrimitiveSlicing:
    result_reg: Id
    obj: Id
    start: Union[Id,None]
    end: Union[Id,None]
    type: NonPrimitiveType

class CCodeGenerator:
    def __init__(self):
        self.function_declarations = []
        self.function_definitions = []
        self.state_in_function_declaration = False
        self.temp_dict = {}
        self.temp_list_dict = {}
        self.generated_code = []
        self.decl_scope = [[]]
        self.list_type_dict = {}
        self.list_decl_dict = []
        self.list_len_dict = {}
        self.converted_str_lst = {}
        self.propagation = {} # [variable_value, scope_counter, state] state being whether the variable should be propgated or not
        self.scope_counter = 0

        self.is_inloop = False
        self.pre_run = False
        self.eval_mode = True  # Optimization flag
        self.variants = []
        self.var_dict = {}
        #self.var_dict = {'true':'true','false':'false','NONE_LITERAL':'NONE_LITERAL'}
        self.has_if_head = False
        self.ignore_if = False

    def generate_code(self, root):
        structure = self.gen(root)
        formatted = self.generate_code_formatter(structure)
        declarations_str, definitions_str = self.generate_function_code()
        return self.code_template(declarations_str, definitions_str, formatted)

    def generate_function_code(self):
        declarations_str = ";\n".join(self.function_declarations)
        if len(declarations_str) != 0: declarations_str += ';'
        definitions_str = ""
        for definition in self.function_definitions:
            formatted = self.generate_code_formatter(definition)
            definitions_str += formatted
        return declarations_str, definitions_str

    def generate_code_formatter(self, structure, indent=0):
        result = ""
        for line in structure:
            if line is None:
                continue
            if isinstance(line, tuple):
                code = self.generate_code_formatter(line, indent)
            elif isinstance(line, list):
                code = self.generate_code_formatter(line, indent + 1)
            else:
                code = "    " * indent + line + "\n"
            result += code
        for tmp in self.temp_list_dict.keys():
            var = self.temp_list_dict[tmp]
            if var != None:
                result = result.replace(tmp, var)
        return result

    def code_template(self, function_declarations, function_definitions, main_code):
        if len(function_declarations) == 0:
            function_code = ""
        else:
            function_code = f"""
/***** Function declarations *****/
{function_declarations}
/***** End of function declarations *****/

/***** Function definitions *****/
{function_definitions}
/***** End of function definitions *****/
        """.strip() + '\n'

        return f"""
#include "../starter.c"

{function_code}
int main() {{
/***** Main *****/
{main_code}
/***** End of main *****/

    str_clean_up();
    list_clean_up();

    return 0;
}}
        """.strip() + '\n'

    def gen(self, node):
        method = 'gen_' + node.__class__.__name__
        try:
            return getattr(self, method)(node)
        except AttributeError:
            print(f"Trying to process node {node}")
            raise

    def gen_Block(self, node: Block):
        result = []
        self.decl_scope.append([])
        self.scope_counter += 1
        for x in node.lst:
            code = self.gen(x)
            if code:
                if type(code) == str and code.find(";") != len(code[0]) -1:
                    code_group = code.split(';')
                    for c in code_group:
                        if c:
                            result.append(c+";")
                else:
                    result.append(code)
        self.decl_scope.pop()
        self.scope_counter -= 1
        return result

    def gen_Expression(self, node: Expression):
        return self.gen(node.value)

    def gen_Id(self, node: Id):
        return node.name

    def gen_Declaration(self, node: Declaration):
        type_t = self.gen(node.type)
        name = self.gen(node.id)
        if type_t == "list_t *":
            self.list_type_dict[name] = type_t
            return None
        if name[0] == '_':
            self.temp_dict[name] = None
            return None
        for scope in self.decl_scope:
            if name in scope:
                return None
        self.decl_scope[-1].append(name)
        return f"{type_t} {name};"

    def gen_Type(self, node: Type):
        if node.value.__class__.__name__ != "NonPrimitiveType":
            assert node.value in ['str_t', 'int_t', 'float_t', 'bool_t', 'str_t', 'none_t'], f"{node}"
            return node.value
        else:
            assert node.value.type in ['list', 'tuple']
            return "list_t *"

    def gen_UnaryOperation(self, node: UnaryOperation):
        left = self.gen(node.left)
        op = self.gen(node.operand)
        operator = self.convert_operator(node.operator)
        if self.eval_mode:
            if not self.pre_run:
                if left[0] == "_":
                    if op[0] == "_":
                        op = self.look_up_temp(op)
                    self.temp_dict[left] = f'({operator} {op})'
                else:
                    value = self._eval(node)
                    if node.type.value == "int_t" and isinstance(value,float):
                        value = int(value)
                    self.var_dict[left] = value
                    return f"({left} = {value});"
            elif left[0] != "_" and left not in self.variants:
                self.variants.append(left)
        else:
            if left[0] == "_":
                self.temp_dict[left] = f'({operator} {op})'
            else:
                return f"{self.gen(node.left)} = ({operator} {self.gen(node.operand)});"

    def gen_BinaryOperation(self, node: BinaryOperation):
        left = self.gen(node.left)
        operator = self.convert_operator(node.operator)
        op_a = self.get_val(self.gen(node.operand_a))
        op_b = self.get_val(self.gen(node.operand_b))
        if self.eval_mode:
            if not self.pre_run:
                if left[0] == "_":
                    op_a = self._eval(node.operand_a)
                    op_b = self._eval(node.operand_b)
                    if node.type.value == 'int_t':
                        if isinstance(op_a,float):
                            op_a = int(op_a)
                        if isinstance(op_b,float):
                            op_b = int(op_b)
                    if type(op_a) == type(op_b) == str and (('"' in op_a or 'input_str()' == op_a) and \
                                                            ('"' in op_b or 'input_str()' == op_b)):
                        self.temp_dict[left] = f'str_concat({op_a},{op_b})'
                        return
                    if node.type.value == 'int_t' and isinstance(op_a,(int,float,bool)) and isinstance(op_b,(int,float,bool)):
                        self.temp_dict[left] = int(eval(f'{op_a} {operator} {op_b}'))
                    elif node.type.value == 'float_t' and isinstance(op_a,(int,float,bool)) and isinstance(op_b,(int,float,bool)):
                        self.temp_dict[left] = float(eval(f'{op_a} {operator} {op_b}'))
                    else:
                        self.temp_dict[left] = f'({op_a} {operator} {op_b})'
                else:
                    value = self._eval(node)
                    if node.type.value == 'int_t' and isinstance(value,float):
                        value = int(value)
                    self.var_dict[left] = value
                    return f"{left} = {value};"
            elif left[0] != "_" and left not in self.variants:
                self.variants.append(left)
        else:
            value = f"({op_a} {operator} {op_b})"
            if left[0] == "_":
                self.temp_dict[left] = value
            else:
                return f"{left} = {value};"

    def gen_Parameter(self, node: Parameter):
        return f"{self.gen(node.paramType)} {self.gen(node.var)}"

    def gen_ParameterLst(self, node: ParameterLst):
        return ", ".join(self.gen(param) for param in node.lst)

    def gen_FunctionDeclaration(self, node: FunctionDeclaration):
        assert not self.state_in_function_declaration, "Cannot declare function inside of a function"
        function_declaration = f"{self.gen(node.returnType)} {self.gen(node.name)}({self.gen(node.lst)})"
        self.function_declarations.append(function_declaration)
        self.state_in_function_declaration = True
        self.function_definitions.append((
            function_declaration + " {",
            self.gen(node.body),
            "} " f"/* End of {self.gen(node.name)} */",
        ))
        self.state_in_function_declaration = False
        return None

    def gen_FunctionCall(self, node: FunctionCall):
        arg_list = []
        for i in node.lst:
            if i in self.temp_dict.keys():
                arg_list.append((str(self.temp_dict[i])))
            else:
                arg_list.append(i)
        arg_string = ", ".join(i for i in arg_list)
        return node.name + "(" + arg_string + ")"

    def gen_IfStmt(self, node: IfStmt):
        if self.eval_mode:
            eval_cond = self._eval(node.ifCond)
            if str(eval_cond) == 'False' or eval_cond == "false" or eval_cond == "NONE_LITERAL":
                self.has_if_head = False
                self.ignore_if = False
                return None
            else:
                self.has_if_head = True
                if not self.pre_run:
                    self.pre_run = True
                    self.gen(node.body)
                    for var in self.variants:
                        if var in self.propagation:
                            self.propagation[var][2] = False
                        self.var_dict[var] = var
                    self.pre_run = False
                body = self.gen(node.body)
                if not body:
                    return None
                if str(eval_cond) == 'True' or eval_cond == "true":
                    self.ignore_if = True
                    return "".join(body)
                return (
                    f"if ({eval_cond})" " {",
                    body,
                    "}",
                )
        else:
            eval_cond = self.get_val(self.gen(node.ifCond))
        return (
            f"if ({eval_cond})" " {",
            self.gen(node.body),
            "}",
        )

    def gen_ElifStmt(self, node: ElifStmt):
        if self.eval_mode:
            if self.ignore_if:
                return None
            eval_cond = self._eval(node.elifCond)
            if not self.pre_run:
                self.pre_run = True
                self.gen(node.body)
                for var in self.variants:
                    if var in self.propagation:
                        self.propagation[var][2] = False
                    self.var_dict[var] = var
                self.pre_run = False
            body = self.gen(node.body)
            if not body:
                return None
            if str(eval_cond) == 'False' or eval_cond == "false" or eval_cond == "NONE_LITERAL":
                return None
            else:
                if self.has_if_head:
                    return (
                        f"else if ({eval_cond})" " {",
                        body,
                        "}",
                    )
                elif str(eval_cond) == 'True' or eval_cond == "true":
                    self.has_if_head = True
                    self.ignore_if = True
                    return "".join(body)
                else:
                    return (
                        f"if ({eval_cond})" " {",
                        body,
                        "}",
                    )
        else:
            eval_cond = self.get_val(self.gen(node.elifCond))
        return (
            f"else if ({eval_cond})" " {",
            self.gen(node.body),
            "}",
        )

    def gen_ElseStmt(self, node: ElseStmt):
        if self.eval_mode:
            if not self.pre_run:
                self.pre_run = True
                self.gen(node.body)
                for var in self.variants:
                    if var in self.propagation:
                        self.propagation[var][2] = False
                    self.var_dict[var] = var
                self.pre_run = False
            body = self.gen(node.body)
            if self.ignore_if or not body:
                return None
            if not self.has_if_head:
                return "".join(body)
        return (
            "else {",
            self.gen(node.body),
            "}",
        )

    def gen_WhileStmt(self, node: WhileStmt):
        cond = self.get_val(self.gen(node.cond))
        if self.eval_mode:
            if not self.is_inloop:
                eval_cond = self._eval(node.cond)
                if str(eval_cond) == 'False' or eval_cond == "false":
                    return None
                self.is_inloop = True
                self.pre_run = True
                self.gen(node.body)
                self.pre_run = False
                for var in self.variants:
                    if var in self.propagation:
                        self.propagation[var][2] = False
                    self.var_dict[var] = var
                body = self.gen(node.body)
                if not body:
                    return None
                result = (f"while ({cond})" " {",
                      body,
                      "}",)
                self.variants = []
                self.is_inloop = False
                return result
            elif self.pre_run:
                self.gen(node.body)
                return None
            else:
                eval_cond = self._eval(node.cond)
                if eval_cond == False or eval_cond == "false":
                    return None
        return (
            f"while ({cond})" " {",
            self.gen(node.body),
            "}",
        )
    def gen_ForLoopRange(self, node: ForLoopRange):

        stop_val = node.rangeVal.stop
        step_val = node.rangeVal.step
        if stop_val in self.temp_dict.keys():
            stop_val = self.get_temp_val(stop_val)
        if step_val in self.temp_dict.keys():
            step_val = self.get_temp_val(step_val)
        assign_string = self.gen_Assignment(Assignment(id=node.var, val=node.rangeVal.start))
        comp_string = f"{node.var.name} < {stop_val};"
        step_string = f"{node.var.name} += {step_val}"
        if self.eval_mode:
            ranges = self._eval(node.rangeVal)
            if type(ranges[0]) == type(ranges[2]) == int and  ranges[0] >= ranges[2]:
                return None
            if not self.is_inloop:
                self.is_inloop = True
                self.pre_run = True
                self.gen(node.body)
                self.pre_run = False
                for var in self.variants:
                    if var in self.propagation:
                        self.propagation[var][2] = False
                    self.var_dict[var] = var
                body = self.gen(node.body)
                if not body:
                    return None
                result = (
                    "for (" + assign_string + " " + comp_string + " " + step_string + "){",
                    body,
                    "}",
                )
                self.variants = []
                self.is_inloop = False
                return result
            elif self.pre_run:
                self.gen(node.body)
                return None
        return (
               "for (" + assign_string + " " + comp_string + " " + step_string + "){",
               self.gen(node.body),
               "}",
        )

    def gen_ForLoopList(self, node: ForLoopList):
        idx = self.get_val(node.indexVar.name)
        assign_var = self.get_val(node.var.name)
        lst = self.get_val(node.Lst.name)
        assign_string = f"int_t i = 0;"
        comp_string = f"i < {node.length};"
        step_string = f"i += {idx}"
        self.var_dict["i"] = 0
        if self.eval_mode:
            if not self.is_inloop:
                self.is_inloop = True
                self.pre_run = True
                self.gen(node.body)
                self.pre_run = False
                for var in self.variants:
                    if var in self.propagation:
                        self.propagation[var][2] = False
                    self.var_dict[var] = var
                body = self.gen(node.body)
                if not body:
                    return None
                result = (
                    "for (" + assign_string + " " + comp_string + " " + step_string + "){",
                    [f"{assign_var} = list_get(int_v, {lst}, i);"],
                    body,
                    "}",
                )
                self.variants = []
                self.is_inloop = False
                return result
            elif self.pre_run:
                self.gen(node.body)
                return None
        return (
               "for (" + assign_string + " " + comp_string + " " + step_string + ") {",
               [f"{assign_var} = list_get(int_v, {lst}, i);"],
               self.gen(node.body),
               "}",
        )

    def gen_Assignment(self, node: Assignment):
        assign_var = self.gen(node.id)
        result = None
        temp_var = False
        if assign_var in self.temp_dict.keys():
            temp_var = True

        if isinstance(assign_var, str) and assign_var[0] == '_':
            self.temp_dict[assign_var] = None
            temp_var = True
        if not self.pre_run:
            if isinstance(node.val, (Id, FunctionCall, String)):
                assign_value = self.gen(node.val)
                if isinstance(node.val, String):
                    self.converted_str_lst[assign_var] = assign_value
                if temp_var:
                    self.temp_dict[assign_var] = assign_value
                    if isinstance(node.val, FunctionCall) and node.val.name[:6] == "print_":
                        return f"{assign_value};"
                    return None

                elif assign_value in self.temp_dict.keys():
                    assign_value = self.get_temp_val(assign_value)

                elif assign_value in self.temp_list_dict.keys():
                    self.temp_list_dict[assign_value] = assign_var
                    return None

                # MARK
                assign_value = self.get_prop_val(assign_value)
                self.set_prop_val(assign_var, assign_value)
                result = f"{assign_var} = {assign_value};"

            elif isinstance(node.val, bool):
                assign_value = str(node.val).lower()
                if temp_var:
                    self.temp_dict[assign_var] = assign_value
                    return None
                elif assign_value in self.temp_dict.keys():
                    assign_value = self.get_temp_val(assign_value)
                elif assign_value in self.temp_list_dict.keys():
                    self.temp_list_dict[assign_value] = assign_var
                    return None
                assign_value = self.get_prop_val(assign_value)
                self.set_prop_val(assign_var, assign_value)
                result = f"{assign_var} = {assign_value};"
            elif node.val == "none-placeholder":
                if temp_var:
                    self.temp_dict[assign_var] = "NONE_LITERAL"
                    return None
                self.set_prop_val(assign_var, "NONE_LITERAL")
                result = f"{assign_var} = NONE_LITERAL;"
            else:
                assign_value = node.val
                if temp_var:
                    self.temp_dict[assign_var] = assign_value
                    return None
                elif assign_value in self.temp_dict.keys():
                    assign_value = self.get_temp_val(assign_value)
                elif assign_value in self.temp_list_dict.keys():
                    self.temp_list_dict[assign_value] = assign_var
                    self.list_len_dict[assign_var] = self.list_len_dict[assign_value]
                    return None
                if (assign_value in self.temp_list_dict.values() or assign_value in self.list_decl_dict or \
                    (type(assign_value) == str and "list_slice" in assign_value)) and\
                        assign_var not in self.temp_list_dict.values():
                    if assign_var not in self.list_decl_dict:
                        self.list_decl_dict.append(assign_var)
                        type_t = self.list_type_dict[assign_var]
                        if "list_slice" in assign_value:
                            params = assign_value.split("(")[1].split(")")[0].split(",")
                            self.list_len_dict[assign_var] = eval(f"{params[2]}-{params[1]}")
                        else:
                            self.list_len_dict[assign_var] = self.list_len_dict[assign_value]
                        return "".join([f"{type_t} {assign_var};", f"{assign_var} = {assign_value}"])
                assign_value = self.get_prop_val(assign_value)
                self.set_prop_val(assign_var, assign_value)
                result = f"{assign_var} = {assign_value}"
        if not temp_var and assign_var not in self.variants:
            if self.pre_run:
                self.variants.append(assign_var)
            else:
                if type(node.val) == str and node.val != '_':
                    value = self._eval(node)
                    self.var_dict[assign_var] = value
                    result = f"{assign_var} = {value};"
                else:
                    self.var_dict[assign_var] = assign_value
        return result

    def gen_String(self, node: String):
        # Using json.dumps to do string escape
        import json
        return json.dumps(node.val)

    def gen_ReturnStatement(self, node: ReturnStatement):
        assert self.state_in_function_declaration, "Cannot have return statement outside of a function declaration"
        value = self.get_val(self.gen(node.value))
        return f"return {value};"

    def gen_LstAdd(self, node: LstAdd):
        obj = self.gen(node.obj)
        type_t = self.gen(node.type)
        type_t = type_t[:-1] + "v"
        value = self.get_val(self.gen(node.value))
        value = self.get_prop_val(value)
        if node.idx == 'end':
            return f"list_add({type_t}, {obj}, {value});"

    def gen_NonPrimitiveIndex(self, node: NonPrimitiveIndex):
        idx_reg = self.gen(node.result)
        idx = self.gen(node.idx)
        type_v = self.convert_v_type(node.type)
        if idx in self.temp_dict:
            idx = self.get_temp_val(idx)
        if idx_reg[0] == "_":
            self.temp_dict[idx_reg] = f"list_get({type_v},{self.gen(node.obj)},{idx})"
        else:
            return f"{self.gen(node.result)} = list_get({type_v},{self.gen(node.obj)},{idx})"

    def gen_NonPrimitiveLiteral(self, node: NonPrimitiveLiteral):
        head = self.gen(node.head)
        if isinstance(head, str) and head[0] == '_':
            self.temp_list_dict[head] = None
        init = [f"list_t * {head} = list_init({len(node.value)});"]
        val_type = self.convert_v_type(node.type)
        for item in node.value:
            value = self.get_val(self.gen(item))
            value = self.get_prop_val(value)
            init.append(f"list_init_add({val_type},{self.gen(node.head)},{value});")
        self.list_len_dict[head] = len(node.value)
        return "".join(init)

    def gen_NonPrimitiveSlicing(self, node: NonPrimitiveSlicing):
        obj = self.gen(node.obj)
        result_reg = self.gen(node.result_reg)
        if node.start:
            start = self.get_val(self.gen(node.start))
        else:
            start = 0
        if node.end:
            end = self.get_val(self.gen(node.end))
        else:
            end = self.list_len_dict[obj]
        result = f"list_slice({obj},{start},{end})"
        self.temp_dict[result_reg] = result
        return None

    def convert_v_type(self,node: Type):
        if isinstance(node.value, str):
            assert node.value in ['str_t', 'int_t', 'float_t', 'bool_t', 'str_t', 'none_t']
            return node.value.replace('_t', '_v')
        elif not isinstance(node.value, NonPrimitiveType):
            assert node.value.value.value in ['str_t', 'int_t', 'float_t', 'bool_t', 'str_t', 'none_t']
            return node.value.value.value.replace('_t', '_v')
        elif not isinstance(node.value, Type):
            assert node.value.value.value in ['str_t', 'int_t', 'float_t', 'bool_t', 'str_t', 'none_t']
            return node.value.value.value.replace('_t', '_v')
        else:
            return 'list_v'

    def get_temp_val(self, tmp):
        if tmp in self.temp_dict.keys():
            return self.get_temp_val(self.temp_dict[tmp])
        return tmp

    def get_val(self,name):
        if name[0] == "_":
            return self.get_temp_val(name)
        return name
    # set progagation dictionary for the variable and value
    def set_prop_val(self, name, val):
        if name in self.propagation.keys():
            prop = self.propagation[name]
            if not prop[2]: # Don't set variable if the variable state is not 
                return None
            if self.scope_counter > prop[1]: # if the variable is being assigned in a if statement, while loop etc, the variable should not continue to propogate
                prop[2] = False
                return None
        if isinstance(val, (bool,int,float)) or val == "NONE_LITERAL":
            self.propagation[name] = [val, self.scope_counter, True]

    def get_prop_val(self, name):
        if self.eval_mode and name in self.propagation.keys():
            prop = self.propagation[name]
            if prop[2]: # 
                return prop[0]
        return name

    def _eval(self, node):
        method = 'eval_' + node.__class__.__name__
        try:
            return getattr(self, method)(node)
        except AttributeError:
            return node

    def convert_operator(self, op):
        if op == "and" or op == "&":
            return "&&"
        elif op == "or" or op == "|":
            return "||"
        elif op == "not":
            return "!"
        return op
    def look_up_temp(self, temp_reg):
        cur_val = temp_reg
        while cur_val != None:
            prev = cur_val
            cur_val = self.temp_dict.get(cur_val)
        return prev

    def eval_BinaryOperation(self, node: BinaryOperation):
        left = self._eval(node.operand_a)
        right = self._eval(node.operand_b)
        left = self.get_prop_val(left)
        right = self.get_prop_val(right)
        operator = self.convert_operator(node.operator)
        if self.gen(node.left) not in self.variants and isinstance(left, (bool, int, float))\
                and isinstance(right, (bool, int, float)):
            temp_dict = self.var_dict.copy()
            for var in self.variants:
                temp_dict.pop(var,None)
            if node.type.value == "int_t":
                return int(eval(f"{left} {operator} {right}",temp_dict))
            return eval(f"{left} {operator} {right}",temp_dict)
        return f"{left} {operator} {right}"

    def eval_UnaryOperation(self, node: UnaryOperation):
        operand = self._eval(node.operand)
        operator = self.convert_operator(node.operator)
        if self.gen(node.left) not in self.variants:
            temp_dict = self.var_dict.copy()
            for var in self.variants:
                temp_dict.pop(var,None)
            operand = self.get_prop_val(operand)
            if node.type.value == "int_t":
                return int(eval(f"{operator} {operand}",temp_dict))
            return eval(f"{operator} {operand}",temp_dict)
        return f"{operator} {operand}"

    def eval_Id(self, node: Id):
        if node.name[0] == "_":
            expr = self.look_up_temp(node.name)
            try:
                if node.name in self.converted_str_lst:
                    return self.converted_str_lst[node.name]
                temp_dict = self.var_dict.copy()
                for var in self.variants:
                    temp_dict.pop(var,None)
                result = eval(f"{expr}",temp_dict)
                if type(result) == str and result not in self.var_dict:
                    import json
                    result = json.dumps(result)
                    self.converted_str_lst[node.name] = result
                    return result
            except:
                result = expr
            return result
        else:
            if node.name not in self.variants and node.name in self.var_dict:
                return self.var_dict[node.name]
        return node.name

    def eval_PrimitiveLiteral(self,node:PrimitiveLiteral):
        return node.value

    def eval_FunctionCall(self,node:FunctionCall):
        return self.gen(node)

    def eval_Assignment(self,node:Assignment):
        expr = self.look_up_temp(node.val)
        name = self.gen(node.id)
        try:
            if node.val in self.converted_str_lst:
                result = self.converted_str_lst[node.val]
                self.converted_str_lst[name] = result
                return result
            temp_dict = self.var_dict.copy()
            for var in self.variants:
                temp_dict.pop(var,None)
            result = eval(f"{expr}", temp_dict)
            if type(result) == str and result not in self.var_dict:
                result = json.dumps(result)
                self.converted_str_lst[name] = result
                return json.dumps(result)
        except:
            result = expr
        return result

    def eval_RangeValues(self,node:RangeValues):
        start = self.look_up_temp(node.start)
        step = self.look_up_temp(node.step)
        stop = self.look_up_temp(node.stop)
        return [eval(f"{start}",self.var_dict),eval(f"{step}",self.var_dict),eval(f"{stop}",self.var_dict)]
