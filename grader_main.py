import os
import argparse
import importlib
import traceback

import yaml
from typing import Optional, List, Dict, Tuple
import numpy as np

from tqdm import tqdm

import grader_utils as utils


def grade_response(config: dict, case_dir: str, response: str, full_score: float, null_score: float) -> Tuple[float, dict]:
    """
        Return current score and detail explanation
    :param config:
    :param case_dir:
    :param response:
    :param full_score:
    :param null_score:
    :return:
    """
    status = dict()
    ans = 0.
    tot = 0.

    if 'lang' not in config:
        print(f'Warning: language not specified in case {config["id"]}')
    if 'type' not in config:
        print(f'Warning: question type not specified in case {config["id"]}')
    elif config['type'] not in ['code debugging', 'code completion', 'knowledge question-answering', 'non-code debugging']:
        print(f'Warning: unusual question type (config["type"]) in case {config["id"]}')

    # four types of evaluation metrics + customized
    if 'keywords' in config['grading']:
        """
            keywords:
                - "xxxxx"
                - content: "xxxxxx"
                  *weight: 2.0
                  *to_lower: true (default: false)
                - content: 
                    content: "xxxx"
                    or:
                        xxx (recursive)
                    and:
                        xxx (recursive)
                    *cond: "context[-1] == 'match'"
                    *regex: true (by default false)
        """

        now_ans, now_tot = 0.0, 0.0

        default_weight = 1.0

        post_handler = None

        status['keywords'] = list()
        for rule in config['grading']['keywords']:
            if isinstance(rule, str):
                rule_content = rule
                rule_weight = default_weight
                to_lower = False
                neg = False
            else:
                if 'post_handler' in rule:
                    post_handler = rule['post_handler']
                    continue
                rule_content = rule['content']
                rule_weight = float(rule.get('weight', default_weight))
                to_lower = bool(rule.get('to_lower', False))
                neg = bool(rule.get('neg', False))

            if utils.keyword_match(rule_content, to_lower, False, response, status['keywords']):
                status['keywords'].append('match')
                now_ans += rule_weight if not neg else -rule_weight
            else:
                status['keywords'].append('unmatch')
            now_tot += rule_weight if not neg else 0.

        if post_handler is not None:
            # post_process the score
            module_name = post_handler['module']
            func_name = post_handler['func']

            custom_module = importlib.import_module(module_name)
            new_ans, new_tot, new_detail = getattr(custom_module, func_name)(now_ans, now_tot, status['keywords'])
            status['post_handler_detail'] = new_detail
            now_ans = new_ans
            now_tot = new_tot

        status['keywords_score'] = now_ans
        status['keywords_totscore'] = now_tot
        ans, tot = ans + now_ans, tot + now_tot

    if 'blank_filling' in config['grading']:
        """
            blank_filling:
                template: "xxxxx[blank]xxxx xxxx [blank] xxx"
                *blank_str: [blank]
                *escape: " '\""
                *prefix: ""
                targets:
                    - aaa
                    - content:
                        - bbb
                        - bbbbb
                    - ccc
                    - content: ddd
                      *weight: 2.0
                      *to_lower: true (default: false)
                    - content: 
                        - eee
                        - fff
                        - content: ggg (no recursion)
                          *cond: grading_details[-1].startswith("unmatch") 
                          *regex: true (default: false)
                      *weight: 2.0
                      *to_lower: true (default: false)
                    - ...
        """

        blank_filling_config = config['grading']['blank_filling']

        default_escape = ' \'"`'

        template = blank_filling_config['template']
        blank_str = blank_filling_config.get('blank_str', '[blank]')
        escape = blank_filling_config.get('escape', default_escape)
        targets = blank_filling_config['targets']
        prefix = blank_filling_config.get('prefix', '')
        post_handler = blank_filling_config.get('post_handler', None)

        now_ans, now_tot, now_detail, post_handler_detail = utils.blank_filling_match(template, blank_str, escape, targets, prefix + response, post_handler)

        status['blank_filling_score'] = now_ans
        status['blank_filling_totscore'] = now_tot
        status['blank_filling_detail'] = now_detail
        if post_handler_detail is not None:
            status['blank_filling_post_handler_detail'] = post_handler_detail
        ans, tot = ans + now_ans, tot + now_tot

    if 'unit_test' in config['grading']:
        """
            unittest:
                *lang: "java/python/javascript/c++/c" # overwrite the test case language
                tests:
                    - "xxxxxx"
                    - path: "xxxxx"
                      *prefix: "xxxxx" (usually contains signature etc)
                      *weight: 2.0 (default: 1.0)
                    - content: "xxxxx"
                      *prefix: "xxxxx"
        """

        unit_test_config = config['grading']['unit_test']

        lang = config['lang']
        if 'lang' in unit_test_config:
            lang = unit_test_config['lang']

        if lang == 'python':
            lang = 'python'
        elif lang in ['c', 'c++', 'cpp', 'c/c++', 'c++/c', 'cpp/c', 'c/cpp']:
            lang = 'cpp'
        elif lang in ['js', 'javascript']:
            lang = 'javascript'
        # elif lang == 'custom-py':
        #     lang = 'custom-py'
        elif lang == 'java':
            lang = 'java'
        elif lang in ['c#', 'c-sharp', 'csharp', 'cs']:
            lang = 'c#'
        elif lang in ['ts', 'typescript']:
            lang = 'typescript'
        elif lang == 'r':
            lang = 'r'
        elif lang == 'go':
            lang = 'go'
        else:
            raise NotImplementedError(f'Does not support this language yet: {lang}.')

        now_ans, now_tot, now_detail = utils.unit_test_execution(lang, response, unit_test_config['tests'], case_dir)

        status['unit_test_score'] = now_ans
        status['unit_test_totscore'] = now_tot
        status['unit_test_detail'] = now_detail
        ans, tot = ans + now_ans, tot + now_tot

    if 'similarity' in config['grading']:
        """
            similarity:
                - metric: rouge1/rouge2/rougeL/rougeLsum
                  references:
                    - xxxx
                    - path: xxxx
                    - ...
                  *max_score: 0.xx (default 0.51 for others, 0.53 for rouge1)
                  *min_score: 0.xx (default 0.30 for rougeL, and same for rouge1)
                  *weight: xxx (default 1.0)
            min/max score set according to https://docs.oneai.com/docs/rouge-metrics-for-summary-headline
            => means the final score would be "sum(weight * clip( (raw_score - min_score) / (max_score - min_score), 0, 1))"
        """

        similarity_config = config['grading']['similarity']
        now_ans, now_tot, now_detail = utils.similarity_assessment(response, similarity_config, case_dir)

        status['similarity_score'] = now_ans
        status['similarity_totscore'] = now_tot
        status['similarity_detail'] = now_detail

        ans, tot = ans + now_ans, tot + now_tot

    if 'customized' in config['grading']:

        customized_config = config['grading']['customized']
        module_name = customized_config['module']
        func_name = customized_config['func']

        custom_module = importlib.import_module(module_name)
        now_ans, now_tot, now_detail = getattr(custom_module, func_name)(response)

        status['custom_score'] = now_ans
        status['custom_totscore'] = now_tot
        status['custom_detail'] = now_detail

        ans, tot = ans + now_ans, tot + now_tot

    if 'max_score' in config['grading']:
        tot = config['grading']['max_score']
        status['max_score'] = config['grading']['max_score']
        ans = min(ans, tot)
    if 'min_score' in config['grading']:
        ans = max(ans, config['grading']['min_score'])
        status['min_score'] = config['grading']['min_score']

    if ans < 0.:
        print(f'Warning: negative score ({ans}) found in case id {config["id"]}')

    # print(f'Score: {ans} / {tot} -> {(ans / tot) * full_score:.3f}')
    return (ans / tot) * full_score, status


