"""
From https://github.com/bigcode-project/bigcode-evaluation-harness/blob/main/lm_eval/tasks/humanevalpack.py
@article{muennighoff2023octopack,
      title={OctoPack: Instruction Tuning Code Large Language Models},
      author={Niklas Muennighoff and Qian Liu and Armel Zebaze and Qinkai Zheng and Binyuan Hui and Terry Yue Zhuo and Swayam Singh and Xiangru Tang and Leandro von Werra and Shayne Longpre},
      journal={arXiv preprint arXiv:2308.07124},
      year={2023}}
"""

"""
    Need to setup javascript environment first
"""

import os
from typing import Dict, List, Tuple
os.environ["HF_ALLOW_CODE_EVAL"] = "1"
# Note: the following allows running only on linux yet
# os.environ['PATH'] = '/usr/local/lib/nodejs/node/bin:' + os.environ['PATH']
# os.environ['NODE_PATH'] = '/usr/local/lib/node_modules'
import contextlib
import signal
import json
import time
import tempfile
import subprocess
from multiprocessing import Process, Queue
import rpy2.robjects as robjects
from evaluate import load

@contextlib.contextmanager
def chdir(root):
    if root == ".":
        yield
        return
    cwd = os.getcwd()
    os.chdir(root)
    try:
        yield
    except BaseException as exc:
        raise exc
    finally:
        os.chdir(cwd)


@contextlib.contextmanager
def create_tempdir():
    with tempfile.TemporaryDirectory() as dirname:
        with chdir(dirname):
            yield dirname

@contextlib.contextmanager
def chdir(root):
    if root == ".":
        yield
        return
    cwd = os.getcwd()
    os.chdir(root)
    try:
        yield
    except BaseException as exc:
        raise exc
    finally:
        os.chdir(cwd)


@contextlib.contextmanager
def create_tempdir():
    with tempfile.TemporaryDirectory() as dirname:
        with chdir(dirname):
            yield dirname


class TimeoutException(Exception):
    pass

@contextlib.contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

def r_executor(references, predictions, timeout):

    program = predictions[0][0] + '\n' + references[0]
    result = []

    with create_tempdir():
        open(f"main.r", 'w').write(program)
        # Run program.
        try:
            exec_result = subprocess.run(["Rscript main.r"], timeout=timeout, capture_output=True, shell=True)
            # print(exec_result.returncode)
            if exec_result.stderr.decode():
                err = exec_result.stderr.decode()
                result.append(f"stderr: {err}")
            elif exec_result.stdout.decode():
                err = exec_result.stdout.decode()
                result.append(f"stdout: {err}")
            else:
                result.append('')
            if exec_result.returncode != 0:
                result[-1] = f"failed: returncode: {exec_result.returncode} " + result[-1] 
            else:
                result[-1] = "passed " + result[-1]
        except subprocess.TimeoutExpired as e:
            result.append("time out")
    
    logs = [[(0, dict(
        task_id=0,
        passed=result[0].startswith("passed"),
        result=result,
        completion_id=0,
    ))]]

    return {'pass@1': float(int(result[0].startswith("passed")))}, logs

    # program = predictions[0][0] + '\n' + references[0]
    # result = []
    # try:
    #     with time_limit(timeout):
    #         print('*' * 80)
    #         print(program)
    #         print('*' * 80)
    #         robjects.r(program)
    #     result.append('passed')
    # except TimeoutException:
    #     result.append("timed out")
    # except BaseException as e:
    #     result.append(f"failed: {e}")
    # logs = [[(0, dict(
    #     task_id=0,
    #     passed=result[0] == "passed",
    #     result=result[0],
    #     completion_id=0,
    # ))]]

    # return {'pass@1': float(int(result[0] == "passed"))}, logs


def python_exec_func(check_program, timeout, queue):
    try:
        with time_limit(timeout):
            exec(check_program, {})
        queue.put("passed")
    except TimeoutException:
        queue.put("timed out")
    except BaseException as e:
        queue.put(f"failed: {type(e)} {e}")

