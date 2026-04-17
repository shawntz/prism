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
  ),
  tar_target(
    ids_to_exclude,
    identify_outliers(item_dprime, src_dprime)
  ),
  tar_target(
    id_verification,
    verify_ids(subject_ids, ids_to_exclude)
  ),
  tar_target(
    detrended_data_clean_trimmed,
    filter_out_bad_ids(demographics, detrended_data_clean)
  ),
  tar_target(
    good_subject_ids,
    get_included_subject_ids(demographics)
  ),
  tar_target(
    detrended_ts_file,
    detrend_subject(
      good_subject_ids,
      detrended_data_clean_trimmed
    ),
    pattern = map(good_subject_ids),
    format = "file"
  ),
  tar_target(
    spline_fits,
    extract_spline_fits(detrended_ts_file)
  ),
  tar_target(
    avg_spline,
    avg_spline_by_run(spline_fits)
  ),
  tar_target(
    item_dprime_trimmed,
    get_item_dprime_by_subj_x_cond(detrended_data_clean_trimmed)
  ),
  tar_target(
    src_dprime_trimmed,
    get_src_dprime_by_subj_x_cond(detrended_data_clean_trimmed)
  ),
  tar_target(
    item_dprime_trimmed_reclassified,
    get_item_dprime_by_subj_x_cond_reclassified(detrended_data_clean_trimmed)
  ),
  tar_target(
    src_dprime_trimmed_reclassified,
    get_src_dprime_by_subj_x_cond_reclassified(detrended_data_clean_trimmed)
  ),
  tar_target(
    item_dprime_trimmed_rwstatus,
    get_item_dprime_by_subj_x_cond_x_rwstatus(detrended_data_clean_trimmed)
  ),
  tar_target(
    src_dprime_trimmed_rwstatus,
    get_src_dprime_by_subj_x_cond_x_rwstatus(detrended_data_clean_trimmed)
  ),
  tar_target(
    item_dprime_trimmed_rwstatus_reclassified,
    get_item_dprime_by_subj_x_cond_x_rwstatus_reclassified(detrended_data_clean_trimmed)
  ),
  tar_target(
    src_dprime_trimmed_rwstatus_reclassified,
    get_src_dprime_by_subj_x_cond_x_rwstatus_reclassified(detrended_data_clean_trimmed)
  )
)
