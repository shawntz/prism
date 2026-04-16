clean_data <- function(df) {
  df <- fix_ids(df)
  df <- fix_colnames(df)
  df <- coerce_types(df)
  df <- derive_ret_dims(df)
  return(df)
}

fix_ids <- function(df) {
  df$subject_id <- substr(df$subject_id, 3, 4)
  df$subject_id <- as.numeric(df$subject_id)
  df$subject_id <- paste0("sub-", str_pad(df$subject_id, width = 2, pad = "0"))
  return(df)
}

fix_colnames <- function(df) {
  df %>%
    rename_with(\(x) paste0("dim.top_level__", x))
}

coerce_types <- function(df) {
  df %>%
    mutate(across(where(is.character), \(col) {
      if (all(col %in% c("TRUE", "FALSE", NA))) {
        return(as.logical(col))
      }
      col <- if_else(col %in% c("NaN", "None", "nan", "none"), NA_character_, col)
      converted <- suppressWarnings(as.numeric(col))
      if (all(is.na(converted) == is.na(col))) {
        return(converted)
      }
      col
    }))
}

derive_ret_dims <- function(df) {
  df %>%
    # make copy of the window_one_status column to separate out chars from floats
    # this resolves an issue where the ascii representation of "blink" and
    # "constriction" return TRUE when compared with certain baseline means that
    # are large enough in numerical value
    mutate(
      dim.window_one_status_desc = case_when(
        dim.top_level__trigger_window_mean_one == "blink" ~ "blink",
        dim.top_level__trigger_window_mean_one == "None" ~ "not computed",
        TRUE ~ "computed"
      ),
      .after = dim.top_level__trigger_window_mean_one
    ) %>%
    mutate(
      dim.top_level__trigger_window_mean_one = case_when(
        dim.top_level__trigger_window_mean_one == "blink" ~ NA,
        dim.top_level__trigger_window_mean_one == "None" ~ NA,
        TRUE ~ dim.top_level__trigger_window_mean_one
      ),
      dim.top_level__trigger_window_mean_one = as.numeric(dim.top_level__trigger_window_mean_one)
    ) %>%
    mutate(
      dim.window_one_status = case_when(
        dim.top_level__trigger_window_mean_one < dim.top_level__trigger_lower_threshold ~ "constriction",
        dim.top_level__trigger_window_mean_one > dim.top_level__trigger_upper_threshold ~ "dilation",
        is.na(dim.top_level__trigger_window_mean_one) ~ NA,
        TRUE ~ "within range"
      ),
      .after = dim.top_level__trigger_window_mean_one
    ) %>%
    mutate(
      dim.window_two_status_desc = case_when(
        dim.top_level__trigger_window_mean_two == "blink" ~ "blink",
        dim.top_level__trigger_window_mean_two == "None" ~ "not computed",
        TRUE ~ "computed"
      ),
      .after = dim.top_level__trigger_window_mean_two
    ) %>%
    mutate(
      dim.top_level__trigger_window_mean_two = case_when(
        dim.top_level__trigger_window_mean_two == "blink" ~ NA,
        dim.top_level__trigger_window_mean_two == "None" ~ NA,
        TRUE ~ dim.top_level__trigger_window_mean_two
      ),
      dim.top_level__trigger_window_mean_two = as.numeric(dim.top_level__trigger_window_mean_two)
    ) %>%
    mutate(
      dim.window_two_status = case_when(
        dim.top_level__trigger_window_mean_two < dim.top_level__trigger_lower_threshold ~ "constriction",
        dim.top_level__trigger_window_mean_two > dim.top_level__trigger_upper_threshold ~ "dilation",
        is.na(dim.top_level__trigger_window_mean_two) ~ NA,
        TRUE ~ "within range"
      ),
      .after = dim.top_level__trigger_window_mean_two
    ) %>%
    mutate(
      dim.realtime_window_status = case_when(
        dim.top_level__burn_in_trial == TRUE ~ "burnin",
        dim.window_one_status_desc == "blink" & dim.window_two_status_desc == "blink" ~ "blink",
        dim.window_one_status_desc == "not computed" & dim.window_two_status_desc == "not computed" ~ "not computed",
        dim.window_one_status == "within range" & dim.window_two_status == "within range" ~ "within range",
        (dim.window_one_status_desc == "blink" | dim.window_one_status_desc == "not computed" | dim.window_one_status == "within range") &
          (dim.window_two_status == "constriction" | dim.window_two_status == "dilation" | dim.window_two_status == "within range") ~ dim.window_two_status,
        dim.window_one_status == "within range" & dim.window_two_status_desc == "blink" ~ "within range",
        (dim.window_one_status == "constriction" | dim.window_one_status == "dilation") & (dim.window_two_status_desc %in% c("not computed", "blink") | is.na(dim.window_two_status)) ~ dim.window_one_status,
        is.na(dim.window_one_status) & !is.na(dim.window_two_status) ~ dim.window_two_status,
        !is.na(dim.window_one_status) & is.na(dim.window_two_status) ~ dim.window_one_status,
        is.na(dim.window_one_status) & is.na(dim.window_two_status) ~ NA_character_,
        TRUE ~ "ERROR"
      ),
      .after = dim.top_level__trigger_should_launch
    ) %>%
    mutate(
      dim.ret_response_acc = case_when(
        (dim.top_level__ret_label == "ctrl_probe_blink_1" | dim.top_level__ret_label == "ctrl_probe_blink_2" | dim.top_level__ret_label == "ctrl_probe_blink_3") ~ NA,
        dim.top_level__enc_goal == dim.top_level__ret_label ~ 1,
        .default = 0
      ),
      dim.ret_response_source_acc = case_when(
        (dim.top_level__enc_goal == "BGSM" & dim.top_level__ret_label == "BGSM") ~ "Size Hit",
        (dim.top_level__enc_goal == "BGSM" & dim.top_level__ret_label == "PLUP") ~ "Size Miss",
        (dim.top_level__enc_goal == "BGSM" & dim.top_level__ret_label == "OLD") ~ "Size Miss",
        (dim.top_level__enc_goal == "BGSM" & dim.top_level__ret_label == "NOV") ~ "Size Miss",
        (dim.top_level__enc_goal == "PLUP" & dim.top_level__ret_label == "BGSM") ~ "Pleasant Miss",
        (dim.top_level__enc_goal == "PLUP" & dim.top_level__ret_label == "PLUP") ~ "Pleasant Hit",
        (dim.top_level__enc_goal == "PLUP" & dim.top_level__ret_label == "OLD") ~ "Pleasant Miss",
        (dim.top_level__enc_goal == "PLUP" & dim.top_level__ret_label == "NOV") ~ "Pleasant Miss",
        (dim.top_level__enc_goal == "NOV" & dim.top_level__ret_label == "BGSM") ~ "Size FA",
        (dim.top_level__enc_goal == "NOV" & dim.top_level__ret_label == "PLUP") ~ "Pleasant FA",
        (dim.top_level__enc_goal == "NOV" & dim.top_level__ret_label == "OLD") ~ "Source CR",
        (dim.top_level__enc_goal == "NOV" & dim.top_level__ret_label == "NOV") ~ "Source CR",
        dim.top_level__ret_label == "NO_RESPONSE" ~ "NO_RESPONSE",
        (dim.top_level__ret_label == "ctrl_probe_blink_1" | dim.top_level__ret_label == "ctrl_probe_blink_2" | dim.top_level__ret_label == "ctrl_probe_blink_3") ~ "blink",
        .default = "ERROR"
      ),
      dim.ret_response_item_acc = case_when(
        (dim.top_level__enc_goal == "BGSM" & dim.top_level__ret_label == "BGSM") ~ "Item Hit",
        (dim.top_level__enc_goal == "BGSM" & dim.top_level__ret_label == "PLUP") ~ "Item Hit",
        (dim.top_level__enc_goal == "BGSM" & dim.top_level__ret_label == "OLD") ~ "Item Hit",
        (dim.top_level__enc_goal == "BGSM" & dim.top_level__ret_label == "NOV") ~ "Item Miss",
        (dim.top_level__enc_goal == "PLUP" & dim.top_level__ret_label == "BGSM") ~ "Item Hit",
        (dim.top_level__enc_goal == "PLUP" & dim.top_level__ret_label == "PLUP") ~ "Item Hit",
        (dim.top_level__enc_goal == "PLUP" & dim.top_level__ret_label == "OLD") ~ "Item Hit",
        (dim.top_level__enc_goal == "PLUP" & dim.top_level__ret_label == "NOV") ~ "Item Miss",
        (dim.top_level__enc_goal == "NOV" & dim.top_level__ret_label == "BGSM") ~ "Item FA",
        (dim.top_level__enc_goal == "NOV" & dim.top_level__ret_label == "PLUP") ~ "Item FA",
        (dim.top_level__enc_goal == "NOV" & dim.top_level__ret_label == "OLD") ~ "Item FA",
        (dim.top_level__enc_goal == "NOV" & dim.top_level__ret_label == "NOV") ~ "Item CR",
        dim.top_level__ret_label == "NO_RESPONSE" ~ "NO_RESPONSE",
        (dim.top_level__ret_label == "ctrl_probe_blink_1" | dim.top_level__ret_label == "ctrl_probe_blink_2" | dim.top_level__ret_label == "ctrl_probe_blink_3") ~ "blink",
        .default = "ERROR"
      ),
      .after = dim.top_level__ret_label
    ) %>%
    mutate(
      dim.trigger_condition = case_when(
        dim.top_level__trigger_should_launch == FALSE & dim.top_level__trigger_actually_delivered == FALSE ~ "no_lapse_no_trigger",
        dim.top_level__trigger_should_launch == TRUE & dim.top_level__trigger_actually_delivered == FALSE ~ "lapse_no_trigger",
        dim.top_level__trigger_should_launch == TRUE & dim.top_level__trigger_actually_delivered == TRUE ~ "lapse_trigger",
        .default = "ERROR"
      )
    ) %>%
    mutate(
      dim.top_level__response_rt = str_replace(dim.top_level__response_rt, "None", NA_character_),
      dim.top_level__response_rt = as.numeric(dim.top_level__response_rt),
      dim.ln_response_rt = log(dim.top_level__response_rt),
      .after = dim.top_level__response_rt
    ) %>%
    mutate(dim.top_level__burn_in_trial = as.logical(dim.top_level__burn_in_trial))
}
