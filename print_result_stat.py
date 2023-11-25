import os
import yaml
import numpy as np
import argparse
from matplotlib import pyplot as plt
import pandas as pd
import io

def compute_stats(file_path: str):
    bsz = 10

    with open(file_path, 'r') as f:
        full_results = yaml.load(f, yaml.Loader)
    peritem_full_score = {}
    peritem_get_scores = []
    peritem_freq = {}
    perlang_full_score = {}
    perlang_get_scores = []
    perlang_freq = {}
    perarea_full_score = {}
    perarea_get_scores = []
    perarea_freq = {}
    tot_scores = []
    full_score = 0.
    
    fields = ['keywords', 'blank_filling', 'unit_test', 'similarity', 'custom']
    
    for case_name, case_report in full_results.items():
        case_full_score = case_report['full_score']
        
        best_scores = []
        best_response_peritem_get_scores = []
        for s in range(0, len(case_report['detail']), bsz):
            # locate the instance with highest score
            best_score = 0.
            best_response_peritem_full_score = {}
            best_response_peritem_get_score = {}
            for response_report in case_report['detail'][s: s+bsz]:
                now_score = 0.
                response_peritem_full_score = {}
                response_peritem_get_score = {}
                for field in fields:
                    if field + '_score' in response_report:
                        now_score += response_report[field + '_score']
                        nfield = field
                        if field == 'custom':
                            # check what is the real metric type
                            with open(case_name, 'r') as f:
                                case_cfg = yaml.load(f, yaml.Loader)
                                nfield = case_cfg['grading']['customized'].get('real_metric_type', field)
                        response_peritem_full_score[nfield] = response_report[field + '_totscore']
                        response_peritem_get_score[nfield] = response_report[field + '_score']
                if now_score >= best_score:
                    best_score = now_score
                    best_response_peritem_full_score = response_peritem_full_score
                    best_response_peritem_get_score = response_peritem_get_score
            best_scores.append(best_score)
            best_response_peritem_get_scores.append(best_response_peritem_get_score)

        tot_case_score = sum(best_response_peritem_full_score.values())
        # overwrite max_score
        if 'max_score' in case_report['detail'][0]:
            tot_case_score = case_report['detail'][0]['max_score']
        best_scores = [min(score, tot_case_score) / tot_case_score for score in best_scores]
        # print(case_name)
        assert np.mean(best_scores) == case_report['now_score'], f"diff found, buggy stat script: {np.mean(best_scores)} vs. {case_report['now_score']}"

        for item in best_response_peritem_full_score:
            best_response_peritem_full_score[item] *= case_full_score / tot_case_score
            for best_response_peritem_get_score in best_response_peritem_get_scores:
                best_response_peritem_get_score[item] *= case_full_score / tot_case_score
        
        for item in best_response_peritem_full_score:
            if item not in peritem_full_score:
                peritem_full_score[item] = 0.
                peritem_freq[item] = 0.
            peritem_full_score[item] += best_response_peritem_full_score[item]
            peritem_freq[item] += 1

        for i, best_response_peritem_get_score in enumerate(best_response_peritem_get_scores):
            if len(peritem_get_scores) <= i:
                peritem_get_scores.append({})
            for item in best_response_peritem_get_score:
                if item not in peritem_get_scores[i]:
                    peritem_get_scores[i][item] = 0.
                peritem_get_scores[i][item] += best_response_peritem_get_score[item]

        for i, best_score in enumerate(best_scores):
            if len(tot_scores) <= i:
                tot_scores.append(0.)
            tot_scores[i] += best_score
        
        now_lang = case_report['lang']
        now_area = case_report['type']
        
        full_score += case_report['full_score']
        
        for i, best_score in enumerate(best_scores):
            if len(perlang_get_scores) <= i:
                perlang_get_scores.append({})
            if now_lang not in perlang_get_scores[i]:
                perlang_get_scores[i][now_lang] = 0.
            perlang_get_scores[i][now_lang] += best_score
        
            if i == 0:
                if now_lang not in perlang_full_score:
                    perlang_full_score[now_lang] = 0.
                    perlang_freq[now_lang] = 0.
                perlang_full_score[now_lang] += case_full_score
                perlang_freq[now_lang] += 1.
        
        for i, best_score in enumerate(best_scores):
            if len(perarea_get_scores) <= i:
                perarea_get_scores.append({})
            if now_area not in perarea_get_scores[i]:
                perarea_get_scores[i][now_area] = 0.
            perarea_get_scores[i][now_area] += best_score

            if i == 0:
                if now_area not in perarea_full_score:
                    perarea_full_score[now_area] = 0.
                    perarea_freq[now_area] = 0.
                perarea_full_score[now_area] += case_full_score
                perarea_freq[now_area] += 1.
        
    langs = list(perlang_get_scores[0].keys())
    areas = list(perarea_get_scores[0].keys())
    
    print(tot_scores)

    return {
        'tot_score': np.mean(tot_scores),
        'tot_std': np.std(tot_scores, ddof=1) if len(tot_scores) > 1 else 0.,
        'tot_full_score': full_score,
        'lang': langs,
        'area': areas,
        'field': fields,
        'perarea_freq': perarea_freq,
        'perarea_get_score': {k: np.mean([perarea_get_score[k] for perarea_get_score in perarea_get_scores]) for k in perarea_get_scores[0]},
        'perarea_get_score_std': {k: np.std([perarea_get_score[k] for perarea_get_score in perarea_get_scores], ddof=1) if len(perarea_get_scores) > 1 else 0.0 for k in perarea_get_scores[0]},
        'perarea_full_score': perarea_full_score,
        'perlang_freq': perlang_freq,
        'perlang_get_score': {k: np.mean([perlang_get_score[k] for perlang_get_score in perlang_get_scores]) for k in perlang_get_scores[0]},
        'perlang_get_score_std': {k: np.std([perlang_get_score[k] for perlang_get_score in perlang_get_scores], ddof=1) if len(perlang_get_scores) > 1 else 0.0 for k in perlang_get_scores[0]},
        'perlang_full_score': perlang_full_score,
        'peritem_freq': peritem_freq,
        'peritem_get_score': {k: np.mean([peritem_get_score[k] for peritem_get_score in peritem_get_scores]) for k in peritem_get_scores[0]},
        'peritem_get_score_std': {k: np.std([peritem_get_score[k] for peritem_get_score in peritem_get_scores], ddof=1) if len(peritem_get_scores) > 1 else 0.0 for k in peritem_get_scores[0]},
        'peritem_full_score': peritem_full_score
    }

