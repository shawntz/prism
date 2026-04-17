identify_outliers <- function(df_item, df_src) {
  get_src_dprime_outliers(df_src) %>%
    filter(is_extreme) %>%
    pull(dim.top_level__subject_id) %>%
    c(get_item_dprime_outliers(df_item) %>% filter(is_extreme) %>% pull(dim.top_level__subject_id)) %>%
    c(
      get_task_instrux_outliers(),
      get_other_bad_subjs()
    ) %>%
    unique() %>%
    sort()
}

#' Here, we identify any subjects with item memory *d'*
#' less than or equal to 0 and/or any subjects who have
#' very few or very many lapsing trials (i.e., more than
#' 2 SDs from the mean proportion of lapsing trials relative
#' to all subjects).
get_item_dprime_outliers <- function(df) {
  df %>%
    mutate(
      dim.trigger_condition = factor(
        dim.trigger_condition,
        levels = c(
          "no_lapse_no_trigger",
          "lapse_no_trigger",
          "lapse_trigger"
        )
      )
    ) %>%
    group_by(dim.top_level__subject_id) %>%
    summarise(
      lapse_sum = sum(n_item_total[dim.trigger_condition %in% c("lapse_no_trigger", "lapse_trigger")]),
      total_sum = sum(n_item_total),
      lapse_prop = lapse_sum / total_sum,
      any_dprime_zero_or_neg = any(item_dp <= 0)
    ) %>%
    mutate(
      z_score = scale(lapse_prop)[, 1],
      is_extreme = abs(z_score) > 2 | any_dprime_zero_or_neg, # more than 2 SD from mean
    )
}

#' Again, we identify any subjects with source memory *d'*
#' less than or equal to 0 and/or any subjects who have very
#' few or very many lapsing trials (i.e., more than 2 SDs from
#' the mean proportion of lapsing trials relative to all subjects).
#'
#' note, the proportion of trials calculation is the same as above
#' (for the item memory *d'* calculations, since the trial counts
#' don't change based on their item vs. source memory).
get_src_dprime_outliers <- function(df) {
  df %>%
    mutate(
      dim.trigger_condition = factor(
        dim.trigger_condition,
        levels = c(
          "no_lapse_no_trigger",
          "lapse_no_trigger",
          "lapse_trigger"
        )
      )
    ) %>%
    group_by(dim.top_level__subject_id) %>%
    summarise(
      lapse_sum = sum(n_src_total[dim.trigger_condition %in% c("lapse_no_trigger", "lapse_trigger")]),
      total_sum = sum(n_src_total),
      lapse_prop = lapse_sum / total_sum,
      any_dprime_zero_or_neg = any(src_dp <= 0)
    ) %>%
    mutate(
      z_score = scale(lapse_prop)[, 1],
      is_extreme = abs(z_score) > 2 | any_dprime_zero_or_neg, # more than 2 SD from mean
    )
}

#' Failure to comply with task instructions:
#' - according to experimenter logs, sub-27
#' misunderstood the instructions and intentionally
#' withheld responses on all `lapse_trigger` trials,
#' thus, they have no usable data here.
get_task_instrux_outliers <- function() {
  return("sub-27")
}

#' Other subjects to exclude based on experimenter logs.
get_other_bad_subjs <- function() {
  return(c("sub-78", "sub-80"))
}
