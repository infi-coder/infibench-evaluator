import re
from typing import Union, Optional, List, Dict, Tuple
import numpy as np
from numba import njit
import time
import os
import importlib
import evaluate

from execution_utils import preprocess, get_exec_results


def keyword_match(rule: Union[str, Dict], to_lower: bool, regex: bool, response: str, context: List[str]) -> bool:
    if isinstance(rule, str):
        if to_lower:
            rule, response = rule.lower(), response.lower()
        if regex:
            return re.search(rule, response) is not None
        else:
            return rule in response
    else:
        # is a dict

        regex = regex
        # overwrite
        if 'regex' in rule: regex = rule['regex']

        if 'or' in rule:
            # OR clause
            ans = any([keyword_match(clause, to_lower, regex, response, context) for clause in rule['or']])
        elif 'and' in rule:
            # AND clause
            ans = all([keyword_match(clause, to_lower, regex, response, context) for clause in rule['and']])
        else:
            assert 'content' in rule
            ans = keyword_match(rule['content'], to_lower, regex, response, context)
        if 'cond' in rule:
            # available variables:
            #   context: ["unmatch", "match", "match", ....]
            #   ans: current judged sat status in bool
            ans = ans and eval(rule['cond'])
        return ans

@njit
def LCS(template: str, tgt: str) -> Tuple[np.ndarray, np.ndarray]:
    '''
        Longest Common Subsequence via dynamic programming
    :param template:
    :param tgt:
    :return: matched length map f, matched index map s
    '''
    f = np.zeros((int(len(template)), int(len(tgt))), dtype="int")
    s_all = np.zeros((int(len(template)), int(len(tgt))), dtype="int")

    for i in range(0, len(template)):
        for j in range(0, len(tgt)):
            if i*j > 0:
                if template[i] == tgt[j]:
                    f[i][j] = f[i-1][j-1] + 1
                    s_all[i][j] = j
                else:
                    f[i][j] = max(f[i][j-1], f[i-1][j])
                    if f[i][j-1] == f[i-1][j]:
                        # break tie by preferring the latter match
                        s_all[i][j] = max(s_all[i][j-1], s_all[i-1][j])
                    else:
                        s_all[i][j] = s_all[i][j-1] if f[i][j-1] >= f[i-1][j] else s_all[i-1][j]
            else:
                if template[i] == tgt[j]:
                    f[i][j] = 1
                    s_all[i][j] = j

    s = np.zeros(len(template), dtype="int")
    p = s_all[len(template)-1][len(tgt)-1]
    for i in range(len(template)-1, -1, -1):
        if template[i] == tgt[p]:
            s[i] = p
        else:
            # lookahead for one char
            s[i] = p+1
        if i > 0:
            if template[i] == tgt[p]:
                p = s_all[i-1][p-1]

    return f, s


def blank_filling_match(template: str, blank_str: str, escape: str, targets: List[Union[dict, str]], response: str,
                        post_handler: Optional[dict] = None) \
        -> Tuple[float, float, List[str]]:

    if response == '': response = ' ' # avoid the empty string problem
    f, s = LCS(template, response)
    n_blank = template.count(blank_str)
    blank_places = [i for i in range(len(template)) if template.startswith(blank_str, i)]
    assert n_blank == len(blank_places) and len(blank_places) == len(targets), \
        "Number of targets should be equal to number of blanks"

    matched_rate = f[len(template)-1][len(response)-1] / (len(template) - n_blank * len(blank_str))
    # print(f'Template following rate = {matched_rate:.3f}')

    now_score, tot_score = 0., 0.
    grading_details = []

    for no, target in enumerate(targets):
        weight = 1.0 if isinstance(target, str) else target.get('weight', 1.0)
        to_lower = False if isinstance(target, str) else target.get('to_lower', False)
        substr_match = False if isinstance(target, str) else target.get('substr_match', False)
        tot_score += weight

        if matched_rate < 0.8:
            grading_details.append(f'unmatched: match rate too low - {matched_rate}')
        else:
            if blank_places[no] == 0:
                response_str = response[s[blank_places[no]]: s[blank_places[no] + len(blank_str)]]
            else:
                # match longer
                response_str = response[s[blank_places[no] - 1] + 1: s[blank_places[no] + len(blank_str)]]
            response_str = response_str.strip(escape)

            # anses are or-clauses
            if isinstance(target, str):
                anses = [target]
            else:
                anses = target['content']
                if isinstance(anses, str):
                    anses = [anses]
                if isinstance(anses, str):
                    anses = [anses]

            matched = False
            now_status = 'unmatched'
            for ans in anses:
                ans_str = ans if isinstance(ans, str) else ans['content']
                ans_cond = None if isinstance(ans, str) else ans.get('cond', None)
                ans_re = False if isinstance(ans, str) else ans.get('regex', False)
                now_status = f'response string: {response_str}, ans: {ans_str}'
                if to_lower:
                    response_str, ans_str = response_str.lower(), ans_str.lower()
                # for ans_cond predicate, the available context is
                # - grading_details: list of string starting with "matched" or "unmatched"
                # - ans_str: str
                # - ans_re: bool
                # - response_str: str
                if not substr_match:
                    if (((not ans_re and response_str == ans_str) or (ans_re and re.fullmatch(ans_str, response_str) is not None))
                            and (ans_cond is None or eval(ans_cond))):
                        now_score += weight
                        now_status = 'matched: ' + now_status
                        matched = True
                        break
                else:
                    if (((not ans_re and response_str.count(ans_str) > 0) or (ans_re and re.search(ans_str, response_str))) and (ans_cond is None or eval(ans_cond))):
                        now_score += weight
                        now_status = 'matched: ' + now_status
                        matched = True
                        break

            if matched:
                grading_details.append(now_status)
            else:
                grading_details.append('unmatched: ' + now_status)

    post_handler_detail = None
    if post_handler is not None:
        # post_process the score
        module_name = post_handler['module']
        func_name = post_handler['func']

        custom_module = importlib.import_module(module_name)
        new_ans, new_tot, post_handler_detail = getattr(custom_module, func_name)(now_score, tot_score, grading_details)
        now_score = new_ans
        tot_score = new_tot

    return now_score, tot_score, grading_details, post_handler_detail