def grade_responses(config: dict, case_dir: str, responses: Optional[List[str]],
                    reduce_mode: str, suite_full_score: float, suite_null_score: float) -> Tuple[float, float, List[dict]]:
    """

    :param config:
    :param case_dir:
    :param responses:
    :param reduce_mode:
    :param suite_full_score:
    :param suite_null_score:
    :return: current score, question full score, and list of dict explaining score for each response
    """
    full_score = config.get('full_score', suite_full_score)
    null_score = config.get('null_score', suite_null_score)
    if responses is None:
        return null_score, full_score, []
    else:
        all_scores_details = [grade_response(config, case_dir, response, full_score, null_score)
                              for response in responses]
        all_scores = [s for s, d in all_scores_details]
        all_details = [d for s, d in all_scores_details]
        if reduce_mode == 'avg':
            score = float(np.average(all_scores))
            std = 0.
        elif reduce_mode == 'max':
            score = float(np.max(all_scores))
            std = 0.
        elif reduce_mode == 'min':
            score = float(np.min(all_scores))
            std = 0.
        elif reduce_mode.startswith('avg_max_'):
            batch = int(reduce_mode[len('avg_max_'): ])
            buk_score = []
            for i in range(0, len(all_scores), batch):
                buk_score.append(float(np.max(all_scores[i:i+batch])))
            score = float(np.mean(buk_score))
            if len(buk_score) > 1:
                std = float(np.std(buk_score, ddof=1))
            else:
                std = 0.
        else:
            raise NotImplementedError(f'Unsupported score reduction mode: {reduce_mode}')
        return score, std, full_score, all_details