def python_unsafe_executor(references, predictions, timeout):

    check_program = predictions[0][0] + '\n' + references[0]

    parent_result = [None]

    q = Queue()
    p = Process(target=python_exec_func, args=(check_program, timeout, q))
    p.start()
    
    p_timeout = False

    start = time.time()
    while time.time() - start <= timeout:
        if not p.is_alive():
            # All the processes are done, break now.
            break
        time.sleep(0.5)  # Just to avoid hogging the CPU
    else:
        # We only enter this if we didn't 'break' above.
        parent_result = ["time out"]
        p_timeout = True
        p.terminate()
        p.join()
    
    if not p_timeout:
        parent_result = [q.get()]

    logs = [[(0, dict(
        task_id=0,
        passed=parent_result[0].startswith("passed"),
        result=parent_result,
        completion_id=0,
    ))]]

    return {'pass@1': float(int(parent_result[0] == "passed"))}, logs

def java_unsafe_executor(references, predictions, timeout):

    check_program = predictions[0][0] + '\n' + references[0]

    result = []

    with create_tempdir():
        open(f"Main.java", 'w').write(check_program)
        # Run program.
        try:
            exec_result = subprocess.run(["javac Main.java; java Main"], timeout=timeout, capture_output=True, shell=True)
            # print(exec_result.returncode)
            if exec_result.stderr.decode():
                err = exec_result.stderr.decode()
                result.append(f"stderr: {err}")
            elif exec_result.stdout.decode():
                err = exec_result.stdout.decode()
                result.append(f"stdout: {err}")
            else:
                result.append('')
            if exec_result.returncode != 0:
                result[-1] = f"failed: returncode: {exec_result.returncode} " + result[-1] 
            else:
                result[-1] = "passed " + result[-1]
        except subprocess.TimeoutExpired as e:
            result.append("time out")
    
    logs = [[(0, dict(
        task_id=0,
        passed=result[0].startswith("passed"),
        result=result,
        completion_id=0,
    ))]]

    return {'pass@1': float(int(result[0].startswith("passed")))}, logs

def cs_unsafe_executor(references, predictions, timeout):

    check_program = predictions[0][0] + '\n' + references[0]

    result = []

    with create_tempdir():
        open(f"main.cs", 'w').write(check_program)
        # Run program.
        try:
            exec_result = subprocess.run(["mcs -out:main.exe main.cs; mono main.exe"], timeout=timeout, capture_output=True, shell=True)
            # print(exec_result.returncode)
            if exec_result.stderr.decode():
                err = exec_result.stderr.decode()
                result.append(f"stderr: {err}")
            elif exec_result.stdout.decode():
                err = exec_result.stdout.decode()
                result.append(f"stdout: {err}")
            else:
                result.append('')
            if exec_result.returncode != 0:
                result[-1] = f"failed: returncode: {exec_result.returncode} " + result[-1] 
            else:
                result[-1] = "passed " + result[-1]
        except subprocess.TimeoutExpired as e:
            result.append("time out")
    
    logs = [[(0, dict(
        task_id=0,
        passed=result[0].startswith("passed"),
        result=result,
        completion_id=0,
    ))]]

    return {'pass@1': float(int(result[0].startswith("passed")))}, logs

def cpp_unsafe_executor(references, predictions, timeout):

    check_program = predictions[0][0] + '\n' + references[0]

    result = []

    with create_tempdir():
        open(f"main.cpp", 'w').write(check_program)
        # Run program.
        try:
            exec_result = subprocess.run(["g++ main.cpp -o main; ./main"], timeout=timeout, capture_output=True, shell=True)
            # print(exec_result.returncode)
            if exec_result.stderr.decode():
                err = exec_result.stderr.decode()
                result.append(f"stderr: {err}")
            elif exec_result.stdout.decode():
                err = exec_result.stdout.decode()
                result.append(f"stdout: {err}")
            else:
                result.append('')
            if exec_result.returncode != 0:
                result[-1] = f"failed: returncode: {exec_result.returncode} " + result[-1] 
            else:
                result[-1] = "passed " + result[-1]
        except subprocess.TimeoutExpired as e:
            result.append("time out")
    
    logs = [[(0, dict(
        task_id=0,
        passed=result[0].startswith("passed"),
        result=result,
        completion_id=0,
    ))]]

    return {'pass@1': float(int(result[0].startswith("passed")))}, logs

