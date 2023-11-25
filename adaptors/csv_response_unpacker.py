"""
    Unpack the inference results generated from our inference engine from a parquet file to the folder format to benchmark.
"""
import os
import os.path as osp
import pandas as pd
import yaml
import argparse
from dump_prompts_to_parquet import NON_QA_SYSTEM_PROMPT, QA_SYSTEM_PROMPT

# Usage: python3 csv_response_unpacker [csv path] [output folder path, if not exists will create]
# Example: python3 csv_response_unpacker.py ../tmp/suite_v1-output.csv responses/100b-mogao-0.2-0.9-10

parser = argparse.ArgumentParser()
parser.add_argument('csv_path', help='path to the csv response file from autoeval batch inference')
parser.add_argument('out_folder', help='path to the output folder')
parser.add_argument('--meta_data_max_tokens', help='max tokens stored in the metadata', default=None)
parser.add_argument('--meta_data_model_name', help='model name stored in the metadata', default='test model')
parser.add_argument('--meta_data_qa_system_prompt', help='qa system prompt stored in the metadata', default=QA_SYSTEM_PROMPT)
parser.add_argument('--meta_data_system_prompt', help='system prompt stored in the metadata', default=NON_QA_SYSTEM_PROMPT)
parser.add_argument('--meta_data_temp', help='temperature stored in the metadata', default=0.2)
parser.add_argument('--meta_data_top_p', help='top p probability stored in the metadata', default=0.9)

if __name__ == '__main__':
    args = parser.parse_args()

    df = pd.read_csv(args.csv_path)

    if not osp.exists(args.out_folder):
        os.makedirs(args.out_folder)

    params = {
        'max_tokens': args.meta_data_max_tokens,
        'model_name': args.meta_data_model_name,
        'qa_system_prompt': args.meta_data_qa_system_prompt,
        'system_prompt': args.meta_data_system_prompt,
        'temp': args.meta_data_temp,
        'top_p': args.meta_data_top_p
        # TODO parse: sample_n
        # TODO parse: answer_paths
    }
    
    sample_n = None
    answer_paths = {}
    tot_cases = 0
    null_cells = 0
    null_cases = set()
    for i, row in df.iterrows():
        tot_cases += 1
        # case_fpath = row['filename'][0]
        # responses = row['responses']
        # case_idx = row['idx']
        # # print(case_fpath)
        # # print(case_idx)
        # # print(responses)

        case_fpath = row['filename']
        if pd.isna(row['completion']):
            null_cells += 1
            responses = ''
            null_cases.add(case_fpath)
        else:
            responses = str(row['completion'])

        case_barepath = case_fpath.split('/')[-1].split('.')[0]
        if case_fpath in answer_paths:
            pass
        else:
            answer_paths[case_fpath] = []

        base_name = f'{case_barepath}_{len(answer_paths[case_fpath])}.txt'
        answer_paths[case_fpath].append(base_name)

        now_case_path = osp.join(args.out_folder, base_name)
        print('out to', now_case_path)
        with open(now_case_path, 'w') as f:
            f.write(responses)
    
    params['answer_paths'] = answer_paths
    params['sample_n'] = sample_n
    with open(osp.join(args.out_folder, 'params.yaml'), 'w')  as f:
        yaml.dump(params, f)
    print('# Tot cases:', tot_cases)
    print('# Empty Responses:', null_cells, 'They are in', null_cases)
