"""
    Dump the prompts of a benchmark suite to a csv, so we can call batch inference
"""

import yaml
import json
import os.path as osp
import argparse
import pandas as pd
import numpy as np
from tqdm import tqdm

# consistent with openai_caller.py
NON_QA_SYSTEM_PROMPT = "You are a professional assistant for programmers. By default, questions and answers are in Markdown format."
QA_SYSTEM_PROMPT = "You are a professional assistant for programmers. By default, questions and answers are in Markdown format. You are chatting with programmers, so please answer as briefly as possible."

# example command: python3 dump_prompts_to_csv.py suite_v1.yaml batched_prompts/suite_v1.csv [--tokenizer ../tokenizers/bbpe136k-v4.0]

# default sampling protocol should be aligned with openai_caller for temp=0.2, top_p=0.9

# uploaded to /home/byte_data_seed/hl_lq/seed_code/linyi.li/open-freeform-code-qa-suite/batched_prompts

parser = argparse.ArgumentParser()
parser.add_argument('suite_path', help='path to the suite definition')
parser.add_argument('out_csv_path', help='path to the output prompt parquet file')
parser.add_argument('--end_n', action='store_true', help='add \\n to the end of prompt, suitable for some models')
parser.add_argument('--tokenizer', default=None, help='path to the tokenizer, if provided, I will count the number of tokens in the prompt and output it as a field')
if __name__ == '__main__':
    args = parser.parse_args()

    tokenizer = None
    if args.tokenizer:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)

    with open(args.suite_path, 'r') as f:
        suite = yaml.load(f, yaml.Loader)
    
    idxes = []
    filenames = []
    question_types = []
    system_prompts = []
    content_prompts = []
    prompts = []
    n_tokens = []

    max_len = 0
    for no, case_path in tqdm(enumerate(suite['cases'])):
        res = {}
        res['idx'] = no
        full_case_path = osp.join(osp.dirname(args.suite_path), case_path)
        with open(full_case_path, 'r') as f:
            case = yaml.load(f, yaml.Loader)
        case_promptpath = case['prompt_path']
        full_case_promptpath = osp.join(osp.dirname(full_case_path), case_promptpath)
        with open(full_case_promptpath, 'r') as f:
            prompt = f.read()
        res['prompt'] = prompt
        res['filename'] = case_path
        res['question_type'] = case['type']
        case_grading_settings = case['grading']
        if 'similarity' in case_grading_settings and len(case_grading_settings) == 1:
            # primarily rouge-based QA
            system_prompt = QA_SYSTEM_PROMPT
        else:
            # non-rouge-based QA
            system_prompt = NON_QA_SYSTEM_PROMPT
        res['system_prompt'] = system_prompt
        if tokenizer:
            res['n_token'] = len(tokenizer.tokenize(system_prompt + '\n' + prompt))
            max_len = max(max_len, res['n_token'])

        idxes.append(res['idx'])
        filenames.append(res['filename'])
        question_types.append(res['question_type'])
        system_prompts.append(res['system_prompt'])
        content_prompts.append(res['prompt'])
        prompts.append(res['system_prompt'] + '\n' + res['prompt'] + ('\n' if args.end_n else ''))
        n_tokens.append(res.get('n_token', None))
    
    if tokenizer:
        print('max prompt len by tokens:', max_len)
        print('mean prompt len by tokens:', np.mean(n_tokens))

    pd.DataFrame({
        'idx': idxes,
        'filename': filenames,
        'question_type': question_types,
        'system_prompt': system_prompts,
        'content_prompt': content_prompts,
        'prompt': prompts,
        'n_token': n_tokens
    }).to_csv(args.out_csv_path)