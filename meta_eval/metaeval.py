from mt_metrics_eval.stats import Correlation
from mt_metrics_eval import stats
import numpy as np

def load_data(path):
    data_dict = {}
    with open(path, "r") as f:
        for line in f:
            sys, score = line.strip().split("\t")
            if data_dict.get(sys) is None:
                data_dict[sys] = []
            if score != "None":
                score = float(score)
            else:
                score = None
            data_dict[sys].append(score)
    return data_dict

def human_metrics_intersection(human, metrics):
    keys_human = human.keys()
    keys_metrics = metrics.keys()
    common_keys = keys_human & keys_metrics
    sorted_common_keys = sorted(common_keys)
    
    new_human_dict = {}
    new_metrics_dict = {}
    new_human = []
    new_metrics = []
    for key in sorted_common_keys:
        new_human_dict[key] = human[key]
        new_metrics_dict[key] = metrics[key]
        new_human += human[key]
        new_metrics.append(metrics[key])
    return new_human, np.array(new_metrics)
 
def meta_evaluation(metric_name, human_sys_path, human_seg_path, metrics_sys_path, metrics_seg_path, exclude_system=None):
    """
    for qe system in WMT, exclude ['synthetic_ref', 'refA']
    """
    human_sys = load_data(human_sys_path)
    human_seg = load_data(human_seg_path)
    metrics_sys = load_data(metrics_sys_path)
    metrics_seg = load_data(metrics_seg_path)
    if exclude_system:
        for sys in exclude_system:
            human_sys.pop(sys, None)
            metrics_sys.pop(sys, None)
            human_seg.pop(sys, None)
            metrics_seg.pop(sys, None)

    new_human_sys, new_metrics_sys = human_metrics_intersection(human_sys, metrics_sys)
    new_human_seg, new_metrics_seg = human_metrics_intersection(human_seg, metrics_seg)
    new_metrics_sys = new_metrics_sys.reshape(-1)

    def corrs(human_sys, human_seg, metrics_sys, metrics_seg):
        """
        human_sys: List, [num_sys]
        human_seg: List, [num_sys * num_segments]
        metrics_sys: Array, (num_sys)
        metrics_seg: Array, (num_sys, num_segments)
        """
        # --- System Level ---
        sys_corr = Correlation(len(metrics_sys), human_sys, metrics_sys)
        sys_pearson = sys_corr.Pearson()
        sys_spearman = sys_corr.Spearman() 
        
        agree_count, total_pairs = stats.Agreement(human_sys, metrics_sys)
        sys_acc = agree_count / total_pairs
        
        # --- Segment Level ---
        seg_corr = Correlation(metrics_seg.size, human_seg, metrics_seg.flatten())
        seg_pearson = seg_corr.Pearson()
        seg_spearman = seg_corr.Spearman()
        
        seg_acct = seg_corr.KendallWithTiesOpt(average_by='item', sample_rate=1.0)
        
        return {
            "sys_acc": sys_acc.item(),
            "sys_pearson": sys_pearson[0].item(),
            "sys_spearman": sys_spearman[0].item(),
            "seg_acct": seg_acct[0],
            "seg_pearson": seg_pearson[0].item(),
            "seg_spearman": seg_spearman[0].item(),
        }
    
    results = corrs(new_human_sys, new_human_seg, new_metrics_sys, new_metrics_seg)
    
    all_values = list(results.values())
    avg_val = sum(all_values) / len(all_values)
    results["avg"] = avg_val

    print(f"\nMetric: {metric_name}")
    
    headers = list(results.keys())
    data_row = [results[k] * 100 for k in headers]
    
    col_width = 15
    header_str = "".join([f"{h:<{col_width}}" for h in headers])
    divider = "-" * (col_width * len(headers))
    data_str = "".join([f"{d:<{col_width}.1f}" for d in data_row])
    
    print(header_str)
    print(divider)
    print(data_str)
    print("=" * (col_width * len(headers))+"\n")

    return results



result = meta_evaluation(
    "RATE-zh-en[noref]",
    "workspace/human-scores/zh-en.sys.score",
    "workspace/human-scores/zh-en.seg.score",
    "workspace/metric-scores/zh-en/RATE-src.sys.score",
    "workspace/metric-scores/zh-en/RATE-src.seg.score"
)

result = meta_evaluation(
    "RATE-en-zh[noref]",
    "workspace/human-scores/en-zh.sys.score",
    "workspace/human-scores/en-zh.seg.score",
    "workspace/metric-scores/en-zh/RATE-src.sys.score",
    "workspace/metric-scores/en-zh/RATE-src.seg.score"
)
