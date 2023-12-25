from ply import yacc
from lex import pythonLexer
from lex import tokens
from dataclasses import dataclass
import argparse
import AST


@dataclass
class statementNode():
    lineNo: int
    tabCount: int
    astNode: AST.Node

    def __init__(self, lineNo, tabCount, astNode):
        self.lineNo = lineNo
        self.tabCount = tabCount
        self.astNode = astNode


lst_stack = []
tup_stack = []

statementNodeLst = []

final_result = []


def statementBodyGenerator():
    stack = []
    current_statement_with_body = None  # the statement that is being considered for any child statements
    expected_tab_count = 0
    statements_with_body = ["IfStmt", "ElifStmt", "ElseStmt", "WhileStmt", "ForLoopRange", "ForLoopList", "FunctionDef"]
    for statement in statementNodeLst:
        if statement.tabCount == expected_tab_count and current_statement_with_body != None:
            current_statement_with_body.astNode.body.lst.append(statement.astNode)
        elif statement.tabCount < expected_tab_count:
            while stack and statement.tabCount <= current_statement_with_body.tabCount:
                current_statement_with_body = stack.pop()
            if statement.tabCount > current_statement_with_body.tabCount:
                expected_tab_count = statement.tabCount
                current_statement_with_body.astNode.body.lst.append(statement.astNode)
                stack.append(current_statement_with_body)

        if statement.tabCount == 0:
            final_result.append(statement.astNode)
        if statement.astNode.__class__.__name__ in statements_with_body:
            stack.append(statement)
            current_statement_with_body = statement
            if current_statement_with_body.astNode.body == None:
                current_statement_with_body.astNode.body = AST.Block(lst=[])
            expected_tab_count += 1
    return final_result


