"""
    Unpack the inference results generated from our inference engine from a parquet file to the folder format to benchmark.
"""
import os
import os.path as osp
import pandas as pd
import yaml
import argparse
from dump_prompts_to_parquet import NON_QA_SYSTEM_PROMPT, QA_SYSTEM_PROMPT

# Usage: python3 parquet_response_unpacker [parquet folder or path] [output folder path, if not exists will create]
# Example: python3 parquet_response_unpacker.py batched_responses responses/freeform_qa_sft_v1_infer_debug-0.2-0.9-10

parser = argparse.ArgumentParser()
parser.add_argument('parquet_path', help='path to a folder or file of parquet data, only *.parquet is read and union')
parser.add_argument('out_folder', help='path to the output folder')
parser.add_argument('--meta_data_max_tokens', help='max tokens stored in the metadata', default=None)
parser.add_argument('--meta_data_model_name', help='model name stored in the metadata', default='test model')
parser.add_argument('--meta_data_qa_system_prompt', help='qa system prompt stored in the metadata', default=QA_SYSTEM_PROMPT)
parser.add_argument('--meta_data_system_prompt', help='system prompt stored in the metadata', default=NON_QA_SYSTEM_PROMPT)
parser.add_argument('--meta_data_temp', help='temperature stored in the metadata', default=0.2)
parser.add_argument('--meta_data_top_p', help='top p probability stored in the metadata', default=0.9)

if __name__ == '__main__':
    args = parser.parse_args()

    source_files = []
    if osp.isdir(args.parquet_path):
        source_files = [osp.join(args.parquet_path, ff) for ff in os.listdir(args.parquet_path) if ff.endswith('.parquet')]
    else:
        source_files = [args.parquet_path]
    
    dfs = []
    for s in source_files:
        dfs.append(pd.read_parquet(s, engine='pyarrow'))
    df = pd.concat(dfs)

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
    for i, row in df.iterrows():
        tot_cases += 1
        case_fpath = row['filename'][0]
        responses = row['responses']
        case_idx = row['idx']
        # print(case_fpath)
        # print(case_idx)
        # print(responses)

        case_paths = []
        sample_n = len(responses)
        for j, s in enumerate(responses):
            base_name = f'{case_idx}_{j}.txt'
            now_case_path = osp.join(args.out_folder, base_name)
            with open(now_case_path, 'w') as f:
                f.write(s)
            case_paths.append(base_name)
        answer_paths[case_fpath] = case_paths
    
    params['answer_paths'] = answer_paths
    params['sample_n'] = sample_n
    with open(osp.join(args.out_folder, 'params.yaml'), 'w')  as f:
        yaml.dump(params, f)
    print('# Tot cases:', tot_cases)
