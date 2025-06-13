#!/bin/bash

# export OPENAI_BASE_URL=https://api5.xhub.chat/v1

# MODEL='gpt-4o-2024-08-06'

# MODEL='gpt-4o-2024-11-20'

# MODEL='qwen2.5:72b-instruct-fp16'

# MODEL='qwen2.5:72b-instruct-fp8'

MODEL='claude-3-7-sonnet-20250219'
dataset='msweagent'
# export OPENAI_BASE_URL='https://cluster1-qwen.cxpcn.site/v1'
export OPENAI_BASE_URL='https://api5.xhub.chat/v1'

DATE=$(date '+%Y-%m-%d_%H:%M:%S')

PYTHONPATH=. \
python app/main.py rust-bench \
    --model $MODEL \
    --setup-map /home/riv3r/auto-code-rover/SWE-bench/setup_result/setup_map.json \
    --tasks-map /home/riv3r/auto-code-rover/SWE-bench/setup_result/tasks_map.json \
    --output-dir "EXP/${MODEL}_${dataset}_${DATE}" \
    --num-processes 1 \
    --task-list-file conf/task.txt \
    --conv-round-limit 5\
    --no-print \
    > Logs/run_logs/${MODEL}_${dataset}_${DATE}.log 2>&1
