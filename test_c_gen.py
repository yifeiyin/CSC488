import pytest
import os
import difflib
from yacc import pythonParser
from type_checker import TypeChecker, SymbolTable
from ir_gen import IRGen
from C_AST_gen import CASTGenerator
from C_AST import CCodeGenerator

@pytest.fixture
def parser():
    p = pythonParser()
    p.build()
    return p

test_dir = 'tests_c_gen'
files = os.listdir(f'./{test_dir}/')
test_names = [f.replace('_input.py', '') for f in files if f.endswith('_input.py')]


def format_parser_output(o):
    import json
    return json.dumps(o, default=lambda x: { 'NODE': x.__class__.__name__, **x.__dict__}, indent=2)


@pytest.mark.parametrize("test_name", test_names)
def test_c_gen(parser, test_name):
    with open(f'./{test_dir}/{test_name}_input.py', 'r') as f:
        input_str = f.read()
    try:
        with open(f'./{test_dir}/{test_name}_output.c', 'r') as f:
            output_str = f.read().strip()
    except FileNotFoundError:
        print(f'No output file for {test_name}')
        output_str = None

    # A dirty but quick way to implement comments
    input_str = '\n'.join(line for line in input_str.split('\n') if not line.startswith('#'))

    parsed_blocks = parser.parse(input_str)
    tc = TypeChecker()
    st = SymbolTable()
    for block in parsed_blocks:
        tc.typecheck(block, st)

    ir_generator = IRGen()
    ir_generator.generate_IR(parsed_blocks)
    generated_ir = ir_generator.IR

    with open(f'./{test_dir}/{test_name}_ir_received.txt', 'w+') as f:
        f.write('\n'.join(repr(ir) for ir in generated_ir) + '\n')

    c_ast_generator = CASTGenerator()
    c_ast = c_ast_generator.generate_AST(generated_ir, st)
    c_code_generator = CCodeGenerator()
    received_str = c_code_generator.generate_code(c_ast)

    with open(f'./{test_dir}/{test_name}_received.c', 'w+') as f:
        f.write(received_str)

    # raise Exception('Raising error pytest so we can see stdout')
    if output_str is not None:
        if received_str.strip().strip("\n") != output_str.strip().strip("\n"):
            diff = difflib.unified_diff(output_str.split('\n'), received_str.split('\n'), f"./tests/{test_name}_output.c", f"./tests/{test_name}_received.c", lineterm='')
            with open(f'./{test_dir}/{test_name}_received.diff', 'w+') as f:
                f.write('\n'.join(diff) + '\n')
            raise AssertionError(f'Output mismatch')
        else:
            try:
                os.remove(f'./{test_dir}/{test_name}_received.diff')
            except FileNotFoundError:
                pass
    else:
        import subprocess
        proc = subprocess.run(f'gcc ./{test_dir}/{test_name}_received.c -o ./{test_dir}/{test_name}_received', shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        print("----- stderr -----")
        print(proc.stderr)
        print("----- stdout -----")
        print(proc.stdout)
        assert proc.returncode == 0, f"gcc return code was {proc.returncode}"