class pythonParser:
    precedence = (
        ('nonassoc', 'EQGREATER', 'EQLESS', 'GREATER', 'LESS', 'EQUAL', 'NOTEQUAL', 'XOR'),
        ('left', 'OR', 'AND'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE', 'MODULE'),
        ('right', 'ASSIGN'),
        ('right', 'UNARY'),
    )

    start = 'program'

    def p_program(self, p):
        """program  : block"""
        p[0] = p[1]

    def p_block(self, p):
        """block    : block statement
                     | statement"""
        if len(p) == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[1]]

    def p_expression(self, p):
        """expression : ID
                      | primitive_literal"""
        if type(p[1]) == str:  # It is ID
            p[0] = AST.Id(name=p[1])
        else:  # Anything else
            p[0] = p[1]

    def p_type(self, p):
        """type     : primitive_type
                    | non_primitive_type"""
        p[0] = AST.Type(p[1])

    def p_primitive_type(self, p):
        """primitive_type   : TINT
                            | TSTR
                            | TFLOAT
                            | TBOOL
                            | NONE"""
        p[0] = AST.PrimitiveType(value=p[1].lower())

    def p_non_primitive(self, p):
        """non_primitive_type   : LBRACKET type RBRACKET
                                | LPAREN type RPAREN"""
        if p[1] == '[':
            p[0] = AST.NonPrimitiveType(name='list', value=p[2])
        elif p[1] == '(':
            p[0] = AST.NonPrimitiveType(name='tuple', value=p[2])
        else:
            assert False

    def p_primitive_literal(self, p):
        """primitive_literal    : INTEGER
                                | FLOAT
                                | STRING
                                | BOOL
                                | NONE"""
        if p[1] == 'None':
            p[0] = AST.PrimitiveLiteral(name='none', value='none-placeholder')
        else:
            p[0] = AST.PrimitiveLiteral(name=p[1].__class__.__name__, value=p[1])

    def p_expr_binary(self, p):
        """expression   : expression PLUS expression
                        | expression MINUS expression
                        | expression TIMES expression
                        | expression DIVIDE expression
                        | expression MODULE expression
                        | expression EQGREATER expression
                        | expression EQLESS expression
                        | expression GREATER expression
                        | expression LESS expression
                        | expression EQUAL expression
                        | expression NOTEQUAL expression
                        | expression OR expression
                        | expression AND expression
                        | expression XOR expression"""
        p[0] = AST.BinaryOperation(left=p[1], operator=p[2], right=p[3])

    def p_expr_unary(self, p):
        """
        expression  : MINUS expression %prec UNARY
                    | NOT expression %prec UNARY"""
        p[0] = AST.UnaryOperation(operator=p[1], right=p[2])

    def p_lst_empty(self, p):
        """
        expression : LBRACKET RBRACKET
        """
        p[0] = AST.NonPrimitiveLiteral(name='list', children=[])

    def p_lst_head(self, p):
        """
        list    : LBRACKET expression
        """
        global lst_stack
        if not p[2]:
            lst = AST.NonPrimitiveLiteral(name='list', children=[lst_stack[-1].children.pop()])
        else:
            lst = AST.NonPrimitiveLiteral(name='list', children=[p[2]])
        lst_stack.append(lst)

    def p_lst_body(self, p):
        """
        list    : list COMMA expression
        """
        global lst_stack
        if p[3]:
            lst_stack[-1].children.append(p[3])

    def p_lst_tail(self, p):
        """
        expression      : list RBRACKET
        """
        global lst_stack
        if len(lst_stack) > 1:
            lst_stack[-2].children.append(lst_stack.pop())
        else:
            p[0] = lst_stack.pop()

    def p_tuple_empty(self, p):
        """
        expression : LPAREN RPAREN
        """
        p[0] = AST.NonPrimitiveLiteral(name='tuple', children=[])

    def p_tuple_head(self, p):
        """
        tuple   : LPAREN expression COMMA expression
        """
        # tuple must have either 0 or more than 1 expression
        global tup_stack
        if not p[2]:
            tup = AST.NonPrimitiveLiteral(name='tuple', children=[tup_stack[-1].children.pop()])
        else:
            tup = AST.NonPrimitiveLiteral(name='tuple', children=[p[2], p[4]])
        tup_stack.append(tup)

    def p_tuple_body(self, p):
        """
        tuple   : tuple COMMA expression
        """
        global tup_stack
        if p[3]:
            tup_stack[-1].children.append(p[3])

    def p_tuple_tail(self, p):
        """
        expression      : tuple RPAREN
        """
        global tup_stack
        if len(tup_stack) > 1:
            tup_stack[-2].children.append(tup_stack.pop())
        else:
            p[0] = tup_stack.pop()

    def p_expr_paren(self, p):
        """
        expression  : LPAREN expression RPAREN
        """
        p[0] = p[2]

    def p_statement(self, p):
        """statement : statement_no_new_line NEWLINE
                     | statement_no_new_line
                     | assignment
                     | expression NEWLINE
        """
        # get current line number
        lineNo = self.lexer.lexLineNo[0]
        tabCount = self.lexer.getTabCount(lineNo)
        statementNodeLst.append(statementNode(lineNo, tabCount, p[1]))
        # update current line number
        self.lexer.lexLineNo[0] = self.lexer.lexLineNo[1]
        p[0] = p[1]

    def p_statement_no_new_line(self, p):
        """statement_no_new_line : function_dec
                                 | return_stmt
                                 | if_statement
                                 | elif_statement
                                 | else_statement
                                 | while_statement
                                 | for_loop_range
                                 | for_loop_lst"""
        p[0] = p[1]

    def p_function_dec(self, p):
        """function_dec : DEF ID LPAREN parameter_or_empty RPAREN FUNCTIONANNOTATION type COLON"""
        p[0] = AST.FunctionDef(name=AST.Id(name=p[2]), lst=p[4], body=None, returnType=p[7])

    def p_parameter_or_empty(self, p):
        """parameter_or_empty : parameter_lst
                            | empty"""
        if len(p) == 1:
            p[0] = AST.ParameterLst(lst=[])
        else:
            p[0] = AST.ParameterLst(lst=p[1])

    def p_parameter_lst(self, p):
        """parameter_lst : parameter_lst COMMA parameter
                         | parameter"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_parameter(self, p):
        """parameter : ID COLON type"""

        p[0] = AST.Parameter(paramType=p[3], var=AST.Id(name=p[1]))

    def p_function_call(self, p):
        """expression : expression LPAREN argument_or_empty RPAREN"""
        p[0] = AST.FunctionCall(name=p[1], lst=p[3])

    def p_argument_or_empty(self, p):
        """argument_or_empty : argument_lst
                             | empty"""
        if p[1]:
            p[0] = AST.ArgumentLst(lst=p[1])
        else:
            p[0] = AST.ArgumentLst(lst=[])

    def p_argument_lst(self, p):
        """argument_lst : argument_lst COMMA expression
                        | expression"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_return_stmt(self, p):
        """return_stmt : RETURN expression NEWLINE"""
        p[0] = AST.ReturnStmt(stmt=p[2])

    def p_if_statement(self, p):
        """if_statement : IF expression COLON"""
        p[0] = AST.IfStmt(ifCond=p[2], body=None)

    def p_elif_statement(self, p):
        """elif_statement : ELIF expression COLON"""
        p[0] = AST.ElifStmt(elifCond=p[2], body=None)

    def p_else_statement(self, p):
        """else_statement : ELSE COLON"""
        p[0] = AST.ElseStmt(body=None)

    def p_for_loop_range(self, p):
        """for_loop_range : FOR ID IN range COLON"""
        p[0] = AST.ForLoopRange(var=AST.Id(name=p[2]), rangeVal=p[4], body=None)

    def p_range(self, p):
        """range : RANGE LPAREN expression RPAREN
                 | RANGE LPAREN expression COMMA expression RPAREN
                 | RANGE LPAREN expression COMMA expression COMMA expression RPAREN"""

        if len(p) == 5:
            p[0] = AST.RangeValues(stop=p[3], start=None, step=None)
        elif len(p) == 7:
            p[0] = AST.RangeValues(stop=p[5], start=p[3], step=None)
        else:
            p[0] = AST.RangeValues(stop=p[5], start=p[3], step=p[7])

    # for list and tuples
    def p_for_loop_lst(self, p):
        """for_loop_lst : FOR ID IN expression COLON"""
        p[0] = AST.ForLoopList(var=AST.Id(name=p[2]), Lst=p[4], body=None)

    def p_while_statement(self, p):
        """while_statement : WHILE expression COLON"""
        p[0] = AST.WhileStmt(cond=p[2], body=None)

    def p_assignment(self, p):
        """assignment :  ID ASSIGN expression NEWLINE
                      |  ID COLON type ASSIGN expression NEWLINE"""
        if len(p) == 5:
            p[0] = AST.Assignment(left=AST.Id(name=p[1]), type=None, right=p[3])
            # should the type be p[3].__class__.__name__?
        else:
            p[0] = AST.Assignment(left=AST.Id(name=p[1]), type=p[3], right=p[5])

    def p_list_append(self, p):
        """
        statement_no_new_line : expression DOT APPEND LPAREN expression RPAREN
        """
        p[0] = AST.LstAppend(obj=p[1], val=p[5])

    def p_non_prim_index(self, p):
        """
        expression : expression LBRACKET expression RBRACKET
        """
        p[0] = AST.NonPrimitiveIndex(obj=p[1], idx=p[3])

    def p_non_prim_slicing(self, p):
        """
        expression  : expression LBRACKET expression COLON RBRACKET
                    | expression LBRACKET expression COLON expression RBRACKET
                    | expression LBRACKET COLON RBRACKET
        """
        if len(p) == 6:
            p[0] = AST.NonPrimitiveSlicing(obj=p[1], start=p[3], end=None)
        elif len(p) == 7:
            p[0] = AST.NonPrimitiveSlicing(obj=p[1], start=p[3], end=p[5])
        else:
            p[0] = AST.NonPrimitiveSlicing(obj=p[1], start=None, end=None)

    def p_non_prim_slicing_r(self, p):
        """
        expression : expression LBRACKET COLON expression RBRACKET
        """
        p[0] = AST.NonPrimitiveSlicing(obj=p[1], start=None, end=p[4])

    def p_empty(self, p):
        """empty :"""
        pass

    def p_error(self, p):
        raise Exception(f"Unable to parse at line={self.lexer.lexLineNo[1]} col={self.lexer.lexLineNo[0]}. At token" + str(p))

    def build(self, **kwargs):
        self.tokens = tokens
        self.lexer = pythonLexer()
        self.lexer.build()
        self.parser = yacc.yacc(module=self, debug=True, **kwargs)

    def parse(self, data):
        statementNodeLst.clear()
        final_result.clear()
        result = self.parser.parse(data)
        statementBodyGenerator()
        self.lexer.clearTabCount()
        return final_result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Take in the miniJava source code and perform lexical analysis.')
    parser.add_argument('FILE', help="Input file with miniJava source code")
    args = parser.parse_args()

    f = open(args.FILE, 'r')
    data = f.read()
    f.close()
    m = pythonParser()
    m.build()
    root = m.parse(data)
    print(root)