parser = argparse.ArgumentParser()
parser.add_argument('suite_path', help='file path to the test suite definition')
parser.add_argument('responses_dir', help='directory path to the responses to grade')
parser.add_argument('--result_detail_path', help='path to store the detailed evaluation result in yaml format',
                    default=None)
parser.add_argument('--result_summary_path', help='path to store the printing friendly report in txt format',
                    default=None)
parser.add_argument('--select', help='select cases to evaluate according to case name in the suite',
                    nargs='*')
if __name__ == '__main__':
    args = parser.parse_args()

    with open(args.suite_path, 'r') as f:
        suite_defs = yaml.load(f, yaml.Loader)
    with open(os.path.join(args.responses_dir, 'params.yaml'), 'r') as f:
        response_info = yaml.load(f, yaml.Loader)
    response_paths = response_info['answer_paths']

    # load default settings
    attempt_reduce_mode = suite_defs.get('attempt_reduce_mode', 'avg')
    full_score_per_question = suite_defs.get('full_score_per_question', 1.0)
    null_score_per_question = suite_defs.get('null_score_per_question', 0.0)

    tot_cases = 0
    tot_cases_with_response = 0
    tot_full_score = 0.
    tot_now_score = 0.
    tot_std = 0.
    results = {}
    keyboard_interrupt = False
    pbar = tqdm(suite_defs['cases'])
    for case in pbar:
        if args.select and len(args.select) > 0 and case not in args.select: continue

        tot_cases += 1

        if isinstance(case, str):
            case_fname, case_weight = case, 1.0
        else:
            case_fname, case_weight = case['path'], float(case['weight'])

        # extract responses
        now_responses = None
        if case_fname in response_paths:
            # response found
            tot_cases_with_response += 1
            now_responses = []
            for response_path in response_paths[case_fname]:
                with open(os.path.join(args.responses_dir, response_path), 'r') as f:
                    now_responses.append(f.read())

        # rebase the case filename
        rebased_case_fname = os.path.join(os.path.dirname(args.suite_path), case_fname)
        with open(case_fname, 'r') as f:
            case_config = yaml.load(f, yaml.Loader)
        case_dir = os.path.dirname(rebased_case_fname)

        # 
        print(case_fname)

        try:
            now_score, now_std, full_score, detail_info = grade_responses(
                case_config, case_dir, now_responses,
                attempt_reduce_mode, full_score_per_question, null_score_per_question)
            tot_full_score += full_score
            tot_now_score += now_score
            tot_std += now_std
            results[case_fname] = {'full_score': full_score, 'now_score': now_score, 'now_std': now_std, 'detail': detail_info}
        except KeyboardInterrupt as e:
            # User interrupted
            keyboard_interrupt = True
            break
        except BaseException as e:
            results[case_fname] = {'full_score': 0., 'now_score': 0., 'now_std': 0.,
                                   'detail': {'info': 'error encountered', 'error_obj': str(e)}}
            print(traceback.format_exc())
        for field in case_config:
            # add other fields to detail results for later statistics
            if field != 'grading':
                results[case_fname][field] = case_config[field]
        pbar.set_description(f'Lang:{case_config["lang"]} CurScore={tot_now_score:4.1f}(est±{tot_std:.1f})/{tot_full_score}={(tot_now_score / tot_full_score * 100. if full_score > 0. else 0.):5.2f}%')

    summary_txt = f"""Total score: {tot_now_score} ± {tot_std} / {tot_full_score}
Total cases: {tot_cases}
Total cases with response: {tot_cases_with_response}
    """
    print(summary_txt)
    if keyboard_interrupt:
        print('Keyboard interrupted')
        exit(1)
    if args.result_summary_path is None:
        stem_filename = f'results/{os.path.basename(args.suite_path).rsplit(".", 1)[0]}_{os.path.basename(args.responses_dir.strip("/"))}'
        print(f'Output to {stem_filename}.(txt/yaml)')
        args.result_summary_path = stem_filename + '.txt'
        args.result_detail_path = stem_filename + '.yaml'
    if os.path.dirname(args.result_detail_path):
        if not os.path.exists(os.path.dirname(args.result_detail_path)):
            os.makedirs(os.path.dirname(args.result_detail_path))
    if os.path.dirname(args.result_summary_path):
        if not os.path.exists(os.path.dirname(args.result_summary_path)):
            os.makedirs(os.path.dirname(args.result_summary_path))
    with open(args.result_summary_path, 'w') as f:
        f.write(summary_txt)
    with open(args.result_detail_path, 'w') as f:
        yaml.dump(results, f, yaml.Dumper)
