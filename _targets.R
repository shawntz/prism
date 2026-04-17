# Created by use_targets().
# https://books.ropensci.org/targets/walkthrough.html#inspect-the-pipeline

library(targets)

tar_option_set(
  packages = c("fs", "splines", "glue", "patchwork", "grid", "tidyverse"),
  format = "qs"
)

tar_source()

list(
  tar_target(
    demographics,
    "data/processed/phenotype/demographics_exclusions_n67.csv",
    format = "file"
  ),
  tar_target(
    subject_ids,
    get_all_subject_ids(demographics)
  ),
  tar_target(
    detrended_data,
    detrend_runs(subject_ids)
  ),
  tar_target(
    detrended_data_clean,
    clean_data(detrended_data)
  ),
  tar_target(
    item_dprime,
    get_item_dprime_by_subj_x_cond(detrended_data_clean)
  ),
  tar_target(
    src_dprime,
    get_src_dprime_by_subj_x_cond(detrended_data_clean)
  )
)
