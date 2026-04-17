detrend_subject <- function(subject_id, trials) {
  pupil_col <- "pupil_raw_deblink_detransient_interpolate_lpfilt"
  pad_n <- 416 + 1000 + 5000 + 4000
  runs <- c("01", "02", "03")
  out_file <- glue("data/processed/pupil/{subject_id}_detrended_ts.rds")
  dir_create(path_dir(out_file))

  all_ts <- map_dfr(runs, function(run) {
    block_name <- paste0("block_", as.integer(run))
    beh_file <- glue("data/raw/{subject_id}/ses-ret/beh/{subject_id}_ses-ret_task-clamp_run-{run}_beh.csv")
    eye_file <- glue("data/interim/{subject_id}/ses-ret/eye/{subject_id}_ses-ret_task-clamp_run-{run}_desc-eyeris_preproc_epoched.RDS")

    if (!file.exists(beh_file) || !file.exists(eye_file)) {
      return(NULL)
    }

    dat <- read_csv(beh_file, show_col_types = FALSE)
    eye <- read_rds(eye_file)

    if (is.null(eye$epoch_fixprestim[[block_name]])) {
      return(NULL)
    }

    epochs <- bind_rows(
      eye$epoch_fixprestim[[block_name]] %>% mutate(epoch = "fixprestim"),
      eye$epoch_realtime1[[block_name]] %>% mutate(epoch = "realtime1"),
      eye$epoch_realtime2[[block_name]] %>% mutate(epoch = "realtime2")
    ) %>%
      select(STIM, epoch, time_orig, all_of(pupil_col)) %>%
      arrange(STIM, time_orig)
    rm(eye)
    gc()

    epochs <- epochs %>%
      group_by(STIM) %>%
      mutate(
        time_gap = c(0, diff(time_orig)) > 10,
        stim_occurrence = cumsum(time_gap) + 1
      ) %>%
      ungroup() %>%
      select(-time_gap)

    stim_order <- dat %>%
      mutate(trial = row_number()) %>%
      select(trial, stim_file, burn_in_trial) %>%
      group_by(stim_file) %>%
      mutate(stim_occurrence = row_number()) %>%
      ungroup()

    ts <- stim_order %>%
      left_join(epochs, by = c("stim_file" = "STIM", "stim_occurrence")) %>%
      group_by(trial) %>%
      group_modify(~ {
        d <- .x %>% filter(epoch %in% c("realtime1", "realtime2"))
        pad <- tibble(
          stim_file = d$stim_file[1],
          burn_in_trial = d$burn_in_trial[1],
          stim_occurrence = d$stim_occurrence[1],
          epoch = NA_character_,
          time_orig = NA_real_,
          !!pupil_col := NA_real_
        ) %>% slice(rep(1, pad_n))
        bind_rows(d, pad)
      }) %>%
      ungroup() %>%
      mutate(time = (row_number() - 1) / 1000)

    spline_fit <- lm(
      pupil_raw_deblink_detransient_interpolate_lpfilt ~ splines::ns(time, df = 5),
      data = ts %>% filter(
        !is.na(pupil_raw_deblink_detransient_interpolate_lpfilt),
        epoch %in% c("realtime1", "realtime2")
      )
    )

    ts %>%
      mutate(
        spline_pred = predict(spline_fit, newdata = pick(everything())),
        pupil_detrended = pupil_raw_deblink_detransient_interpolate_lpfilt - spline_pred,
        subject = subject_id,
        run = run
      )
  })

  if (is.null(all_ts) || nrow(all_ts) == 0) {
    write_rds(tibble(), out_file)
    return(out_file)
  }

  sub_trials <- trials %>%
    filter(
      dim.top_level__subject == subject_id,
      !dim.top_level__burn_in_trial,
      !dim.top_level__abort_ret_trial,
      !dim.ret_response_item_acc %in% c("blink", "NO_RESPONSE")
    ) %>%
    mutate(
      dim.top_level__run = str_pad(as.integer(dim.top_level__run), width = 2, pad = "0"),
      dim.top_level__trial = as.integer(dim.top_level__trial)
    )

  all_ts <- all_ts %>%
    left_join(sub_trials, by = c(
      "subject" = "dim.top_level__subject",
      "run" = "dim.top_level__run",
      "trial" = "dim.top_level__trial"
    ))

  write_rds(all_ts, out_file)
  out_file
}
