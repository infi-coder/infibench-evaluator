"""
    This helper script generates answers from GPT4 / 3.5 by calling OpenAI APIs
"""
import random
import time
import os
import argparse
import yaml
from tqdm import tqdm
import openai

parser = argparse.ArgumentParser()
parser.add_argument('suite_path', help='File definition of the dataset suite')
parser.add_argument('model_name', help='Model to inquiry from OpenAI',
                    choices=["gpt-4", "gpt-4-0613", "gpt-4-32k", "gpt-4-32k-0613",
                             "gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-16k-0613"])
parser.add_argument('--temp', type=float, help='Sampling temperature', default=0.2)
parser.add_argument('--top_p', type=float, help='Sampling top probability', default=0.9)
parser.add_argument('--n', type=int, help='Sampling numbers', default=3)
parser.add_argument('--max_tokens', type=int, help='max tokens', default=None)
parser.add_argument('--timeout', type=int, help='timeout in seconds', default=300)
parser.add_argument('--patience', type=int, help='failure trials', default=3)
parser.add_argument('--key_path', help='API key to call OpenAI', default='openai_token.key')
parser.add_argument('--storage', help='Directory to store the prompting result', default='responses')
parser.add_argument('--expdir_suffix', help='Optional suffix added to the exp dir', default='')
parser.add_argument('--system_prompt', help='Prefix prompt as the system role',
                    default='You are a professional assistant for programmers. '
                            'By default, questions and answers are in Markdown format.')
parser.add_argument('--qa_system_prompt', help='Prefix prompt as the system role for rougeQA questions',
                    default='You are a professional assistant for programmers. '
                            'By default, questions and answers are in Markdown format. '
                            'You are chatting with programmers, so please answer as briefly as possible.')
parser.add_argument('--skip', action='store_true', help='whether to skip if already generated', default=False)


def single_turn(prompt, system_prompt, model_name, temp, top_p, n, max_tokens, timeout, patience, batch=2):
    ans = []
    orig_patience = patience

    attempt = 0
    print('')

    while len(ans) < n and patience > 0:
        print(f'  finish progress {len(ans)}/{n} atm={attempt}', end='\r', flush=True)
        patience = orig_patience
        config = {
            "temperature": temp,
            "top_p": top_p,
            "n": min(batch, n - len(ans)),
            "timeout": timeout,
        }
        if max_tokens is not None:
            config['max_tokens'] = max_tokens

        while patience > 0:
            patience -= 1
            attempt += 1
            try:
                response = openai.ChatCompletion.create(
                    engine=model_name,  # supported models: gpt-35-turbo, gpt-4, gpt-4-32k, gpt-4-32k-0613
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    **config
                )
                ans.extend([response['choices'][x]['message']['content'] for x in range(len(response['choices']))])
                break
            except Exception as e:
                print(f'attempt {attempt} (remaining: {patience}) error:', e)
                time.sleep(2 ** attempt + random.random() * 3)

    if len(ans) < n:
        # means sometimes it hits patience limit
        print(f'become impatient with {len(ans)} completions')
        return None
    else:
        return ans


if __name__ == '__main__':
    args = parser.parse_args()
    # load openai key
    with open(args.key_path, 'r') as f:
        api_url, api_key = f.readlines()[:2]
    api_url, api_key = api_url.strip(), api_key.strip()
    openai.api_type = "azure"
    openai.api_base = api_url
    openai.api_version = "2023-06-13"
    openai.api_key = api_key

    # create folder
    suite_basename = os.path.basename(args.suite_path)
    exp_name = f'{args.model_name}_{args.temp}_{args.top_p}_{args.n}_{suite_basename.rsplit(".", 1)[0]}{args.expdir_suffix}'
    exp_folder = os.path.join(args.storage, exp_name)
    if not os.path.exists(exp_folder):
        os.makedirs(exp_folder)
    print('Results stored to', exp_folder)

    # init params
    params = {
        'temp': args.temp,
        'model_name': args.model_name,
        'top_p': args.top_p,
        'sample_n': args.n,
        'max_tokens': args.max_tokens,
        'system_prompt': args.system_prompt,
        'qa_system_prompt': args.qa_system_prompt
    }
    answer_mapping = {}

    # start the evaluation
    with open(args.suite_path, 'r') as f:
        suite = yaml.load(f, yaml.Loader)
    # test loading all configs first
    for no, case in tqdm(enumerate(suite['cases'])):
        if isinstance(case, str):
            case_fpath = case
        else:
            case_fpath = case['path']
        case_fpath = os.path.join(os.path.dirname(args.suite_path), case_fpath)
        case_stemname = case_fpath.split('/')[-1].split('.')[0]
        with open(case_fpath, 'r') as f:
            tmp_conf = yaml.load(f, yaml.Loader)
    print('all cfgs can be successfully parsed')
    # really start the calling process
    for no, case in tqdm(enumerate(suite['cases'])):
        if isinstance(case, str):
            case_fpath = case
        else:
            case_fpath = case['path']
        case_fpath = os.path.join(os.path.dirname(args.suite_path), case_fpath)
        case_stemname = case_fpath.split('/')[-1].split('.')[0]

        if args.skip and all([os.path.exists(os.path.join(exp_folder, f'{case_stemname}_{j}.txt')) for j in range(args.n)]):
            answer_mapping[case_fpath] = []
            for j in range(args.n):
                outpath = f'{case_stemname}_{j}.txt'
                answer_mapping[case_fpath].append(outpath)
            continue

        with open(case_fpath, 'r') as f:
            tmp_conf = yaml.load(f, yaml.Loader)
            case_promptpath = tmp_conf['prompt_path']
            case_grading_settings = tmp_conf['grading']
        if 'similarity' in case_grading_settings and len(case_grading_settings) == 1:
            # primarily rouge-based QA
            system_prompt = args.qa_system_prompt
        else:
            system_prompt = args.system_prompt
        case_promptpath = os.path.join(os.path.dirname(case_fpath), case_promptpath)
        with open(case_promptpath, 'r') as f:
            prompt = f.read()
        responses = single_turn(prompt, system_prompt, args.model_name,
                                args.temp, args.top_p, args.n,
                                args.max_tokens, args.timeout, args.patience)
        if responses is not None:
            answer_mapping[case_fpath] = []
            for j, item in enumerate(responses):
                outpath = f'{case_stemname}_{j}.txt'
                answer_mapping[case_fpath].append(outpath)
                outpath = os.path.join(exp_folder, outpath)
                with open(outpath, 'w') as f:
                    f.write(item)

    # wrap up and store params
    params['answer_paths'] = answer_mapping
    with open(os.path.join(exp_folder, 'params.yaml'), 'w') as f:
        yaml.dump(params, f)