def tab_gen(stats, cols):
    cols = [''] + sum([[col, '', '', ''] for col in cols], []) + ['Full Score', 'Allocation']
    lines = [cols]
    # Tot score
    lines.append(['Overall Score'] + sum([[stat['tot_score'], stat['tot_std'], stat['tot_score'] / stats[0]['tot_full_score'], stat['tot_std'] / stats[0]['tot_full_score']] for stat in stats], []) + [stats[0]['tot_full_score'], ''])
    # Score by Lang
    lang_ranks = sorted(stats[0]['lang'], key=lambda x: stats[0]['perlang_full_score'][x], reverse=True)
    lines += [['Lang: ' + lang] + sum([[stat['perlang_get_score'][lang], stat['perlang_get_score_std'][lang], stat['perlang_get_score'][lang] / stats[0]['perlang_full_score'][lang], stat['perlang_get_score_std'][lang] / stats[0]['perlang_full_score'][lang]] for stat in stats], []) + [stats[0]['perlang_full_score'][lang], stats[0]['perlang_full_score'][lang] / stats[0]['tot_full_score']] for lang in lang_ranks]
    # Score by Area
    area_ranks = sorted(stats[0]['area'], key=lambda x: stats[0]['perarea_full_score'][x], reverse=True)
    lines += [['Type: ' + area] + sum([[stat['perarea_get_score'][area], stat['perarea_get_score_std'][area], stat['perarea_get_score'][area] / stats[0]['perarea_full_score'][area], stat['perarea_get_score_std'][area] / stats[0]['perarea_full_score'][area]] for stat in stats], []) + [stats[0]['perarea_full_score'][area], stats[0]['perarea_full_score'][area] / stats[0]['tot_full_score']] for area in area_ranks]
    # Score by Evaluation metric
    item_ranks = sorted(stats[0]['peritem_full_score'].keys(), key=lambda x: stats[0]['peritem_full_score'][x], reverse=True)
    lines += [['Metric: ' + item] + sum([[stat['peritem_get_score'][item], stat['peritem_get_score_std'][item], stat['peritem_get_score'][item] / stats[0]['peritem_full_score'][item], stat['peritem_get_score_std'][item] / stats[0]['peritem_full_score'][item]] for stat in stats], []) + [stats[0]['peritem_full_score'][item], stats[0]['peritem_full_score'][item] / stats[0]['tot_full_score']] for item in item_ranks]
    return lines

def to_text(tab, csv_fmt=False):
    ncols = len(tab[0])
    max_lens = [0 for _ in range(ncols)]
    for row in tab:
        for j, item in enumerate(row):
            if isinstance(item, str): 
                max_lens[j] = max(max_lens[j], len(item))
            elif isinstance(item, float):
                if j in [1,2,5]:
                    row[j] = f'{item:.2f}' 
                else:
                    row[j] = f'{item * 100.:.2f}%'
                if j in [2,4]:
                    row[j] = '±' + row[j] # std
                max_lens[j] = max(max_lens[j], len(row[j]))
    splitter = '|'.join(['-' * (max_lens[i] + 2) for i in range(ncols)])
    header = '-' * len(splitter)
    if csv_fmt:
        df = pd.DataFrame(tab)
        with io.StringIO() as f:
            df.to_csv(f)
            ans = f.getvalue()
        return ans
    else:
        contents = []
        for row in tab:
            formatted_row = [row[j].ljust(max_lens[j]+1).rjust(max_lens[j]+2) for j in range(ncols)]
            contents.append(formatted_row[0] + '|' + formatted_row[1] + ' ' + formatted_row[2] + '|' + formatted_row[3] + ' ' + formatted_row[4] + '|' + '|'.join(formatted_row[5:]))
        return '\n'.join([header, contents[0], splitter] + contents[1:] + [header])

parser = argparse.ArgumentParser()
parser.add_argument('result_yaml_path', type=str)
parser.add_argument('result_table_path', type=str)
parser.add_argument('--model_name', type=str, default='This Model')
if __name__ == '__main__':
    args = parser.parse_args()
    in_path = args.result_yaml_path
    out_path = args.result_table_path
    if os.path.dirname(out_path):
        if not os.path.exists(os.path.dirname(out_path)):
            os.makedirs(os.path.dirname(out_path))
    
    stats = compute_stats(in_path)
    tab = tab_gen([stats], [args.model_name])
    tab_text = to_text(tab, out_path.endswith('.csv'))

    with open(out_path, 'w') as f:
        f.write(tab_text)
    print('Write to', out_path)
    print('Final Result:')
    print(tab_text)
