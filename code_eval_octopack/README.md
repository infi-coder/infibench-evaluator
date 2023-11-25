---
title: Code Eval OctoPack
emoji: 🐙
colorFrom: blue
colorTo: red
sdk: gradio
sdk_version: 3.19.1
app_file: app.py
pinned: false
tags:
- evaluate
- metric
description: >-
  This metric implements code evaluation with execution across multiple languages as used in the paper "OctoPack: Instruction Tuning
  Code Large Language Models" (https://arxiv.org/abs/2308.07124).
---

# Metric Card for Code Eval

## Metric description

The CodeEval metric estimates the pass@k metric for code synthesis. 

It implements the code exection for HumanEvalPack as described in the paper ["OctoPack: Instruction Tuning Code Large Language Model"](https://arxiv.org/abs/2308.07124).


## How to use 

The Code Eval metric calculates how good are predictions given a set of references. Its arguments are:

`predictions`: a list of candidates to evaluate. Each candidate should be a list of strings with several code candidates to solve the problem.

`references`: a list with a test for each prediction. Each test should evaluate the correctness of a code candidate.

`k`: number of code candidates to consider in the evaluation. The default value is `[1, 10, 100]`.

`num_workers`: the number of workers used to evaluate the candidate programs (The default value is `4`).

`timeout`: The maximum time taken to produce a prediction before it is considered a "timeout". The default value is `3.0` (i.e. 3 seconds).

`language`: Which language to execute the code in. The default value is `python` and alternatives are `javascript`, `java`, `go`, `cpp`, `rust`

`cargo_string`: The cargo installations to perform for Rust. Defaults to some basic packages, see `code_eval_octopack.py`.

```python
from evaluate import load
code_eval = load("Muennighoff/code_eval_octopack")
test_cases = ["assert add(2,3)==5"]
candidates = [["def add(a,b): return a*b", "def add(a, b): return a+b"]]
pass_at_k, results = code_eval.compute(references=test_cases, predictions=candidates, k=[1, 2], language="python")
```

N.B.
This metric exists to run untrusted model-generated code. Users are strongly encouraged not to do so outside of a robust security sandbox. Before running this metric and once you've taken the necessary precautions, you will need to set the `HF_ALLOW_CODE_EVAL` environment variable. Use it at your own risk:
```python
import os
os.environ["HF_ALLOW_CODE_EVAL"] = "1"` 
```

## Output values

The Code Eval metric outputs two things:

`pass_at_k`: a dictionary with the pass rates for each k value defined in the arguments.

`results`: a dictionary with granular results of each unit test.

## Examples 

Full match at `k=1`:

```python
from evaluate import load
code_eval = load("Muennighoff/code_eval_octopack")
test_cases = ["assert add(2,3)==5"]
candidates = [["def add(a, b): return a+b"]]
pass_at_k, results = code_eval.compute(references=test_cases, predictions=candidates, k=[1], language="python")
print(pass_at_k)
{'pass@1': 1.0}
```

No match for k = 1:

```python
from evaluate import load
code_eval = load("Muennighoff/code_eval_octopack")
test_cases = ["assert add(2,3)==5"]
candidates = [["def add(a,b): return a*b"]]
pass_at_k, results = code_eval.compute(references=test_cases, predictions=candidates, k=[1], language="python")
print(pass_at_k)
{'pass@1': 0.0}
```

Partial match at k=1, full match at k=2:

```python
from evaluate import load
code_eval = load("Muennighoff/code_eval_octopack")
test_cases = ["assert add(2,3)==5"]
candidates = [["def add(a, b): return a+b", "def add(a,b): return a*b"]]
pass_at_k, results = code_eval.compute(references=test_cases, predictions=candidates, k=[1, 2], language="python")
print(pass_at_k)
{'pass@1': 0.5, 'pass@2': 1.0}
```

## Citation

```bibtex
@article{muennighoff2023octopack,
      title={OctoPack: Instruction Tuning Code Large Language Models}, 
      author={Niklas Muennighoff and Qian Liu and Armel Zebaze and Qinkai Zheng and Binyuan Hui and Terry Yue Zhuo and Swayam Singh and Xiangru Tang and Leandro von Werra and Shayne Longpre},
      journal={arXiv preprint arXiv:2308.07124},
      year={2023}
}
```
