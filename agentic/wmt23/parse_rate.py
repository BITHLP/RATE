import json
import os

rate_trajectory_dir = "./trajectory_gpt4o_judger"


def parse_rate_result(json_file_path):
    parsed_result = {}
    with open(json_file_path, "r") as f:
        data = json.load(f)
        for key in data:
            if "trans_" in key: # eval 
                rounds_content = data[key]
                final_score = rounds_content[f"Round_{len(rounds_content)}"]["response_content"]["score"]
                parsed_result[f"{key}"] = float(final_score)
            else: # not eval, no anotated in meta dataset
                parsed_result[f"trans_{key}"] = 0.0
    return parsed_result


meta_datas = []
system_names = []
with open("wmt23-ende.jsonl", "r") as f:
    for line in f:
        data = json.loads(line)
        meta_datas.append(data)
    system_names = data["system_names"]
f.close()
rate_scores = [] # {qid, input_lang, output_lang, src, trans0_score, trans1_score, ...}

for meta_data in meta_datas:
    qid = meta_data["qid"]
    with open(os.path.join(rate_trajectory_dir, f"{qid}.json"), "r") as f:
        rate_scores.append(parse_rate_result(os.path.join(rate_trajectory_dir, f"{qid}.json")))
    f.close()
rate_system = {}

os.makedirs("rate_score", exist_ok=True)
with open("./rate_score/rate-src.seg.score", "w") as f_seg:
    for sys in system_names:
        for rate_score in rate_scores:
            score = rate_score[f"trans_{sys}"]
            f_seg.write(f"{sys}\t{score}\n")
            if rate_system.get(sys) is None:
                rate_system[sys] = 0.
            rate_system[sys] += float(score)
f_seg.close()

with open("./rate_score/rate-src.sys.score", "w") as f_sys:
    for sys in system_names:
        score = rate_system[sys]
        f_sys.write(f"{sys}\t{score}\n")
f_sys.close()

