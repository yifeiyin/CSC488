import pytest
from C_AST import *
from lex import pythonLexer

case1 = Block([
    Declaration(Id('var1'), Type('int_t')),
    BinaryOperation(Id('var1'),Type('int_t'), '+', operand_a=Id('var1'), operand_b=Id('var2')),
])

case1_out = """
#include "../starter.c"


int main() {
/***** Main *****/
int_t var1;
var1 = var1 + var2;

/***** End of main *****/

    str_clean_up();
    list_clean_up();

    return 0;
}
"""

case2 = Block([
    Declaration(Id('var1'), Type('int_t')),
    BinaryOperation(Id('var1'),Type('int_t'), '+', operand_a=Id('var1'), operand_b=Id('var1')),
    IfStmt(ifCond=Id('var1'), body=Block([
        BinaryOperation(Id('var1'),Type('int_t'), '+', operand_a=Id('var1'), operand_b=Id('var2')),
        IfStmt(ifCond=Id('var1'), body=Block([
            BinaryOperation(Id('var1'),Type('int_t'), '+', operand_a=Id('var1'), operand_b=Id('var2')),
        ])),
    ])),
])

case2_out = """
#include "../starter.c"


int main() {
/***** Main *****/
int_t var1;
var1 = var1 + var1;
if (var1 + var1) {
    var1 = var1 + var2;
    if (var1) {
        var1 = var1 + var2;
    }
}

/***** End of main *****/

    str_clean_up();
    list_clean_up();

    return 0;
}
"""

case3 = Block([
    FunctionDeclaration(
        name=Id("func1"),
        lst=ParameterLst([
            Parameter(Type('int_t'), Id('arg1')),
            Parameter(Type('int_t'), Id('arg2')),
        ]),
        body=Block([

        ]),
        returnType=Type('int_t'),
    )
])

case3_out = """
#include "../starter.c"

/***** Function declarations *****/
int_t func1(int_t arg1, int_t arg2);
/***** End of function declarations *****/

/***** Function definitions *****/
int_t func1(int_t arg1, int_t arg2) {
} /* End of func1 */

/***** End of function definitions *****/

int main() {
/***** Main *****/

/***** End of main *****/

    str_clean_up();
    list_clean_up();

    return 0;
}
"""

cases = [
    [case1, case1_out],
    [case2, case2_out],
    [case3, case3_out],
]

@pytest.fixture
def lexer():
    l = pythonLexer()
    l.build()
    return l

@pytest.mark.parametrize("input_data, expected", cases)
def test_main_c_ast(input_data, expected):
    result = CCodeGenerator().generate_code(input_data)
    print(result)
    assert result.strip() == expected.strip()
