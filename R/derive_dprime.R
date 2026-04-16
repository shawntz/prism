get_item_dprime_by_subj_x_cond <- function(df) {
  summarize_item_block(
    df = df,
    group_vars = c(
      "dim.top_level__subject_id",
      "dim.trigger_condition"
    )
  )
}

get_item_dprime_by_subj_x_cond_reclassified <- function(df) {
  summarize_item_reclassified(
    df = df,
    group_vars = c(
      "dim.top_level__subject_id",
      "dim.top_level__detrended_status"
    )
  )
}

get_src_dprime_by_subj_x_cond <- function(df) {
  summarize_src_block(
    df = df,
    group_vars = c(
      "dim.top_level__subject_id",
      "dim.trigger_condition"
    )
  )
}

get_item_dprime_by_subj_x_cond_x_rwstatus <- function(df) {
  summarize_item_block(
    df = df,
    group_vars = c(
      "dim.top_level__subject_id",
      "dim.trigger_condition",
      "dim.realtime_window_status"
    )
  )
}

get_src_dprime_by_subj_x_cond_x_rwstatus <- function(df) {
  summarize_src_block(
    df = df,
    group_vars = c(
      "dim.top_level__subject_id",
      "dim.trigger_condition",
      "dim.realtime_window_status"
    )
  )
}

get_item_dprime_by_subj_x_cond_x_rwstatus_reclassified <- function(df) {
  summarize_item_reclassified(
    df = df,
    group_vars = c(
      "dim.top_level__subject_id",
      "dim.top_level__detrended_status",
      "dim.realtime_window_status"
    )
  )
}

get_src_dprime_by_subj_x_cond_x_rwstatus_reclassified <- function(df) {
  summarize_src_reclassified(
    df = df,
    group_vars = c(
      "dim.top_level__subject_id",
      "dim.top_level__detrended_status",
      "dim.realtime_window_status"
    )
  )
}

get_src_dprime_by_subj_x_cond_reclassified <- function(df) {
  summarize_src_reclassified(
    df = df,
    group_vars = c(
      "dim.top_level__subject_id",
      "dim.top_level__detrended_status"
    )
  )
}

# calculate adjusted d' -------------------------------------------------------
calc_dprime <- function(n_hit, n_fa, n_targets, n_distractors) {
  hit_rate_adjusted <- (n_hit + 0.5) / (n_targets + 1)
  fa_rate_adjusted <- (n_fa + 0.5) / (n_distractors + 1)
  qnorm(hit_rate_adjusted) - qnorm(fa_rate_adjusted)
}

# helper func: process item memory --------------------------------------------
summarize_item_block <- function(df, group_vars) {
  df %>%
    filter(
      !dim.top_level__burn_in_trial,
      !dim.ret_response_item_acc %in% c("blink", "NO_RESPONSE")
    ) %>%
    group_by(across(all_of(group_vars))) %>%
    summarise(
      item_hit       = sum(dim.ret_response_item_acc == "Item Hit"),
      item_miss      = sum(dim.ret_response_item_acc == "Item Miss"),
      item_fa        = sum(dim.ret_response_item_acc == "Item FA"),
      item_cr        = sum(dim.ret_response_item_acc == "Item CR"),
      n_item_target  = sum(dim.top_level__enc_goal %in% c("BGSM", "PLUP")),
      n_item_foil    = sum(dim.top_level__enc_goal == "NOV"),
      n_item_total   = item_hit + item_miss + item_fa + item_cr,
      .groups        = "drop"
    ) %>%
    mutate(
      item_hr  = item_hit / n_item_target,
      item_far = item_fa / n_item_foil,
      item_dp  = calc_dprime(item_hit, item_fa, n_item_target, n_item_foil),
    )
}

summarize_item_reclassified <- function(df, group_vars) {
  df %>%
    filter(
      !dim.top_level__burn_in_trial,
      !dim.ret_response_item_acc %in% c("blink", "NO_RESPONSE"),
      !dim.top_level__detrended_status %in% "NA_notrigger"
    ) %>%
    group_by(across(all_of(group_vars))) %>%
    summarise(
      item_hit       = sum(dim.ret_response_item_acc == "Item Hit"),
      item_miss      = sum(dim.ret_response_item_acc == "Item Miss"),
      item_fa        = sum(dim.ret_response_item_acc == "Item FA"),
      item_cr        = sum(dim.ret_response_item_acc == "Item CR"),
      n_item_target  = sum(dim.top_level__enc_goal %in% c("BGSM", "PLUP")),
      n_item_foil    = sum(dim.top_level__enc_goal == "NOV"),
      n_item_total   = item_hit + item_miss + item_fa + item_cr,
      .groups        = "drop"
    ) %>%
    mutate(
      item_hr  = item_hit / n_item_target,
      item_far = item_fa / n_item_foil,
      item_dp  = calc_dprime(item_hit, item_fa, n_item_target, n_item_foil),
    )
}

# helper func: process source memory ------------------------------------------
summarize_src_block <- function(df, group_vars) {
  df %>%
    filter(
      !dim.top_level__burn_in_trial,
      !dim.ret_response_source_acc %in% c("blink", "NO_RESPONSE")
    ) %>%
    group_by(across(all_of(group_vars))) %>%
    summarise(
      src_hit       = sum(dim.ret_response_source_acc %in% c("Size Hit", "Pleasant Hit")),
      src_miss      = sum(dim.ret_response_source_acc %in% c("Size Miss", "Pleasant Miss")),
      src_fa        = sum(dim.ret_response_source_acc %in% c("Size FA", "Pleasant FA")),
      src_cr        = sum(dim.ret_response_source_acc == "Source CR"),
      n_src_target  = sum(dim.top_level__enc_goal %in% c("BGSM", "PLUP")),
      n_src_foil    = sum(dim.top_level__enc_goal == "NOV"),
      n_src_total   = src_hit + src_miss + src_fa + src_cr,
      .groups       = "drop"
    ) %>%
    mutate(
      src_hr  = src_hit / n_src_target,
      src_far = src_fa / n_src_foil,
      src_dp  = calc_dprime(src_hit, src_fa, n_src_target, n_src_foil),
    )
}

summarize_src_reclassified <- function(df, group_vars) {
  df %>%
    filter(
      !dim.top_level__burn_in_trial,
      !dim.ret_response_item_acc %in% c("blink", "NO_RESPONSE"),
      !dim.top_level__detrended_status %in% "NA_notrigger"
    ) %>%
    group_by(across(all_of(group_vars))) %>%
    summarise(
      src_hit       = sum(dim.ret_response_source_acc %in% c("Size Hit", "Pleasant Hit")),
      src_miss      = sum(dim.ret_response_source_acc %in% c("Size Miss", "Pleasant Miss")),
      src_fa        = sum(dim.ret_response_source_acc %in% c("Size FA", "Pleasant FA")),
      src_cr        = sum(dim.ret_response_source_acc == "Source CR"),
      n_src_target  = sum(dim.top_level__enc_goal %in% c("BGSM", "PLUP")),
      n_src_foil    = sum(dim.top_level__enc_goal == "NOV"),
      n_src_total   = src_hit + src_miss + src_fa + src_cr,
      .groups       = "drop"
    ) %>%
    mutate(
      src_hr  = src_hit / n_src_target,
      src_far = src_fa / n_src_foil,
      src_dp  = calc_dprime(src_hit, src_fa, n_src_target, n_src_foil),
    )
}
