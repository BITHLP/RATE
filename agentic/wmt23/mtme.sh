# alias mtme='python3 -m mt_metrics_eval.mtme'

scores=/data/yztian/OpenSource/RATE/agentic/wmt23/rate_score

python3 -m mt_metrics_eval.mtme -t wmt23 -l en-de --matrix --matrix_level sys --matrix_corr accuracy --add_metrics_from_dir $scores --k 0

python3 -m mt_metrics_eval.mtme -t wmt23 -l en-de --matrix --matrix_level sys --add_metrics_from_dir $scores --k 0

python3 -m mt_metrics_eval.mtme -t wmt23 -l en-de --matrix --matrix_level seg --avg item \
  --matrix_corr KendallWithTiesOpt --matrix_perm_test pairs --add_metrics_from_dir $scores \
  --matrix_corr_args "{'variant':'acc23', 'sample_rate':1.0}" --k 0

python3 -m mt_metrics_eval.mtme -t wmt23 -l en-de --matrix --matrix_level seg --add_metrics_from_dir $scores --k 0