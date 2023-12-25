import pytest
import os
from compiler import read, compiler, execute_program

test_names_compile = [f.replace('.py', '') for f in os.listdir(f'./tests/compile/') if f.endswith('.py')]
@pytest.mark.parametrize("test_name", test_names_compile)
def test_compile(test_name):
    d= './tests/compile'
    compiler(
        input_file=f'{d}/{test_name}.py',
        c=f'{d}/{test_name}.c',
        executable=f'{d}/{test_name}',
        opt_on='03_' in test_name,
        ir_tmp=f'{d}/{test_name}_IR.txt',
    )

test_names_error = [f.replace('.py', '') for f in os.listdir(f'./tests/error/') if f.endswith('.py')]
@pytest.mark.parametrize("test_name", test_names_error)
def test_error(test_name):
    d = './tests/error'

    first_line, second_line = read(f'{d}/{test_name}.py').split('\n')[:2]
    assert first_line.startswith('#'), "Expect first line to be a comment for this test"
    assert second_line.startswith('#'), "Expect second line to be a comment for this test"
    expected_words = second_line.replace('#', '').strip().split()

    if '[RUNTIME]' in first_line:
        try:
            compiler(
                input_file=f'{d}/{test_name}.py',
                c=f'{d}/{test_name}.c',
                executable=f'{d}/{test_name}',
                opt_on='[OPT_ON]' in first_line,
                ir_tmp=f'{d}/{test_name}_IR.txt',
            )
        except Exception as e:
            raise Exception(f"Does not expect error at this stage, got: {e}")

        code, stdout = execute_program(f'{d}/{test_name}', input='')
        assert code == 1, f"Expected runtime error, got: {code=} {stdout=}"

        for word in expected_words:
            first_line = str(stdout).split('\n')[0]
            assert word in first_line, f"Expect error message to contain {word}\n\nGot Error:{str(stdout)}"
        if len(expected_words) == 0:
            raise Exception("Got stdout: " + str(stdout))


    else:
        try:
            compiler(
                input_file=f'{d}/{test_name}.py',
                c=f'{d}/{test_name}.c',
                executable=f'{d}/{test_name}',
                opt_on='[OPT_ON]' in first_line,
                ir_tmp=f'{d}/{test_name}_IR.txt',
            )
        except Exception as e:
            # Expect every word in second line to appear in the error message
            for word in expected_words:
                first_line = str(e).split('\n')[0]
                assert word in first_line, f"Expect error message to contain {word}\n\nGot Error:{str(e)}"
            if len(expected_words) == 0:
                raise Exception("Got error: " + str(e))
        else:
            raise Exception("Expected an error to be thrown")


test_names_opt = [f.replace('.py', '') for f in os.listdir(f'./tests/opt/') if f.endswith('.py')]
@pytest.mark.parametrize("test_name", test_names_opt)
def test_opt(test_name):
    d= './tests/opt'
    compiler(
        input_file=f'{d}/{test_name}.py',
        c=f'{d}/{test_name}_opt_on.c',
        executable=f'{d}/{test_name}_opt_on',
        opt_on=True,
        ir_tmp=None,
    )

    compiler(
        input_file=f'{d}/{test_name}.py',
        c=f'{d}/{test_name}_opt_off.c',
        executable=f'{d}/{test_name}_opt_off',
        opt_on=False,
        ir_tmp=None,
    )

    output_on = execute_program(f'{d}/{test_name}_opt_on', input='')[1]
    output_off = execute_program(f'{d}/{test_name}_opt_off', input='')[1]

    assert output_on == output_off, f"Expect opt_on to be the same as opt_off\n\nGot:\n{output_on=}\n{output_off=}"

