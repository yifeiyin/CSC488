import pytest
from lex import pythonLexer

@pytest.fixture
def lexer():
    l = pythonLexer()
    l.build()
    return l

cases = {
    "1.234": "FLOAT",
    "-1.234": "FLOAT",
    "0.": "FLOAT",
    "-0.": "FLOAT",
    "-11.": "FLOAT",
    "11.": "FLOAT",
    "0.0": "FLOAT",
    "-0.0": "FLOAT",
    "1": "INTEGER",
    "-1": "INTEGER",
    "-10000": "INTEGER",
    "-0": "INTEGER",
    "0": "INTEGER",
    "True": "BOOL",
    "False": "BOOL",
    "None": "NONE",
    "a": "ID",
    "a1": "ID",
    "a1_": "ID",
    "a1_1": "ID",
    "a1_1_": "ID",
    "|": "OR",
    "or": "OR",
    "&": "AND",
    "and": "AND",
    "^": "XOR",
    ":": "COLON",
    "=": "ASSIGN",
    "!": "NOT",
    "not": "NOT",
    "!=": "NOTEQUAL",
    "==": "EQUAL",
    "<=": "EQLESS",
    ">=": "EQGREATER",
    "[": "LBRACKET",
    "]" : "RBRACKET",
    "not": "NOT",
    "else": "ELSE",
    "-": "MINUS",
    "int": "TINT",
    "'hi'": "STRING",
    '"hi"': "STRING",
    r"'hi\''": "STRING",
}

@pytest.mark.parametrize("input_data, expected", cases.items())
def test_lex_simple_token(lexer, input_data, expected):
        result = lexer.test(input_data)
        assert len(result) == 1, f"Expect 1, got {len(result)}: {[x.type for x in result]}"
        assert result[0].type == expected, f"Expect {expected}, got {result[0].type}"
