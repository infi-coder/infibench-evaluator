#!/bin/bash
# This script exemplifies how to run the evaluation framework pipeline
# See detail instructions in https://infi-coder.github.io/inficoder-eval/

# 1. setup
pip3 install -r requirements.txt
./setup.sh

# 2a. call OpenAI API to generate responses
# We already put GPT-3.5-turbo and GPT-4 responses in the repo, so you are fine to skip it
python3 openai_caller.py suite_v2.0.0.yaml gpt-4 --n 10 --skip --expdir_suffix _rawmerge
python3 openai_caller.py suite_v2.0.0.yaml gpt-3.5-turbo --n 10 --skip --expdir_suffix _rawmerge

# 2b. or locate your model's response csv file and unpack it
python3 adaptors/csv_response_unpacker.py your_response.csv responses/your_model_response_folder

# 3. evaluate

python3 grader_main.py suite_v2.0.0_dev.yaml responses/gpt-4_0.2_0.9_30_suite_v2.0.0_dev
# Result output to results/suite_v2.0.0_dev_gpt-4_0.2_0.9_30_suite_v2.0.0_dev.txt and results/suite_v2.0.0_dev_gpt-4_0.2_0.9_30_suite_v2.0.0_dev.yaml
python3 grader_main.py suite_v2.0.0_dev.yaml responses/gpt-3.5-turbo_0.2_0.9_30_suite_v2.0.0_dev
# Result output to results/suite_v2.0.0_dev_gpt-3.5-turbo_0.2_0.9_30_suite_v2.0.0_dev.txt and results/suite_v2.0.0_dev_gpt-3.5-turbo_0.2_0.9_30_suite_v2.0.0_dev.yaml

python3 grader_main.py suite_v2.0.0_dev.yaml responses/your_model_response_folder

# 4. compute statistics and print the final scores

python3 print_result_stat.py results/suite_v2.0.0_dev_gpt-4_0.2_0.9_30_suite_v2.0.0_dev.yaml example_table_gpt-4.txt --model_name gpt-4

python3 print_result_stat.py results/suite_v2.0.0_dev_gpt-3.5-turbo_0.2_0.9_30_suite_v2.0.0_dev.yaml example_table_gpt-3.5-turbo.txt --model_name gpt-3.5-turbo