def sql_unsafe_executor(references, predictions, timeout):
    import sqlite3
    conn = sqlite3.connect(':memory:')
    cur = conn.cursor()
    result = []
    try:
        with time_limit(timeout):
            cur.execute(predictions[0][0] + '\n' + references[0])
        result.append("passed")
    except TimeoutException:
        result.append("timed out")
    except BaseException as e:
        result.append(f"failed: {e}")

    conn.close()

    logs = [[(0, dict(
        task_id=0,
        passed=result[0].startswith("passed"),
        result=result,
        completion_id=0,
    ))]]

    return {'pass@1': float(int(result[0] == "passed"))}, logs


def js_unsafe_executor(references, predictions, timeout):

    check_program = predictions[0][0] + '\n' + references[0]

    result = []

    with create_tempdir():
        open(f"test.js", 'w').write(check_program)
        # Run program.
        try:
            exec_result = subprocess.run(["node", "test.js"], timeout=timeout, capture_output=True)
            # print(exec_result.returncode)
            if exec_result.stderr.decode():
                err = exec_result.stderr.decode()
                result.append(f"stderr: {err}")
            elif exec_result.stdout.decode():
                err = exec_result.stdout.decode()
                result.append(f"stdout: {err}")
            else:
                result.append('')
            if exec_result.returncode != 0:
                result[-1] = f"failed: returncode: {exec_result.returncode} " + result[-1] 
            else:
                result[-1] = "passed " + result[-1]
        except subprocess.TimeoutExpired as e:
            result.append("time out")
    
    logs = [[(0, dict(
        task_id=0,
        passed=result[0].startswith("passed"),
        result=result,
        completion_id=0,
    ))]]

    return {'pass@1': float(int(result[0].startswith("passed")))}, logs


def ts_unsafe_executor(references, predictions, timeout):

    check_program = predictions[0][0] + '\n' + references[0]

    result = []

    with create_tempdir():
        open(f"test.ts", 'w').write(check_program)
        # Compile to js then run program.
        try:
            exec_result = subprocess.run(["npx tsc test.ts --outfile test.js; node test.js"], timeout=timeout, capture_output=True, shell=True)
            # with open('test.js', 'r') as f:
            #     print(f.read())
            # print(exec_result.returncode)
            if exec_result.stderr.decode():
                err = exec_result.stderr.decode()
                result.append(f"stderr: {err}")
            elif exec_result.stdout.decode():
                err = exec_result.stdout.decode()
                result.append(f"stdout: {err}")
            else:
                result.append('')
            if exec_result.returncode != 0:
                result[-1] = f"failed: returncode: {exec_result.returncode} " + result[-1] 
            else:
                result[-1] = "passed " + result[-1]
        except subprocess.TimeoutExpired as e:
            result.append("time out")
    
    logs = [[(0, dict(
        task_id=0,
        passed=result[0].startswith("passed"),
        result=result,
        completion_id=0,
    ))]]

    return {'pass@1': float(int(result[0].startswith("passed")))}, logs


def go_unsafe_executor(references, predictions, timeout):

    check_program = predictions[0][0] + '\n' + references[0]

    result = []

    with create_tempdir():
        open(f"main.go", 'w').write(check_program)

        try:
            exec_result = subprocess.run(["go", "run", "main.go"], timeout=timeout, capture_output=True)

            if exec_result.returncode == 0:
                result.append("passed")
            else:
                if exec_result.stderr:
                    try:
                        err = exec_result.stderr.decode()
                    except:
                        err = exec_result.stderr
                else:
                    try:
                        err = exec_result.stdout.decode()
                    except:
                        err = exec_result.stdout
                result.append(f"failed: {err}")
        except subprocess.TimeoutExpired as e:
            result.append("time out")
    
    logs = [[(0, dict(
        task_id=0,
        passed=result[0].startswith("passed"),
        result=result,
        completion_id=0,
    ))]]

    return {'pass@1': float(int(result[0].startswith("passed")))}, logs


# language supported by us
LANGUAGES = ["python", "cpp", "javascript", "typescript", "java", "go", "rust", "c#", 'r']

