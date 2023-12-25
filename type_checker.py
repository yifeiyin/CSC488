import AST
from AST import Type, PrimitiveType, NonPrimitiveType
from symbol_table import SymbolTable, ParseError
from typing import Union

class TypeChecker:

    def do_typecheck(self,nodes,st=None):
        for node in nodes:
            self.typecheck(node,st)

    def typecheck(self, node, st=None) -> Union[Type, None]:
        method = 'check_' + node.__class__.__name__
        result_type = getattr(self, method, self.generic_typecheck)(node, st)
        assert isinstance(result_type, AST.Type) or result_type is None, f"Got: {result_type}"
        return result_type

    def generic_typecheck(self, node, st=None):
        raise Exception(f"Missing function check_{node.__class__.__name__}. Trying to process {node}")

    def check_FunctionDef(self, node: AST.FunctionDef, st: SymbolTable):
        param_lst = node.lst.lst or []

        if node.returnType is not None:
            return_type = node.returnType
        else:
            return_type = None

        st.declare_function(node.name.name, param_lst, return_type)
        st.func_call_stack.append(return_type)
        st.push_scope()
        for param in param_lst:
            st.declare_variable(param.var.name,param.paramType)

        for function_body_statement in node.body.lst:
            self.typecheck(function_body_statement, st)

        st.pop_scope()
        st.func_call_stack.pop()


    def check_FunctionCall(self, node: AST.FunctionCall, st: SymbolTable) -> Type:
        arg_types = []
        if node.lst.lst:
            for argument_expression in node.lst.lst:
                arg_types.append(self.typecheck(argument_expression, st))

        return st.lookup_function(node.name.name, arg_types)


    def check_ReturnStmt(self, node: AST.ReturnStmt, st: SymbolTable):
        return_type = self.typecheck(node.stmt, st)
        if len(st.func_call_stack) == 0:
            raise ParseError("Unexpected empty list for st.func_call_stack")

        func_return_type = st.func_call_stack[-1]
        if not func_return_type and not return_type:
            # Both are None
            pass

        elif func_return_type and return_type:
            self.assert_same_type(func_return_type, return_type)

        else:
            raise ParseError("The return type does no match the last declared function call" + \
                f"at node: {repr(node)}")


    def assert_same_type(self, t1: Type, t2: Type, context=None):
        """
        Helper function to check if two given type node is that of the
        same type. Precondition is that both t1 and t2 are that of class Type
        """
        assert isinstance(t1, Type)
        assert isinstance(t2, Type)

        if not (isinstance(t1.value, AST.PrimitiveType) and isinstance(t2.value, AST.PrimitiveType)) and \
                not (isinstance(t1.value, AST.NonPrimitiveType) and isinstance(t2.value, AST.NonPrimitiveType)):
            raise ParseError(f"Different class type: t1={t1.__class__.__name__} t2={t2.__class__.__name__}")

        if repr(t1.value) != repr(t2.value): # Handles nested types
            if context:
                raise ParseError(f"Encountered different type while {context}: t1={t1} t2={t2}")
            else:
                raise ParseError(f"Encountered different type: t1={t1} t2={t2}")

    def assert_expect_type_to_be(self, t1: Type, t2: Type, friendly_name: str):
        assert isinstance(t1, Type)
        assert isinstance(t2, Type)

        if not (isinstance(t1.value, AST.PrimitiveType) and isinstance(t2.value, AST.PrimitiveType)) and \
                not (isinstance(t1.value, AST.NonPrimitiveType) and isinstance(t2.value, AST.NonPrimitiveType)):
            raise ParseError(f"Different class type: t1={t1.__class__.__name__} t2={t2.__class__.__name__}")

        if repr(t1.value) != repr(t2.value): # Handles nested types
            raise ParseError(f"Expect {friendly_name} to be {t2}, but got {t1}")

    def check_Assignment(self, node: AST.Assignment, st: SymbolTable) -> Type:
        variable_name = node.left.name
        try:
            variable_type = st.lookup_variable(variable_name)
        except ParseError:
            # Variable does not exist, declare it now, and check RHS type
            variable_type = node.type
            assert variable_type is not None, f"When declaring {node.left.name}, type is missing"
            st.declare_variable(variable_name, variable_type)
            rhs_type = self.typecheck(node.right, st)
            if variable_type != rhs_type:
                # TODO: RHS could have None if the list is empty
                if (isinstance(variable_type.value, NonPrimitiveType) and isinstance(rhs_type.value, NonPrimitiveType)) and variable_type.value.name == rhs_type.value.name:
                    return variable_type
                raise ParseError(f'Assignment type mismatch. RHS should be {variable_type} instead of {rhs_type}.\nProcessing {node}')
        else:
            # Variable already exists, check the type of RHS
            rhs_type = self.typecheck(node.right, st)
            if variable_type != rhs_type:
                raise ParseError(f'Assignment type mismatch. RHS should be {variable_type} instead of {rhs_type}.\nProcessing {node}')

        return variable_type


    def check_RangeValues(self, node: AST.RangeValues, st: SymbolTable) -> None:
        int_type = Type(PrimitiveType('int'))
        self.assert_expect_type_to_be(self.typecheck(node.start.value, st), int_type, 'range start')
        if node.stop is not None:
            self.assert_expect_type_to_be(self.typecheck(node.stop.value, st), int_type, 'range stop')
        if node.step is not None:
            self.assert_expect_type_to_be(self.typecheck(node.step.value, st), int_type, 'range step')
        return None


    def check_ForLoopList(self, node: AST.ForLoopList, st: SymbolTable) -> None:
        list_type = self.typecheck(node.Lst, st)
        var_t = None
        try:
            var_t = st.lookup_variable(node.var.name)
        except Exception:
            st.declare_variable(node.var.name, list_type.value.value)
        if var_t and var_t != list_type.value.value:
            raise ParseError(f'For loop variant type mismatch. Got {var_t}, list type is {list_type.value.value}.\nProcessing {node}')
        for body_statement in node.body.lst:
            self.typecheck(body_statement, st)
        return None


    def check_ForLoopRange(self, node: AST.ForLoopRange, st: SymbolTable) -> None:
        list_type = Type(PrimitiveType('int'))
        st.push_scope()
        var_t = None
        try:
            var_t = st.lookup_variable(node.var.name)
        except Exception:
            st.declare_variable(node.var.name, list_type)
        if var_t and var_t != list_type:
            raise ParseError(f'For loop variant type mismatch. Got {var_t}, list type is {list_type}.\nProcessing {node}')
        for body_statement in node.body.lst:
            self.typecheck(body_statement, st)
        st.pop_scope()
        return None

    def check_PrimitiveLiteral(self, node: AST.PrimitiveLiteral, st: SymbolTable) -> Type:
        return Type(PrimitiveType(node.name))

    def check_NonPrimitiveLiteral(self, node: AST.NonPrimitiveLiteral, st: SymbolTable) -> Type:
        first_elem_type = None
        for i, child in enumerate(node.children):
            t = self.typecheck(child, st)
            if first_elem_type is None:
                first_elem_type = t
            else:
                try:
                    if (isinstance(first_elem_type.value, NonPrimitiveType) and isinstance(t.value, NonPrimitiveType)) and first_elem_type.value.name == t.value.name:
                        pass
                    else:
                        self.assert_same_type(first_elem_type, t)
                except ParseError:
                    raise ParseError(f'Mismatched types in list literal, first element is of type {first_elem_type}, {i}-th element is of type {t}')

        return Type(NonPrimitiveType(node.name, first_elem_type))

    #assert two node values are either int or float type
    def assert_both_numbers(self, left: Type, right:Type) -> Type:
        int_type = Type(PrimitiveType('int'))
        float_type = Type(PrimitiveType('float'))
        is_float = False
        try:
            self.assert_same_type(left, int_type)
        except ParseError:
            try:
                self.assert_same_type(left, float_type)
                is_float = True
            except ParseError:
                raise ParseError(f"Invalid type on Binary Operator left={left}")
        try:
            self.assert_same_type(right, int_type)
        except ParseError:
            try:
                self.assert_same_type(right, float_type)
                is_float = True
            except ParseError:
                raise ParseError(f"Invalid type on Binary Operator right={right}")
        if is_float:
            return float_type
        return int_type

    def check_BinaryOperation(self, node: AST.BinaryOperation, st: SymbolTable) -> Type:
        numbers_only_operations = ["-", "*", "/", "<", "<=", "=>", ">"]
        left = self.typecheck(node.left,  st)
        right = self.typecheck(node.right, st)
        if node.operator in numbers_only_operations:
            t = self.assert_both_numbers(left, right)
            return t
        else:
            try:
                #case when comparing numbers
                t = self.assert_both_numbers(left, right)
                return t
            except ParseError:
                try:
                    #case when comparing bool, str etc
                    self.assert_same_type(left, right)
                    return left
                except ParseError:
                    raise ParseError(f"Type mismatch on Binary Operator left={left} right={right}")

    def check_UnaryOperation(self, node: AST.UnaryOperation, st: SymbolTable) -> Type:
        int_type = Type(PrimitiveType('int'))
        float_type = Type(PrimitiveType('float'))
        cond_type = Type(PrimitiveType('bool'))

        right = self.typecheck(node.right, st)

        if node.operator == "-":
            try:
                self.assert_same_type(right, int_type)
                return int_type
            except ParseError:
                try:
                    self.assert_same_type(right, float_type)
                    return float_type
                except ParseError:
                    raise ParseError(f"Invalid type on Unary Operator right={right}")
        else:
            try:
                self.assert_same_type(right, cond_type)
                return cond_type
            except ParseError:
                raise ParseError(f"Invalid type on Unary Operator right={right}")

    def check_IfStmt(self, node:AST.IfStmt, st: SymbolTable) -> None:
        self.typecheck(node.ifCond, st)
        st.push_scope()
        for statement in node.body.lst:
            self.typecheck(statement, st)
        st.pop_scope()

    def check_ElifStmt(self, node:AST.ElifStmt, st: SymbolTable) -> None:
        self.typecheck(node.elifCond, st)
        st.push_scope()
        for statement in node.body.lst:
            self.typecheck(statement, st)
        st.pop_scope()

    def check_ElseStmt(self, node:AST.ElseStmt, st: SymbolTable) -> None:
        st.push_scope()
        for statement in node.body.lst:
            self.typecheck(statement, st)
        st.pop_scope()

    def check_WhileStmt(self, node:AST.WhileStmt, st: SymbolTable) -> None:
        self.typecheck(node.cond, st)
        st.push_scope()
        for statement in node.body.lst:
            self.typecheck(statement, st)
        st.pop_scope()

    def check_LstAppend(self,node:AST.LstAppend, st:SymbolTable):
        obj_type = self.typecheck(node.obj,st)
        val_type = self.typecheck(node.val,st)
        assert isinstance(obj_type.value,NonPrimitiveType)
        if obj_type.value.name != 'list': raise Exception(f'Cannot use append on type {obj_type.value.name}')
        assert obj_type.value.value == val_type

    def check_NonPrimitiveIndex(self,node:AST.NonPrimitiveIndex,st:SymbolTable):
        obj_type = self.typecheck(node.obj,st)
        idx_type = self.typecheck(node.idx,st)
        assert isinstance(obj_type.value,NonPrimitiveType)
        assert isinstance(idx_type.value,PrimitiveType)
        assert idx_type.value.value == 'int'
        return obj_type.value.value

    def check_Id(self,node: AST.Id,st:SymbolTable)->Type:
        return st.lookup_variable(node.name)

    def check_NonPrimitiveSlicing(self,node:AST.NonPrimitiveSlicing,st:SymbolTable):
        obj_type = self.typecheck(node.obj,st)
        if node.start:
            start_t = self.typecheck(node.start)
            assert isinstance(start_t.value, PrimitiveType)
            assert start_t.value.value == 'int'
        if node.end:
            end_t = self.typecheck(node.end)
            assert isinstance(end_t.value, PrimitiveType)
            assert end_t.value.value == 'int'
        return obj_type
