import argparse
from ply import lex

reserved = {
    'while': 'WHILE',
    'for': 'FOR',
    'in': 'IN',
    'range': 'RANGE',
    'if': "IF",
    'elif': "ELIF",
    'else': "ELSE",
    'return': 'RETURN',
    'int': 'TINT',
    'str': 'TSTR',
    'float': "TFLOAT",
    'bool': "TBOOL",
    'None': "NONE",
    'def': "DEF",
    'append': "APPEND"
}

tokens = [
    'PLUS',
    'MINUS',
    'MODULE',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'LBRACKET',
    'RBRACKET',
    'EQGREATER',
    'EQLESS',
    'NOTEQUAL',
    'EQUAL',
    'ASSIGN',
    'GREATER',
    'LESS',
    'AND',
    'OR',
    'NOT',
    'XOR',
    'FUNCTIONANNOTATION',
    'BOOL',
    'STRING',
    'FLOAT',
    'INTEGER',
    'ID',
    'NEWLINE',
    'COLON',
    'COMMA',
    'DOT'
] + list(reserved.values())

class pythonLexer():
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_MODULE = r'%'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_EQGREATER = r'\>='
    t_EQLESS = r'\<='
    t_EQUAL = r'=='
    t_ASSIGN = r'='
    t_GREATER = r'\>'
    t_LESS = r'\<'
    t_XOR = r'\^'
    t_COMMA = r','
    t_COLON = r':'
    t_DOT = r'\.'
    t_ignore_COMMENT = r'\#.*'
    t_ignore = ' '
    literals = "!@-`~\\|/{}?'\""

    #keeps track number of tabs for each line number
    tab_list = []
    # lexLineNo[0] is the current line number
    # lexLineNo[1] is the line number after counting newline
    lexLineNo = [1,1]

    def t_BOOL(self,t):
        r'(True)|(False)'
        if t.value == 'True':
            t.value = True
        elif t.value == 'False':
            t.value = False
        else:
            assert False
        return t

    def t_NOTEQUAL(self,t):
        r'\!='
        return t

    def t_AND(self,t):
        r'(and)|(&)'
        return t

    def t_OR(self,t):
        r'(or)|\|'
        return t

    def t_NOT(self,t):
        r'(not)|!'
        return t

    # NOT HANDLE ESCAPE STRING YET
    def t_STRING(self,t):
        r'("(?:\\.|[^"\\])*")|(\'(?:\\.|[^\'\\])*\')'
        t.value = str(t.value[1:-1])
        return t

    def t_FLOAT(self,t):
        r'-?(([1-9]\d*)|(0))\.\d*'
        t.value = float(t.value)
        return t

    def t_INTEGER(self,t):
        r'-?(([1-9]\d*)|0)'
        t.value = int(t.value)
        return t

    def t_ID(self,t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = reserved.get(t.value, 'ID')  # Check for reserved words
        return t

    def t_NEWLINE(self,t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        self.lexLineNo[1] = t.lexer.lineno
        return t

    def t_TAB(self, t):
        r'\t+'
        self.tab_list.append([t.lexer.lineno, len(t.value)])

    def t_FUNCTIONANNOTATION(self, t):
        r'(-\>)'
        return t


    def t_error(self,t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def getTabCount(self, lineNo):
        for i in self.tab_list:
            if i[0] == lineNo:
                return i[1]
        return 0

    def clearTabCount(self):
        self.tab_list.clear()

    def build(self, **kwargs):
        self.tokens = tokens
        self.lexer = lex.lex(module=self, **kwargs)

    def test(self, data):
        self.lexer.input(data)
        result = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            result.append(tok)
        return result

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Take in the miniJava source code and perform lexical analysis.')
    parser.add_argument('FILE', help="Input file with miniJava source code")
    args = parser.parse_args()

    f = open(args.FILE, 'r')
    data = f.read()
    f.close()

    m = pythonLexer()
    m.build()
    print(m.test(data), sep='\n')
