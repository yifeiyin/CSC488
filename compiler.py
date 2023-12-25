from os import execl
from yacc import pythonParser
from type_checker import TypeChecker, SymbolTable
from ir_gen import IRGen
from C_AST_gen import CASTGenerator
from C_AST import CCodeGenerator

def py_parser():
    p = pythonParser()
    p.build()
    return p

def read(filename):
    with open(filename) as f:
        return f.read()

def write(filename, s):
    with open(filename, 'w+') as f:
        f.write(s)

def ir_to_str(ir):
    return '\n'.join(repr(ir_line) for ir_line in ir) + '\n'

def remove_comments(input_str):
    # A dirty but quick way to implement comments
    return '\n'.join(line for line in input_str.split('\n') if not line.startswith('#'))

def parse_from_code_to_blocks(input_str):
    return py_parser().parse(input_str)

def type_check_from_blocks_to_st(blocks):
    tc = TypeChecker()
    st = SymbolTable()
    for block in blocks:
        tc.typecheck(block, st)
    return st

def from_blocks_to_ir(blocks):
    ir_generator = IRGen()
    ir_generator.generate_IR(blocks)
    return ir_generator.IR

def from_ir_st_to_c(ir, st, opt_on):
    c_ast_generator = CASTGenerator()
    c_ast = c_ast_generator.generate_AST(ir, st)
    c_code_generator = CCodeGenerator()
    c_code_generator.eval_mode = opt_on
    return c_code_generator.generate_code(c_ast)

def compiler(input_file, c, executable, opt_on=False, ir_tmp=None):
    input_str = read(input_file)
    input_str = remove_comments(input_str)

    for index, s in enumerate(input_str.split('\n')):
        if s.startswith(' ') and len(s.strip()) != 0:
            raise Exception(f"Leading spaces detected at line {index}\nIndentation using spaces are not supported. Did you mean to use tabs?")

    try:
        blocks = parse_from_code_to_blocks(input_str)
    except Exception as e:
        raise Exception("Parser Error: " + e.args[0])
    try:
        st = type_check_from_blocks_to_st(blocks)
    except Exception as e:
        raise Exception("Type Checker Error: " + e.args[0])

    try:
        ir = from_blocks_to_ir(blocks)
    except Exception as e:
        raise Exception("IR Translation Error: ", e.args[0])
    if ir_tmp: write(ir_tmp, ir_to_str(ir))
    try:
        code = from_ir_st_to_c(ir, st, opt_on=opt_on)
    except Exception as e:
        raise Exception("Unable to generate target: " + e.args[0])

    write(c, code)

    try:
        check_if_code_compiles(c, executable)
    except Exception as e:
        raise Exception("Unable to compile output: ", e)


def check_if_code_compiles(filename, output):
    import subprocess
    proc = subprocess.run(f'gcc {filename} -o {output}', shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    assert proc.returncode == 0, f"gcc return code was {proc.returncode}\n{proc.stderr}"


def execute_program(filename, input=""):
    import subprocess
    proc = subprocess.run(f'{filename}', shell=True, stdout=subprocess.PIPE, universal_newlines=True, input=input)
    return (proc.returncode, proc.stdout)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Compile a python program to C')
    parser.add_argument('input', help='The python program to compile')
    parser.add_argument('-o', '--opt', help='Enable optimization', action='store_true')
    parser.add_argument('-r', '--run', help='Run the code if successfully compiled', action='store_true')
    args = parser.parse_args()

    name = args.input
    input_file = f'./playground/{name}.py'
    c_file = input_file.replace('.py', '.c')
    output_file = input_file.replace('.py', '')
    ir_tmp_file = input_file.replace('.py', '.ir.txt')

    print(f"Compiling {input_file} to {c_file}. Optimization: {'on' if args.opt else 'off'}")

    try:
        compiler(input_file, c_file, output_file, opt_on=args.opt, ir_tmp=ir_tmp_file)
    except Exception as e:
        raise
    else:
        print('Successfully compiled to C code')

    try:
        check_if_code_compiles(c_file, output_file)
    except Exception as e:
        print('Unable to compile the output c code to executable')
        print(e)
        exit(1)
    else:
        print('Successfully compiled to executable')

    if args.run:
        print('Running the program now...')
        execl(output_file, output_file)
