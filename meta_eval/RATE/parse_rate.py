import json
import os


workspace = "../workspace"
metaeval_data = "../MENT.jsonl"
rate_output_dir = "../../agentic/trajectory_gpt4o_judger"
rate_output_file_list = os.listdir(rate_output_dir)

def parse_rate_result(json_file_path):
    parsed_result = {}
    # print(json_file_path)
    with open(json_file_path, "r") as f:
        data = json.load(f)
        for key in data:
            rounds_content = data[key]
            final_score = rounds_content[f"Round_{len(rounds_content)}"]["response_content"]["score"]
            parsed_result[f"{key}"] = float(final_score)
    return parsed_result


rate_en_zh = []
rate_zh_en = []
with open(metaeval_data, "r") as f:
    for line in f:
        data = json.loads(line)
        qid = data["qid"]
        src_lang = data["src_lang"]
        trans_lang = data["trans_lang"]

        if f"{qid}.json" in rate_output_file_list:
            if src_lang == "en" and trans_lang == "zh":
                rate_en_zh.append(parse_rate_result(os.path.join(rate_output_dir, f"{qid}.json")))
            else:
                rate_zh_en.append(parse_rate_result(os.path.join(rate_output_dir, f"{qid}.json")))
        else:
            print(f"Not found output of RATE, qid: {qid}")
f.close()

rate_en_zh_system = {}
rate_zh_en_system = {}

with open(f"{workspace}/metric-scores/en-zh/RATE-src.seg.score", "w") as f_rate_enzh:
    for i in range(10):
        for rate in rate_en_zh:
            f_rate_enzh.write(f"system_{i}\t{rate[f'system_{i}']}\n")
            if rate_en_zh_system.get(f"system_{i}") is None:
                    rate_en_zh_system[f"system_{i}"] = 0
            rate_en_zh_system[f"system_{i}"] += rate[f"system_{i}"]
f_rate_enzh.close()

with open(f"{workspace}/metric-scores/zh-en/RATE-src.seg.score", "w") as f_rate_zhen:
    for i in range(10):
        for rate in rate_zh_en:
            f_rate_zhen.write(f"system_{i}\t{rate[f'system_{i}']}\n")
            if rate_zh_en_system.get(f"system_{i}") is None:
                    rate_zh_en_system[f"system_{i}"] = 0
            rate_zh_en_system[f"system_{i}"] += rate[f"system_{i}"]
f_rate_zhen.close()

with open(f"{workspace}/metric-scores/en-zh/RATE-src.sys.score", "w") as f_rate_enzh, open(f"{workspace}/metric-scores/zh-en/RATE-src.sys.score", "w") as f_rate_zhen:
    for i in range(10):
        f_rate_enzh.write(f"system_{i}\t{rate_en_zh_system[f'system_{i}']}\n")
        f_rate_zhen.write(f"system_{i}\t{rate_zh_en_system[f'system_{i}']}\n")
f_rate_enzh.close()
f_rate_zhen.close()
