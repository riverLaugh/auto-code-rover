#
import os,re

path = "/home/riv3r/auto-code-rover/EXP/qwen2.5:32b-instruct-fp8_517bug_2025-04-09_12:27:13/no_patch"

subfolders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]

tasks=[]

def remove_timestamp(name):
    # 使用正则表达式移除时间戳
    return re.sub(r'_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$', '', name)

for folder in subfolders:
    task_name = remove_timestamp(folder)
    tasks.append(task_name)

with open("tasks.txt", "w") as f:
    for task in tasks:
        f.write(task + "\n")