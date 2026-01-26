import os
import json

mt_metrics_eval_v2_dir = "/data/yztian/mt-metrics-eval/download/.mt-metrics-eval/mt-metrics-eval-v2"

human_score_file = open(f"{mt_metrics_eval_v2_dir}/wmt23/human-scores/en-de.mqm.seg.score", "r")
data = {}
for line in human_score_file:
    system, score = line.strip().split("\t")
    if data.get(system) is None:
        data[system] = []
    data[system].append([score])

system_output_dir = f"{mt_metrics_eval_v2_dir}/wmt23/system-outputs/en-de"
for system in data.keys():
    idx = 1
    with open(os.path.join(system_output_dir, f"{system}.txt")) as f:
        for line in f:
            data[system][idx-1].append(line.strip())
            idx += 1

source_file = open(f"{mt_metrics_eval_v2_dir}/wmt23/sources/en-de.txt", "r")
idx = 1
for line in source_file:
    for system in data.keys():
        data[system][idx-1].append(line.strip())
    idx += 1

with open("wmt23-ende.jsonl","w") as f:
    all_json_data = []
    idx = 1
    for idx in range(len(data["AIRC"])):
        json_data = {}
        json_data["qid"] = f"wmt23-ende-{idx}"
        json_data["system_names"] = []
        json_data["src"] = ""
        src = data[list(data.keys())[0]][idx][2]
        json_data["src"] = src
        for key in data.keys():
            if data[key][idx][0] == "None":
                json_data["flag"] = "None"
            else:
                json_data["flag"] = "NotNone"
            json_data["system_names"].append(key)
            json_data[f"trans_{key}"] = data[key][idx][1]
            assert src == data[key][idx][2]
            if data[key][idx][0] == "None":
                json_data[f"avg_trans_{key}_scores"] = None
            else:
                json_data[f"avg_trans_{key}_scores"] = float(data[key][idx][0])
        all_json_data.append(json_data)
        idx += 1
    for json_data in all_json_data:
        f.write(json.dumps(json_data, ensure_ascii=False)+"\n")
f.close()