LANGUAGE_TO_NAME = {
    "python": "Python",
    "cpp": "C++",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java": "Java",
    "go": "Go",
    "rust": "Rust",
    "c#": "C#",
    'r': 'R'
}

LANGUAGE_TO_EXTENSION = {
    "python": "py",
    "cpp": "cpp",
    "javascript": "js",
    "typescript": "ts",
    "java": "java",
    "go": "go",
    "rust": "rs",
    "c#": "cs",
    'r': 'r'
}

# Taken from https://huggingface.co/datasets/nuprl/MultiPL-E/ & https://github.com/THUDM/CodeGeeX
LANGUAGE_TO_STOP_WORDS = {
    # https://github.com/THUDM/CodeGeeX/blob/23ee51505a2bcd34d59d2e271b22e5bd91475462/codegeex/benchmark/utils.py#L164
    "python": ["\nclass", "\ndef", "\n#", "\n@", "\nprint", "\nif", "\nassert"],
    # https://github.com/THUDM/CodeGeeX/blob/23ee51505a2bcd34d59d2e271b22e5bd91475462/codegeex/benchmark/utils.py#L185
    "cpp": [],
    # https://github.com/THUDM/CodeGeeX/blob/23ee51505a2bcd34d59d2e271b22e5bd91475462/codegeex/benchmark/utils.py#L188
    "javascript": [],
    "typescript": [],
    # https://github.com/THUDM/CodeGeeX/blob/23ee51505a2bcd34d59d2e271b22e5bd91475462/codegeex/benchmark/utils.py#L177
    "go": ["\n//", "\nfunc main(", "struct", "\nfunc"],
    # https://github.com/THUDM/CodeGeeX/blob/23ee51505a2bcd34d59d2e271b22e5bd91475462/codegeex/benchmark/utils.py#L169
    "java": [],
    "rust": [],
    "sql": [],
    "c#": [],
    'r': []
}

LANGUAGE_TO_TIMEOUT = {
    "python": 10,
    "cpp": 60,
    "javascript": 10,
    "typescript": 20,
    "java": 10,
    "go": 20,
    "rust": 300,  # Necessary for first-time compilation of cargo
    "sql": 10,
    "c#": 20,
    'r': 20
}

# Java sometimes fails with more workers; For JS it's twice as fast with 4 workers
LANGUAGE_TO_NUM_WORKERS = {
    "python": 4,
    "cpp": 4,
    "javascript": 4,
    "typescript": 4,
    "java": 1,
    "go": 4,
    "rust": 1,
    "sql": 1,
    "c#": 4,
    'r': 4
}

# https://github.com/THUDM/CodeGeeX/blob/23ee51505a2bcd34d59d2e271b22e5bd91475462/codegeex/benchmark/utils.py#L6
IMPORT_HELPER = {
    "python": [
        "import math",
        "import re",
        "import sys",
        "import copy",
        "import datetime",
        "import itertools",
        "import collections",
        "import heapq",
        "import statistics",
        "import functools",
        "import hashlib",
        "import numpy",
        "import numpy as np",
        "import pandas as pd",
        "import string",
        "import requests",
        "import openpyxl",
        "import xlsxwriter",
        "import yolk",
        "from typing import *",
        "from collections import *",
    ],
    "go": [
        "math",
        "strings",
        "fmt",
        "strconv",
        "time",
        "bytes",
        "regexp",
        "sort",
        "math/rand",
        "crypto/md5",
    ],
    "cpp": [
        "using namespace std;",
        "#include<stdlib.h>",
        "#include<algorithm>",
        "#include<cmath>",
        "#include<math.h>",
        "#include<numeric>",
        "#include<stdio.h>",
        "#include<vector>",
        "#include<set>",
        "#include<map>",
        "#include<queue>",
        "#include<stack>",
        "#include<list>",
        "#include<deque>",
        "#include<boost/any.hpp>",
        "#include<string>",
        "#include<climits>",
        "#include<cstring>",
        "#include<iostream>",
        "#include<sstream>",
        "#include<fstream>",
    ],
    "c#": [],
    'r': [
        'rm(list=ls())',
        'library(assert)',
    ]
}


