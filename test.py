import json

with open("/home/riv3r/auto-code-rover/SWE-bench/setup_result/setup_map.json", "r") as f:
    setup_map = json.load(f)

with open("task.txt", "w") as f:
    for key in setup_map.keys():
        f.write(key + "\n")