def unit_test_execution(lang: str, response: str, unit_tests: List[Union[str, Dict]], case_dir: str) \
        -> Tuple[float, float, List[Dict[str, str]]]:

    grading_details = []
    now_score = 0.
    tot_score = 0.
    for no, unit_test in enumerate(unit_tests):
        prefix = ''
        weight = 1.0
        prefix_from_file = ''
        timeout = None
        clean_up_code = ''
        only_longest = False
        if isinstance(unit_test, str):
            reference = unit_test
        else:
            if 'path' in unit_test:
                with open(os.path.join(case_dir, unit_test['path']), 'r') as f:
                    reference = f.read()
            else:
                assert 'content' in unit_test
                reference = unit_test['content']
            prefix = unit_test.get('prefix', '')
            prefix_path = unit_test.get('prefix_path', None)
            timeout = unit_test.get('timeout', None)
            if prefix_path is not None:
                with open(os.path.join(case_dir, prefix_path), 'r') as f:
                    prefix_from_file = f.read()
            if 'cleanup_path' in unit_test:
                with open(os.path.join(case_dir, unit_test['cleanup_path']), 'r') as f:
                    clean_up_code = f.read()
            weight = unit_test.get('weight', 1.0)
            only_longest = unit_test.get('only_longest', False)
        combined_response = prefix + '\n' + response

        tot_score += weight

        preprocessed_code = preprocess([combined_response], lang, only_longest)
        exec_passks, exec_details, code = get_exec_results(prefix_from_file, preprocessed_code, reference, lang, timeout)

        # cleanup
        if len(clean_up_code) > 0:
            exec(clean_up_code)

        now_score += float(exec_passks['pass@1']) * weight
        now_grading_detail = exec_details[0][0][1]
        now_grading_detail['code'] = code
        grading_details.append(now_grading_detail)

    return now_score, tot_score, grading_details


def similarity_assessment(response: str, similarity_metrics: List[Dict], case_dir: str) \
        -> Tuple[float, float, List[Dict[str, float]]]:
    now_score, tot_score = 0.0, 0.0
    grading_details = []

    rouge = evaluate.load('rouge')
    for metric in similarity_metrics:
        references = metric['references']
        passages = []
        for item in references:
            if isinstance(item, str):
                passages.append(item)
            else:
                with open(os.path.join(case_dir, item['path']), 'r') as f:
                    passages.append(f.read())
        results = rouge.compute(predictions=[response], references=[passages])
        results = dict([(k, float(v)) for k, v in results.items()])
        raw_score = results[metric['metric']]

        if 'min_score' in metric:
            min_score = float(metric['min_score'])
        else:
            min_score = 0.3
        if 'max_score' in metric:
            max_score = float(metric['max_score'])
        elif metric['metric'] == 'rouge1':
            max_score = 0.53
        else:
            max_score = 0.51
        normalized_score = max(min((raw_score - min_score) / (max_score - min_score), 1.0), 0.0)
        weight = metric.get('weight', 1.0)
        tot_score += weight
        now_score += normalized_score * weight

        results['normalized_score'] = normalized_score
        grading_details.append(results)

    return now_score, tot_score, grading_details


# if __name__ == '__main__':
#     # numba test
#     a = 'ba' * 5000
#     b = 'ab' * 5000
#     stime = time.time()
#     f, s = LCS(a, b)
#     print('time elapsed =', time.time() - stime)