def remove_last_block(code, lang):
    """
    Adapted from https://github.com/THUDM/CodeGeeX/blob/23ee51505a2bcd34d59d2e271b22e5bd91475462/codegeex/benchmark/utils.py#L151
    """
    stop_words = LANGUAGE_TO_STOP_WORDS[lang]
    for w in stop_words:
        if w in code:
            code = code[:code.find(w)]

    ### Find the first occassion where a chain of { } is closed
    if lang == "python":
        for i, line in enumerate(code.split("\n")):
            if len(line.strip()) > 0 and line[0] != ' ' and line[0] != '\t':
                return "\n".join(code.split("\n")[:i])
    elif lang in ["java", "javascript", "go", "cpp", "rust"]:
        open_brackets = 2 if lang == "java" else 1
        cut = False
        for i, c in enumerate(code):
            if c == '{':
                open_brackets += 1
            elif c == '}':
                open_brackets -= 1
            if open_brackets == 0:
                code = code[:i+1]
                cut = True
                break
        if not cut:
            if lang == "java":
                main_pos = code.find("public static void main")
                if main_pos != -1:
                    code = code[:main_pos] + '}'
                if '}' in code:
                    code = code[:code.rfind('}')] + '}'
                if code.count('{') - 1 == code.count('}'):
                    code += "\n}"
            elif '}' in code:
                code = code[:code.rfind('}')] + '}'
    return code


def preprocess(generations: List[str], lang: str, only_longest: bool) -> List[str]:
    """
        Extract code blocks from the generations
    :param generations:
    :param lang:
    :return: processed pure code blocks
    """
    ans = []
    for gen in generations:
        if gen.count('```') + gen.count('\\begin{code}') + gen.count('\\end{code}') >= 2:
            # TODO: just directly concatenate all code blocks
            # print(gen)
            lines = gen.split('\n')
            code_idendifier_lines = [no for no, text in enumerate(lines) if text.count("```") > 0 or text.count('\\begin{code}') > 0 or text.count('\\end{code}') > 0]
            # print(code_idendifier_lines)
            if only_longest:
                longest_lines = 0
                longest_lines_idx = 0
                for i in range(0, len(code_idendifier_lines)-1, 2):
                    if code_idendifier_lines[i+1] - code_idendifier_lines[i] > longest_lines:
                        longest_lines = code_idendifier_lines[i+1] - code_idendifier_lines[i]
                        longest_lines_idx = i
                if len(code_idendifier_lines) >= 2:
                    gen = '\n'.join(lines[code_idendifier_lines[longest_lines_idx] + 1:
                                            code_idendifier_lines[longest_lines_idx + 1]])
                else:
                    gen = ''
            else:
                gens = []
                for i in range(0, len(code_idendifier_lines)-1, 2):
                    now_gen = '\n'.join(lines[code_idendifier_lines[i] + 1:
                                              code_idendifier_lines[i + 1]])
                    gens.append(now_gen)
                gen = '\n\n'.join(gens)
        else:
            # function-signature form
            gen = remove_last_block(gen, lang)
        ans.append(gen)
    return ans


