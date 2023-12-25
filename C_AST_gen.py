import C_AST
from ir_gen import *
from symbol_table import SymbolTable
from typing import List
from AST import Type as A_Type, NonPrimitiveType


class CASTGenerator:
    def __init__(self):
        self.seen_labels = []  # Labels have seen
        self.waiting_labels = []  # Labels have not seen
        self.temp_st = SymbolTable()  # Keep track of declared variables
        self.result_AST = []
        self.end_if_labels = []  # value is a tuple (label name, head of if)
        self.current_str = None
        self.current_str_count = 0
        self.argument_list_stack = []
        self.argument_list_dict = {}
        # For loop variables
        self.loop_start = None
        self.loop_stop = None
        self.loop_step = None

        self.list_len = {}
        self.get_length = {}
        self.empty_non_prim = []



    def generate_AST(self, ir, st=None):
        self.ir = ir[:]
        while self.ir:
            ir_line = self.ir.pop(0)
            generated_line = self.gen(ir_line, st)
            if generated_line != None:
                self.result_AST += generated_line
        return C_AST.Block(self.result_AST)

    def gen(self, ir_line, st=None):
        method = 'gen_' + ir_line.__class__.__name__
        try:
            return getattr(self, method)(ir_line, st)
        except AttributeError:
            print(f"Trying to process ir {ir_line}")
            raise

    def gen_IR_Label(self, ir_node: IR_Label, st=None):
        if "FORRANGE" in ir_node.value:
            # do something for FOR
            #pass
            return self._gen_IR_For_Range(self.ir.pop(0), st)
        elif "FORLIST" in ir_node.value:
            return self._gen_IR_For_List(self.ir.pop(0), st)
        elif "WHILE" in ir_node.value:
            # do something for WHILE
            return self._gen_IR_While(self.ir.pop(0), st)
        elif 'FUNC' in ir_node.value:
            # This is a function, we need the label at the top of waiting
            # to find the end of declaration
            # Based on our Function IR, return statement is required.
            # Also, assume functions are declared in global scope
            end_func_idx = ir_node.value.rfind("_")
            return self._gen_IR_Func(self.ir.pop(0), ir_node.value[7:end_func_idx], st)
        else:
            # other cases
            return ir_node.value

    def gen_IR_Goto(self, ir_node: IR_Goto, st=None):
        if ir_node.label not in self.seen_labels:
            # If label not in seen, it means the following code is in a block
            self.waiting_labels.append(ir_node.label)
        return []

    def gen_IR_PrimitiveLiteral(self, ir_node: IR_PrimitiveLiteral, st=None):
        ''' All primitive literal are assigned to register'''
        type_val = type(ir_node.val)
        # String is not represented as primitive literal in IR
        if type_val == int:
            type_val = 'int_t'
        elif type_val == float:
            type_val = "float_t"
        elif type_val == str and ir_node.val == 'none-placeholder':
            type_val = "none_t"
        elif type_val == bool:
            type_val = "bool_t"
        else:
            assert False, f"Unexpected type_val {type_val} for {ir_node}"

        # Primitive Literal Reg will not be assigned again
        self.temp_st.declare_variable(name=ir_node.reg, type=C_AST.Type(value=type_val))
        id_node = C_AST.Id(name=ir_node.reg)
        decl_node = C_AST.Declaration(id=id_node, type=C_AST.Type(value=type_val))
        return [decl_node, C_AST.Assignment(id=id_node, val=ir_node.val)]

    def gen_IR_BinaryOperation(self, ir_node: IR_BinaryOperation, st=None):
        result_node = C_AST.Id(name=ir_node.result_reg)
        left_node = C_AST.Id(name=ir_node.left_reg)
        right_node = C_AST.Id(name=ir_node.right_reg)
        if ir_node.result_reg not in self.temp_st.scope_stack[-1]:
            # need assignment
            # should we consider string here?
            if ir_node.operator in ["<", "<=", "=>", ">", "=="]:
                type_t = 'bool_t'
            else:
                operand_t = [self.temp_st.lookup_variable(ir_node.left_reg).value,
                             self.temp_st.lookup_variable(ir_node.right_reg).value]
                if 'float_t' in operand_t:
                    type_t = 'float_t'
                elif 'str_t' in operand_t:
                    type_t = 'str_t'
                else:
                    type_t = 'int_t'
            self.temp_st.declare_variable(name=ir_node.result_reg, type=C_AST.Type(value=type_t))
            operation_node = C_AST.BinaryOperation(left=result_node,
                                                   type=C_AST.Type(type_t),
                                                   operator=ir_node.operator,
                                                   operand_a=left_node,
                                                   operand_b=right_node)
            decl_node = C_AST.Declaration(id=result_node, type=C_AST.Type(value=type_t))
            return [decl_node, operation_node]
        else:
            type_t = self.temp_st.lookup_variable(ir_node.result_reg)
            operation_node = C_AST.BinaryOperation(left=result_node,
                                                   type=C_AST.Type(type_t),
                                                   operator=ir_node.operator,
                                                   operand_a=left_node,
                                                   operand_b=right_node)
        return [operation_node]

    def gen_IR_UnaryOperation(self, ir_node: IR_UnaryOperation, st=None):
        result_node = C_AST.Id(name=ir_node.result_reg)
        operand_node = C_AST.Id(name=ir_node.operand_reg)
        if ir_node.result_reg not in self.temp_st.scope_stack[-1]:
            if ir_node.operator == "!":
                type_t = "bool_t"
            else:
                type_t = self.temp_st.lookup_variable(ir_node.operand_reg).value
            decl_node = C_AST.Declaration(id=result_node, type=C_AST.Type(value=type_t))
            self.temp_st.declare_variable(ir_node.result_reg,C_AST.Type(type_t))
            operation_node = C_AST.UnaryOperation(left=result_node,type=C_AST.Type(type_t), operator=ir_node.operator, operand=operand_node)
            return [decl_node, operation_node]
        else:
            type_t = self.temp_st.lookup_variable(ir_node.result_reg)
            operation_node = C_AST.UnaryOperation(left=result_node,type=C_AST.Type(type_t),operator=ir_node.operator, operand=operand_node)
        return [operation_node]

    def gen_IR_FunctionCall(self, ir_node: IR_FunctionCall, st=None):
        args = self.argument_list_dict[ir_node.reg]
        arg_types = []
        for arg in args:
            arg_types.append(self.temp_st.lookup_variable(arg))

        c_name, type_val = self.temp_st.get_C_function(ir_node.name, arg_types)

        function_call_node = C_AST.FunctionCall(name=c_name, lst=args)

        # Assume return types are PrimitiveType
        if type_val.value.value == 'int':
            type_val = 'int_t'
        elif type_val.value.value == 'float':
            type_val = 'float_t'
        elif type_val.value.value == 'bool':
            type_val = 'bool_t'
        elif type_val.value.value == 'str':
            type_val = 'str_t'
        elif type_val.value.value == 'none':
            type_val = 'none_t'
        else:
            assert False, f"{type_val=}"
        # return always immediately follows the function call
        ret_reg = self.gen(self.ir.pop(0))
        self.temp_st.declare_variable(name=ret_reg, type=C_AST.Type(value=type_val))
        id_node = C_AST.Id(name=ret_reg)
        decl_node = C_AST.Declaration(id=id_node, type=C_AST.Type(value=type_val))

        return [decl_node, C_AST.Assignment(id=id_node, val=function_call_node)]

    def gen_IR_FunctionReturn(self, ir_node: IR_FunctionReturn, st=None):
        return ir_node.reg

    def gen_IR_ReturnStmt(self, ir_node: IR_ReturnStmt, st=None):
        return [C_AST.ReturnStatement(value=C_AST.Id(ir_node.reg))]

    def gen_IR_IfStmt(self, ir_node: IR_IfStmt, st=None):
        false_label = ir_node.if_false.label
        idx = 0
        prev_node = None
        next_node = self.ir[idx]
        # if next node is not label or not the false label, then it is in body
        while not (next_node.__class__.__name__ == 'IR_Label' and next_node.value == false_label):
            idx += 1
            prev_node = next_node
            next_node = self.ir[idx]
        # based on the if stmt structure in IR, the end of if label must be before false label
        self.end_if_labels.append([prev_node.label, 0])
        if_node = C_AST.IfStmt(ifCond=C_AST.Id(name=ir_node.cond_reg), body=C_AST.Block([]))
        # signal is set to false when reaching the false label
        continue_sig = True
        while continue_sig:
            node = self.ir.pop(0)
            val = self.gen(node, st)
            if val and val == false_label:
                continue_sig = False
            elif val:
                if_node.body.lst += val
        # call elif to check if we have following elif
        if_stmt = self._gen_IR_ElifStmt(self.ir.pop(0), [if_node], st)
        return if_stmt

    def _gen_IR_ElifStmt(self, ir_node: any, if_stmt=None, st=None):
        idx = 0
        prev_node = None
        next_node = ir_node
        continue_sig = True
        while not (next_node.__class__.__name__ == 'IR_ElifStmt' or \
                   (next_node.__class__.__name__ == 'IR_Label' and next_node.value == self.end_if_labels[-1][0])):
            # it has to reach one of the condition without reaching the end of ir
            prev_node = next_node
            next_node = self.ir[idx]
            idx += 1
        if next_node.__class__.__name__ == 'IR_Label':
            # if stmts is empty, there is not trailing if statements
            if not prev_node:
                self.end_if_labels.pop()
                return if_stmt
            result_stmt = C_AST.ElseStmt(body=C_AST.Block([]))
            cur_node = ir_node
            while continue_sig:
                val = self.gen(cur_node, st)
                if val and val == self.end_if_labels[-1][0]:
                    continue_sig = False
                elif val:
                    result_stmt.body.lst += val
                if continue_sig:
                    cur_node = self.ir.pop(0)
        else:
            # reach elif, stmts are the conditional expression, need to be inserted before if head`
            cond_ast = []
            cur_node = ir_node
            while cur_node.__class__.__name__ != 'IR_ElifStmt':
                temp_val = self.gen(cur_node,st)
                if temp_val:
                    cond_ast += temp_val
                cur_node = self.ir.pop(0)
            if_stmt = if_stmt[:self.end_if_labels[-1][1]] + cond_ast + if_stmt[self.end_if_labels[-1][1]:]
            self.end_if_labels[-1][1] += len(cond_ast)
            result_stmt = C_AST.ElifStmt(elifCond=C_AST.Id(cur_node.cond_reg), body=C_AST.Block([]))
            false_label = next_node.elif_false.label
            while continue_sig:
                node = self.ir.pop(0)
                val = self.gen(node, st)
                if val and val == false_label:
                    continue_sig = False
                elif val:
                    result_stmt.body.lst += val
        if_stmt.append(result_stmt)
        if result_stmt.__class__.__name__ == "ElseStmt":
            self.end_if_labels.pop()
            return if_stmt
        if_stmt = self._gen_IR_ElifStmt(self.ir.pop(0), if_stmt, st)
        return if_stmt

    def gen_IR_Assignment(self, ir_node: IR_Assignment, st=None):
        id_node = C_AST.Id(name=ir_node.name)
        stmt_node = C_AST.Assignment(id=id_node, val=ir_node.val)
        if ir_node.name not in self.temp_st.scope_stack[-1]:
            try:
                type_t = self.temp_st.lookup_variable(name=ir_node.val)
            except Exception:
                id_type = st.lookup_variable(ir_node.name)
                assert isinstance(id_type.value, NonPrimitiveType), f"Referencing undefined ir variable {ir_node.val}"
            # Assume all non primitives will eventually be assigned to a value
            if type_t.value.__class__.__name__ == 'NonPrimitiveType':
                try:
                    id_type = st.lookup_variable(ir_node.name)
                    type_t = self.convert_NonPrimitive_Type(id_type)
                except:
                    # if it is not in global scope, then we will need to manually match
                    type_t = type_t.value
                self.list_len[ir_node.name] = self.list_len.get(ir_node.val)
                if ir_node.val not in self.list_len:
                    Exception(f'C_AST_Gen Error: {ir_node.name} is not previously defined as non-primitive')
                while self.empty_non_prim:
                    obj = self.empty_non_prim.pop()
                    obj.type = C_AST.Type(type_t)
                    self.temp_st.update_variable(name=obj.head.name,type=C_AST.Type(type_t))
            else:
                type_t = type_t.value
            self.temp_st.declare_variable(name=ir_node.name, type=C_AST.Type(type_t))
            decl_node = C_AST.Declaration(id=id_node, type=C_AST.Type(type_t))
            return [decl_node, stmt_node]
        return [stmt_node]

    def gen_IR_GetLength(self, ir_node:IR_GetLength, st=None):
        length = self.list_len.get(ir_node.pointer_reg)
        if length is None:
            raise Exception(f'C_AST_Gen Error: {ir_node.pointer_reg} is not previously defined as non-primitive')
        self.get_length[length] = ir_node.pointer_reg
        # return self.gen_IR_Assignment(IR_Assignment(name=ir_node.result_reg, val=length))
        return None

    def gen_IR_List(self, ir_node: IR_List, st=None):
        head = C_AST.Id(name=ir_node.reg)
        length = ir_node.length
        lst = []
        val_type = None
        continue_sig = True
        decl_stmt = []
        while continue_sig and length > 0:
            cur_node = self.ir.pop(0)
            if cur_node.__class__.__name__ == "IR_List_VAL":
                lst.append(C_AST.Id(cur_node.reg))
                length -= 1
            else:
                val = self.gen(cur_node, st)
                if not val_type:
                    val_type = self.temp_st.lookup_variable(cur_node.reg)
                decl_stmt += val
            if length == 0:
                continue_sig = False
        if ir_node.operator == 'LIST':
            type_t = C_AST.Type(C_AST.NonPrimitiveType(type='list',value=val_type))
        else:
            type_t = C_AST.Type(C_AST.NonPrimitiveType(type='tuple',value=val_type))
        self.temp_st.declare_variable(ir_node.reg,type_t)
        self.list_len[ir_node.reg] = ir_node.length
        result = C_AST.NonPrimitiveLiteral(head=head,type = type_t,value=lst)
        if not val_type:
            self.empty_non_prim.append(result)
        return decl_stmt+[result]

    def gen_IR_LoopStart(self, ir_node: IR_LoopStart, st=None):
        self.temp_st.declare_variable(name=ir_node.reg, type=C_AST.Type("int_t"))
        id_node = C_AST.Id(name=ir_node.reg)
        decl_node = C_AST.Declaration(id=id_node, type=C_AST.Type("int_t"))
        assign = C_AST.Assignment(id=id_node, val=ir_node.val)
        self.loop_start = ir_node.reg
        return [decl_node, assign]

    def gen_IR_LoopStop(self, ir_node: IR_LoopStop, st=None):
        self.temp_st.declare_variable(name=ir_node.reg, type=C_AST.Type("int_t"))
        id_node = C_AST.Id(name=ir_node.reg)
        decl_node = C_AST.Declaration(id=id_node, type=C_AST.Type("int_t"))
        assign = C_AST.Assignment(id=id_node, val=ir_node.val)
        self.loop_stop = ir_node.reg
        return [decl_node, assign]

    def gen_IR_LoopStep(self, ir_node: IR_LoopStep, st=None):
        self.temp_st.declare_variable(name=ir_node.reg, type=C_AST.Type("int_t"))
        id_node = C_AST.Id(name=ir_node.reg)
        decl_node = C_AST.Declaration(id=id_node, type=C_AST.Type("int_t"))
        assign = C_AST.Assignment(id=id_node, val=ir_node.val)
        self.loop_step = ir_node.reg
        return [decl_node, assign]

    def gen_IR_String(self,ir_node:IR_String,st=None):
        self.current_str = C_AST.String(val="", len=ir_node.length)
        self.current_str_count = 0

        type_val = "str_t"
        self.temp_st.declare_variable(name=ir_node.reg, type=C_AST.Type(value=type_val))
        id_node = C_AST.Id(name=ir_node.reg)
        decl_node = C_AST.Declaration(id=id_node, type=C_AST.Type(value=type_val))
        return [decl_node, C_AST.Assignment(id=id_node, val=self.current_str)]

    def gen_IR_String_char(self,ir_node:IR_String_char,st=None):
        self.current_str.val = self.current_str.val + ir_node.val
        self.current_str_count += 1
        if self.current_str_count == self.current_str.len:
            self.current_str_count = 0
            self.current_str = None
        return None

    def gen_IR_Parameter_VAL(self, ir_node: IR_Parameter_VAL, st=None):
        return ir_node.name

    def gen_IR_Argument(self, ir_node: IR_Argument, st=None):
        self.argument_list_stack.append([ir_node.function_call_reg, ir_node.length])
        self.argument_list_dict[ir_node.function_call_reg] = []
        return None

    def gen_IR_Argument_VAL(self, ir_node: IR_Argument_VAL, st=None):
        current_function_call = self.argument_list_stack[-1]
        self.argument_list_dict[current_function_call[0]].append(ir_node.reg)
        if(len(self.argument_list_dict[current_function_call[0]]) == current_function_call[1]):
            self.argument_list_stack.pop()
        return None

    def _gen_IR_Func(self, ir_node: IR_Parameter, func_name: str, st: SymbolTable):
        params = []
        param_regs = []
        # get params
        length = ir_node.length
        for i in range(length):
            cur_node = self.ir.pop(0)
            val = self.gen(cur_node)
            params.append(val)
            param_regs.append(cur_node.reg)
        types = st.get_func_by_name(func_name, params)
        # convert param types to C types
        converted_types = self.convert_types(types[0])
        converted_ret_type = self.convert_types([types[1]])[0]
        # add hashed number after function name
        hash_name = self.temp_st.declare_C_function(func_name, converted_types, types[1])
        self.temp_st.push_scope()
        param_lst = C_AST.ParameterLst([])
        for i in range(len(params)):
            param_lst.lst.append(C_AST.Parameter(var=params[i], paramType=converted_types[i]))
            self.temp_st.declare_variable(params[i].name, converted_types[i])
            self.temp_st.declare_variable(param_regs[i], converted_types[i])
        func_node = C_AST.FunctionDeclaration(name=C_AST.Id(hash_name), lst=param_lst, body=C_AST.Block([]), \
                                              returnType=converted_ret_type)
        continue_sig = True
        #  get function body
        while continue_sig:
            cur_node = self.ir.pop(0)
            val = self.gen(cur_node, st)
            # check if reached the end of function
            if val and val == self.waiting_labels[-1]:
                self.seen_labels.append(self.waiting_labels.pop())
                continue_sig = False
            elif val:
                func_node.body.lst += val
        self.temp_st.pop_scope()
        return [func_node]

    def convert_types(self, param_types: List[A_Type]):
        converted_types = []
        for type in param_types:
            if type.value.__class__.__name__ == "PrimitiveType":
                converted_types.append(C_AST.Type(type.value.value + "_t"))
            else:
                converted_types.append(C_AST.Type(C_AST.NonPrimitiveType(type.value.name)))
        return converted_types

    def _gen_IR_While(self, ir_node: any, st=None):
        head = []
        cur_node = ir_node
        while cur_node.__class__.__name__ != "IR_IfStmt":
            head += self.gen(cur_node, st)
            cur_node = self.ir.pop(0)
        false_label = cur_node.if_false.label
        result_stmt = C_AST.WhileStmt(cond=C_AST.Id(cur_node.cond_reg),body=C_AST.Block([]))
        continue_sig = True
        while continue_sig:
            cur_node = self.ir.pop(0)
            val = self.gen(cur_node,st)
            if val and val == false_label:
                continue_sig = False
            elif val:
                result_stmt.body.lst+= val
        if head:
            result_stmt.body.lst.append(head[-1])
        return head + [result_stmt]

    def _gen_IR_For_Range(self, ir_node: any ,st=None):
        head = []
        cur_node = ir_node
        cur_id = None
        for_loop_comp = None
        cur_loop_start = self.loop_start
        cur_loop_stop = self.loop_stop
        cur_loop_step = self.loop_step
        while cur_node.__class__.__name__ != "IR_IfStmt":
            if cur_node.__class__.__name__ == "IR_Assignment" and cur_node.val == cur_loop_start:
                cur_assign = self.gen(cur_node, st)
                head += cur_assign
                cur_id = cur_assign[0].id
            elif cur_node.__class__.__name__ == "IR_BinaryOperation" and cur_node.right_reg == cur_loop_stop:
                for_loop_comp = self.gen(cur_node,st)
            else:
                head += self.gen(cur_node, st)

            cur_node = self.ir.pop(0)

        false_label = cur_node.if_false.label
        result_stmt = C_AST.ForLoopRange(rangeVal=C_AST.RangeValues(stop=cur_loop_stop, start=cur_loop_start, step=cur_loop_step),var=cur_id, body=C_AST.Block([]))
        continue_sig = True
        while continue_sig:
            cur_node = self.ir.pop(0)
            val = self.gen(cur_node, st)
            if val and val == false_label:
                continue_sig = False
            elif val:
                result_stmt.body.lst+= val
        return head + [result_stmt]

    def _gen_IR_For_List(self, ir_node: any , st=None):
        head = []
        cur_node = ir_node
        cur_assign = None
        cur_id = None
        cur_index = None
        cur_list_reg = None
        cur_list_len = None
        for_loop_comp = None
        decl_stmt = None
        while cur_node.__class__.__name__ != "IR_IfStmt":
            if cur_node.__class__.__name__ == "IR_ForLoopVar":
                cur_id = cur_node.reg
            elif cur_node.__class__.__name__ == "IR_NonPrimitiveIndex":
                cur_id = cur_node.result_reg
                cur_list_reg = cur_node.obj_reg
                cur_list_len = self.list_len.get(cur_list_reg)
                cur_index = cur_node.idx_reg
                list_t = self.temp_st.lookup_variable(cur_node.obj_reg)
                if list_t.value.__class__.__name__ == "NonPrimitiveType" and list_t.value.value.__class__.__name__ == "Type":
                    if cur_id not in self.temp_st.scope_stack[-1]:
                        self.temp_st.declare_variable(cur_id, list_t.value.value)
                        decl_stmt = C_AST.Declaration(id=C_AST.Id(cur_id),type=list_t.value.value)
                else:
                    assert f"For list type error on {cur_id}"
            else:
                head += self.gen(cur_node, st)

            cur_node = self.ir.pop(0)

        false_label = cur_node.if_false.label
        result_stmt = C_AST.ForLoopList(var=C_AST.Id(name=cur_id), indexVar=C_AST.Id(cur_index), length=cur_list_len, Lst=C_AST.Id(cur_list_reg), body=C_AST.Block([]))

        continue_sig = True
        while continue_sig:
            cur_node = self.ir.pop(0)
            val = self.gen(cur_node, st)
            if val and val == false_label:
                continue_sig = False
            elif val:
                result_stmt.body.lst += val

        if decl_stmt:
            return head + [decl_stmt] + [result_stmt]

        return head + [result_stmt]



    def gen_IR_LstAdd(self,ir_node:IR_LstAdd,st=None):
        obj = C_AST.Id(ir_node.obj_reg)
        value = C_AST.Id(ir_node.val_reg)
        type_t = self.temp_st.lookup_variable(ir_node.obj_reg)
        type_t = C_AST.Type(type_t.value.value.value)
        return [C_AST.LstAdd(obj=obj,value=value,type=type_t, idx=ir_node.idx)]

    def gen_IR_NonPrimitiveIndex(self,ir_node:IR_NonPrimitiveIndex,st=None):
        result = C_AST.Id(ir_node.result_reg)
        obj = C_AST.Id(ir_node.obj_reg)
        idx = C_AST.Id(ir_node.idx_reg)
        type_t = self.temp_st.lookup_variable(ir_node.obj_reg)
        type_t = C_AST.Type(type_t.value.value.value)
        self.temp_st.declare_variable(ir_node.result_reg,type_t)
        return [C_AST.NonPrimitiveIndex(result,obj,type_t,idx)]

    def gen_IR_NonPrimitiveSlicing(self,ir_node: IR_NonPrimitiveSlicing,st=None):
        obj = C_AST.Id(ir_node.obj_reg)
        result_reg = C_AST.Id(ir_node.result_reg)
        start = None
        end = None
        if ir_node.start_reg:
            start = C_AST.Id(ir_node.start_reg)
        if ir_node.end_reg:
            end = C_AST.Id(ir_node.end_reg)
        type_t = self.temp_st.lookup_variable(ir_node.obj_reg)
        self.temp_st.declare_variable(ir_node.result_reg, type_t)
        return [C_AST.NonPrimitiveSlicing(result_reg,obj,start,end,type_t)]


    # Used for non primitive type from st
    def convert_NonPrimitive_Type(self,node:A_Type):
        if node.value.__class__.__name__ == "PrimitiveType":
            return node.value.value+"_t"
        return C_AST.NonPrimitiveType(type=node.value.name,value=C_AST.Type(self.convert_NonPrimitive_Type(node.value.value)))
