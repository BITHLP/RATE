import json
import os
import numpy as np

workspace = "./workspace"
metaeval_data = "./MENT.jsonl"

os.makedirs(os.path.join(workspace, "human-scores"), exist_ok=True)
os.makedirs(os.path.join(workspace, "metric-scores"), exist_ok=True)
os.makedirs(os.path.join(workspace, "metric-scores", "en-zh"), exist_ok=True)
os.makedirs(os.path.join(workspace, "metric-scores", "zh-en"), exist_ok=True)
os.makedirs(os.path.join(workspace, "sources"), exist_ok=True)
os.makedirs(os.path.join(workspace, "references"), exist_ok=True)
os.makedirs(os.path.join(workspace, "system-outputs"), exist_ok=True)
os.makedirs(os.path.join(workspace, "system-outputs", "en-zh"), exist_ok=True)
os.makedirs(os.path.join(workspace, "system-outputs", "zh-en"), exist_ok=True)

en_zh_srcs = []
en_zh_refs = []
en_zh_human_scores = {}
en_zh_system_outputs = {}
zh_en_srcs = []
zh_en_refs = []
zh_en_human_scores = {}
zh_en_system_outputs = {}
for i in range(10):
    en_zh_human_scores[f"system_{i}"] = []
    en_zh_system_outputs[f"system_{i}"] = []
    zh_en_human_scores[f"system_{i}"] = []
    zh_en_system_outputs[f"system_{i}"] = []

with open(metaeval_data, "r") as f:
    for line in f:
        data = json.loads(line)
        if data["src_lang"] == "en" and data["trans_lang"] == "zh":
            en_zh_srcs.append(data["src"].strip())
            en_zh_refs.append(data["ref"].strip())
            for i in range(10):
                en_zh_human_scores[f"system_{i}"].append(data[f"avg_trans_{i}_score"])
                en_zh_system_outputs[f"system_{i}"].append(data[f"trans_{i}"])
        else:
            zh_en_srcs.append(data["src"].strip())
            zh_en_refs.append(data["ref".strip()])
            for i in range(10):
                zh_en_human_scores[f"system_{i}"].append(data[f"avg_trans_{i}_score"])
                zh_en_system_outputs[f"system_{i}"].append(data[f"trans_{i}"])
f.close()

with open(os.path.join(workspace, "sources", "en-zh.txt"), "w") as f:
    for src in en_zh_srcs:
        f.write(json.dumps({"src":src}, ensure_ascii=False)+"\n")
f.close()

with open(os.path.join(workspace, "sources", "zh-en.txt"), "w") as f:
    for src in zh_en_srcs:
        f.write(json.dumps({"src":src}, ensure_ascii=False)+"\n")
f.close()

with open(os.path.join(workspace, "references", "en-zh.txt"), "w") as f:
    for ref in en_zh_refs:
        f.write(json.dumps({"ref": ref}, ensure_ascii=False)+"\n")
f.close()

with open(os.path.join(workspace, "references", "zh-en.txt"), "w") as f:
    for ref in zh_en_refs:
        f.write(json.dumps({"ref": ref}, ensure_ascii=False)+"\n")
f.close()

with open(os.path.join(workspace, "human-scores", "en-zh.seg.score"), "w") as f:
    for i in range(10):
        for score in en_zh_human_scores[f"system_{i}"]:
            f.write(f"system_{i}\t{score}\n")
f.close()

with open(os.path.join(workspace, "human-scores", "en-zh.sys.score"), "w") as f:
    for i in range(10):
        sys_sum_score = np.sum(en_zh_human_scores[f"system_{i}"]).item()
        f.write(f"system_{i}\t{sys_sum_score}\n")
f.close()

with open(os.path.join(workspace, "human-scores", "zh-en.seg.score"), "w") as f:
    for i in range(10):
        for score in zh_en_human_scores[f"system_{i}"]:
            f.write(f"system_{i}\t{score}\n")
f.close()

with open(os.path.join(workspace, "human-scores", "zh-en.sys.score"), "w") as f:
    for i in range(10):
        sys_sum_score = np.sum(zh_en_human_scores[f"system_{i}"]).item()
        f.write(f"system_{i}\t{sys_sum_score}\n")
f.close()

for i in range(10):
    with open(os.path.join(workspace, "system-outputs", "en-zh", f"system_{i}"), "w") as f:
        for trans in en_zh_system_outputs[f"system_{i}"]:
            f.write(json.dumps({"trans":trans}, ensure_ascii=False)+"\n")
    f.close()

    with open(os.path.join(workspace, "system-outputs", "zh-en", f"system_{i}"), "w") as f:
        for trans in zh_en_system_outputs[f"system_{i}"]:
            f.write(json.dumps({"trans":trans}, ensure_ascii=False)+"\n")
    f.close()