def get_exec_results(prefix_from_file: str, generations: List[str], references: str, lang: str,
                     timeout: None) -> Tuple[Dict[str, float], Dict[int, List], str]:
    """Takes the list of LM generations and evaluates them against ground truth references.

    :param prefix_from_file: universal setup code
    :param generations: list(str)
        list of string containing generations
    :param references: str
         str containing the test case
    """
    generations = [prefix_from_file + '\n' + gen for gen in generations]
    code_metric = load("code_eval_octopack")

    timeout = LANGUAGE_TO_TIMEOUT[lang] if timeout is None else timeout
    num_workers = LANGUAGE_TO_NUM_WORKERS[lang]

    ### CUSTOM PROG LANGUAGE CHANGES ###
    # Inspiration: https://github.com/THUDM/CodeGeeX/blob/ebeb850f227a90c79de39f7e26b1302f374f3240/codegeex/benchmark/evaluate_humaneval_x.py
    if lang == "python":
        python_imports = "\n".join(IMPORT_HELPER["python"])
        generations = [
            (python_imports + "\n" + g).strip() for g in generations
        ]
        # move "from __future__" to the head
        new_generations = []
        for gen in generations:
            gen_lines = gen.split('\n')
            gen_nonfuture_lines = []
            gen_future_lines = []
            for line in gen_lines:
                if line.startswith('from __future__'): 
                    gen_future_lines.append(line) 
                else: 
                    gen_nonfuture_lines.append(line)
            if len(gen_future_lines) > 0:
                print('. found and reorg __future__')
            new_generations.append("\n".join(gen_future_lines + gen_nonfuture_lines))
        generations = new_generations
    elif lang == "cpp":
        cpp_imports = "\n".join(IMPORT_HELPER["cpp"])
        # Remove main in case present
        generations = [
            # (cpp_imports + "\n" + g.split("int main")[0]).strip() for g in generations
            (cpp_imports + "\n" + g).strip() for g in generations
        ]
    elif lang == 'r':
        r_imports = '\n'.join(IMPORT_HELPER['r'])
        generations = [
            (r_imports + "\n" + g).strip() for g in generations
        ]

    # packaging to a suite of single instance for evaluation
    generations = [[gen] for gen in generations]
    references = [references]

    ### EVALUATION ###
    if lang == 'python':
        results, logs = python_unsafe_executor(
            references=references,
            predictions=generations,
            timeout=timeout,
        )
    elif lang == 'sql':
        results, logs = sql_unsafe_executor(
            references=references,
            predictions=generations,
            timeout=timeout,
        )
    elif lang == 'java':
        results, logs = java_unsafe_executor(
            references=references,
            predictions=generations,
            timeout=timeout,
        )
    elif lang in ['javascript', 'js']:
        results, logs = js_unsafe_executor(
            references=references,
            predictions=generations,
            timeout=timeout,
        )
    elif lang == 'typescript':
        results, logs = ts_unsafe_executor(
            references=references,
            predictions=generations,
            timeout=timeout,
        )
    elif lang == 'cpp':
        results, logs = cpp_unsafe_executor(
            references=references,
            predictions=generations,
            timeout=timeout,
        )
    elif lang == 'c#':
        results, logs = cs_unsafe_executor(
            references=references,
            predictions=generations,
            timeout=timeout,
        )
    elif lang == 'r':
        results, logs = r_executor(
            references=references,
            predictions=generations,
            timeout=timeout
        )
    elif lang == 'go':
        results, logs = go_unsafe_executor(
            references=references,
            predictions=generations,
            timeout=timeout,
        )
    else:
        results, logs = code_metric.compute(
            references=references,
            predictions=generations,
            language=lang,
            timeout=timeout,
            num_workers=num_workers,
        )
    # # Write logs to json
    # with open("logs.json", "w") as f:
    #     json.dump(logs, f, indent=4, ensure_ascii=False)

    """Debugging help
    for i, (gen, ref) in enumerate(zip(generations, references)):
        import time
        starttime = time.time()            
        results, log = code_metric.compute(
            references=[ref],
            predictions=[gen],
            language=language,
            timeout=timeout,
        )
        print("Took: ", time.time() - starttime)
        with open("errors.txt", "a") as f:
            f.write(log[0][0][1]["result"] + "\n")
        if ("compilation error" in log[0][0][1]["result"]):
            print("Result")
            print(results)
            print("Log")
            print(log)
            print("Gen")
            print(gen[0])
            print("Ref")
            print(ref)
    """
    """
    print(generations[0][0])
    print(references[0])
    print(logs)
    """

    print(lang, logs[0][0][1]['result'][0][:40])

    return results, logs, generations[0][0]


if __name__ == '__main__':
    # test the runtime of python and javascript
    code_eval = load("Muennighoff/code_eval_octopack")

    test_cases = ["assert add(2,3)==5"]
    candidates = [["def add(a,b): return a*b", "def add(a, b): return a+b"]]

    pass_at_k, results = code_eval.compute(references=test_cases, predictions=candidates, k=[1, 2], language="python")

    print(pass_at_k, results)

    test_cases = ["console.assert(add(2,3)==5)"]
    candidates = [["function add(a,b) { return a*b; }", "function add(a, b) { return a+b; }"]]

    pass_at_k, results = code_eval.compute(references=test_cases, predictions=candidates, k=[1, 2], language="javascript")

    print(pass_at_k, results)
